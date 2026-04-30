from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
import calendar

from .models import Sede, Evento, ConfiguracionGlobal, Proveedor


# Funciones Auxiliares (Mantenlas igual)
def restar_meses(anio, mes, meses_a_restar):
    nuevo_mes = mes - meses_a_restar
    nuevo_anio = anio
    while nuevo_mes <= 0:
        nuevo_mes += 12
        nuevo_anio -= 1
    return nuevo_anio, nuevo_mes


def calcular_minutos_caida_reales(eventos, inicio_periodo, fin_periodo, rol_filtro):
    intervalos = []
    for ev in eventos:
        if ev.rol == rol_filtro:
            inicio = max(ev.fecha_inicio, inicio_periodo)
            fin = min(ev.fecha_fin or timezone.now(), fin_periodo)
            if inicio < fin:
                intervalos.append((inicio, fin))

    if not intervalos:
        return 0

    intervalos.sort(key=lambda x: x[0])
    merged = [intervalos[0]]
    for current_start, current_end in intervalos[1:]:
        last_start, last_end = merged[-1]
        if current_start <= last_end:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))

    return sum(int((f - i).total_seconds() / 60) for i, f in merged)


# --- FUNCIÓN PRINCIPAL DEL DASHBOARD ---
def dashboard_kpi(request):
    hoy = timezone.now()

    # Filtros URL
    mes_raw = request.GET.get('mes')
    anio_raw = request.GET.get('anio')
    sede_id_raw = request.GET.get('sede_id')

    try:
        mes = int(mes_raw) if mes_raw else hoy.month
    except ValueError:
        mes = hoy.month

    try:
        anio = int(anio_raw) if anio_raw else hoy.year
    except ValueError:
        anio = hoy.year

    try:
        sede_id = int(sede_id_raw) if sede_id_raw else None
    except ValueError:
        sede_id = None

    tab_activa = 'individual' if 'sede_id' in request.GET else 'sedes'

    # Configuración Global
    config = ConfiguracionGlobal.objects.first()
    meta = config.meta_disponibilidad if config else 0.99
    minutos_dia = config.minutos_dia if config else 1440

    # Fechas del período actual
    tz = timezone.get_current_timezone()
    primer_dia_mes = timezone.make_aware(datetime(anio, mes, 1), tz)
    _, ultimo_dia_num = calendar.monthrange(anio, mes)
    ultimo_dia_mes = timezone.make_aware(datetime(anio, mes, ultimo_dia_num, 23, 59, 59), tz)
    minutos_mes_total = ultimo_dia_num * minutos_dia

    # Objetos Base
    sedes = Sede.objects.all()
    proveedores = Proveedor.objects.all()

    # Fallbacks para evitar UnboundLocalError (image_2.png)
    # Definimos las variables ANTES de cualquier condicional
    resumen_historico = []
    historico_sede = []
    sede_obj = None

    # --- TABLA 1: DISPONIBILIDAD DE SEDES ---
    reporte_sedes = []
    for sede in sedes:
        eventos_mes = Evento.objects.filter(Q(idsede=sede) & Q(fecha_inicio__lte=ultimo_dia_mes) & (
                Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True)))

        caida_p = calcular_minutos_caida_reales(eventos_mes, primer_dia_mes, ultimo_dia_mes, 'Principal')
        caida_s = calcular_minutos_caida_reales(eventos_mes, primer_dia_mes, ultimo_dia_mes, 'Respaldo')

        caida_simultanea = 0
        eventos_p = [(max(ev.fecha_inicio, primer_dia_mes), min(ev.fecha_fin or timezone.now(), ultimo_dia_mes)) for ev
                     in eventos_mes if ev.rol == 'Principal']
        eventos_s = [(max(ev.fecha_inicio, primer_dia_mes), min(ev.fecha_fin or timezone.now(), ultimo_dia_mes)) for ev
                     in eventos_mes if ev.rol == 'Respaldo']
        for inicio_p, fin_p in eventos_p:
            for inicio_s, fin_s in eventos_s:
                inter_inicio = max(inicio_p, inicio_s)
                inter_fin = min(fin_p, fin_s)
                if inter_inicio < inter_fin:
                    caida_simultanea += int((inter_fin - inter_inicio).total_seconds() / 60)

        disp_combinada = (1 - (caida_simultanea / minutos_mes_total)) * 100
        reporte_sedes.append({
            'sede': sede.nombre,
            'canal_p': sede.canal_primario.nombre if sede.canal_primario else "N/A",
            'min_p': caida_p,
            'disp_p': round((1 - (caida_p / minutos_mes_total)) * 100, 4),
            'indisp_p_pct': round((caida_p / minutos_mes_total) * 100, 4),
            'canal_s': sede.canal_secundario.nombre if sede.canal_secundario else "N/A",
            'min_s': caida_s,
            'disp_s': round((1 - (caida_s / minutos_mes_total)) * 100, 4),
            'indisp_s_pct': round((caida_s / minutos_mes_total) * 100, 4),
            'disp_total': round(disp_combinada, 4),
            'cumple': (disp_combinada / 100) >= meta,
            'meta': meta * 100
        })

    # --- TABLA 2: DISPONIBILIDAD GLOBAL POR CANAL ---
    reporte_canales = []
    for prov in proveedores:
        sedes_que_lo_usan = Sede.objects.filter(
            Q(canal_primario=prov) | Q(canal_secundario=prov) | Q(canal_mpls=prov)).distinct()
        conteo_sedes = sedes_que_lo_usan.count()
        if conteo_sedes > 0:
            min_posibles_global = conteo_sedes * minutos_mes_total
            eventos_prov = Evento.objects.filter(Q(idproveedor=prov) & Q(fecha_inicio__lte=ultimo_dia_mes) & (
                    Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True)))
            caida_total_prov = sum(int((min(ev.fecha_fin or timezone.now(), ultimo_dia_mes) - max(ev.fecha_inicio,
                                                                                                  primer_dia_mes)).total_seconds() / 60)
                                   for ev in eventos_prov if
                                   max(ev.fecha_inicio, primer_dia_mes) < min(ev.fecha_fin or timezone.now(),
                                                                              ultimo_dia_mes))
            disp_canal = (1 - (caida_total_prov / min_posibles_global)) * 100
            reporte_canales.append({
                'nombre': prov.nombre, 'sedes_uso': conteo_sedes, 'min_caida': caida_total_prov,
                'min_posibles': min_posibles_global, 'disp': round(disp_canal, 4),
                'indisp': round(100 - disp_canal, 4), 'cumple': (disp_canal / 100) >= meta
            })

        # --- REEMPLAZA DESDE AQUÍ HACIA ABAJO EN TU VIEWS.PY ---

        # TABLA 3: MATRIZ HISTÓRICA POR PROVEEDOR (12 MESES DEL AÑO)
        meses_historial = []
        meses_nombres = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre',
                         'Octubre', 'Noviembre', 'Diciembre']

        for num_mes, nombre_corto in enumerate(meses_nombres, start=1):
            _, ult_dia = calendar.monthrange(anio, num_mes)
            p_dia_m = timezone.make_aware(datetime(anio, num_mes, 1), tz)
            u_dia_m = timezone.make_aware(datetime(anio, num_mes, ult_dia, 23, 59, 59), tz)
            min_mes_t = ult_dia * minutos_dia

            datos_mes = {'nombre': f"{nombre_corto[:3].upper()} {anio}", 'valores_prov': []}

            for prov in proveedores:
                sedes_uso = Sede.objects.filter(
                    Q(canal_primario=prov) | Q(canal_secundario=prov) | Q(canal_mpls=prov)
                ).distinct().count()

                if sedes_uso > 0:
                    min_pos_g = sedes_uso * min_mes_t
                    eventos = Evento.objects.filter(
                        Q(idproveedor=prov) & Q(fecha_inicio__lte=u_dia_m) & (
                                    Q(fecha_fin__gte=p_dia_m) | Q(fecha_fin__isnull=True))
                    )

                    caida = sum(
                        int((min(ev.fecha_fin or timezone.now(), u_dia_m) - max(ev.fecha_inicio,
                                                                                p_dia_m)).total_seconds() / 60)
                        for ev in eventos if
                        max(ev.fecha_inicio, p_dia_m) < min(ev.fecha_fin or timezone.now(), u_dia_m)
                    )

                    disp_final = round((1 - (caida / min_pos_g)) * 100, 2) if min_pos_g > 0 else 100.0
                    datos_mes['valores_prov'].append(disp_final)
                else:
                    datos_mes['valores_prov'].append(100.0)

            meses_historial.append(datos_mes)

        # TABLA 4: HISTÓRICO POR SEDE SELECCIONADA (12 MESES DEL AÑO)
        historico_sede = []
        sede_obj = Sede.objects.filter(pk=sede_id).first() if sede_id else sedes.first()

        if sede_obj:
            for numero_mes, nombre_mes in enumerate(meses_nombres, start=1):
                _, ult_dia = calendar.monthrange(anio, numero_mes)
                p_h = timezone.make_aware(datetime(anio, numero_mes, 1), tz)
                u_h = timezone.make_aware(datetime(anio, numero_mes, ult_dia, 23, 59, 59), tz)
                m_total_h = ult_dia * minutos_dia

                evs_sede = Evento.objects.filter(
                    Q(idsede=sede_obj) & Q(fecha_inicio__lte=u_h) & (Q(fecha_fin__gte=p_h) | Q(fecha_fin__isnull=True))
                )

                caida_p = calcular_minutos_caida_reales(evs_sede, p_h, u_h, 'Principal')
                caida_s = calcular_minutos_caida_reales(evs_sede, p_h, u_h, 'Respaldo')
                caida_m = calcular_minutos_caida_reales(evs_sede, p_h, u_h, 'MPLS')

                historico_sede.append({
                    'mes': f"{nombre_mes[:3].upper()} {anio}",
                    'disp_p': round((1 - (caida_p / m_total_h)) * 100, 2) if m_total_h > 0 else 100.0,
                    'disp_s': round((1 - (caida_s / m_total_h)) * 100, 2) if m_total_h > 0 else 100.0,
                    'disp_m': round((1 - (caida_m / m_total_h)) * 100, 2) if m_total_h > 0 else 100.0,
                })

        # 🔥 TABLA 5: RENDIMIENTO MPLS
        reporte_mpls = []
        for sede in sedes.exclude(canal_mpls__isnull=True):
            eventos_mes = Evento.objects.filter(Q(idsede=sede) & Q(fecha_inicio__lte=ultimo_dia_mes) & (
                    Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True)))

            caida_mpls = calcular_minutos_caida_reales(eventos_mes, primer_dia_mes, ultimo_dia_mes, 'MPLS')
            disp_mpls = round((1 - (caida_mpls / minutos_mes_total)) * 100, 4)

            reporte_mpls.append({
                'sede': sede.nombre, 'proveedor': sede.canal_mpls.nombre, 'min_caida': caida_mpls,
                'disp': disp_mpls, 'indisp': round(100 - disp_mpls, 4), 'cumple': (disp_mpls / 100) >= meta,
            })

        # 🔥 NUEVA TABLA 6: GLOBAL PROVEEDORES MPLS
        reporte_canales_mpls = []
        for prov in proveedores:
            sedes_uso_mpls = Sede.objects.filter(canal_mpls=prov).distinct()
            conteo_sedes_mpls = sedes_uso_mpls.count()

            if conteo_sedes_mpls > 0:
                min_posibles_mpls = conteo_sedes_mpls * minutos_mes_total
                eventos_prov_mpls = Evento.objects.filter(
                    Q(idproveedor=prov) & Q(rol='MPLS') & Q(fecha_inicio__lte=ultimo_dia_mes) & (
                            Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True)))

                caida_total_mpls = sum(int((min(ev.fecha_fin or timezone.now(), ultimo_dia_mes) - max(ev.fecha_inicio,
                                                                                                      primer_dia_mes)).total_seconds() / 60)
                                       for ev in eventos_prov_mpls if
                                       max(ev.fecha_inicio, primer_dia_mes) < min(ev.fecha_fin or timezone.now(),
                                                                                  ultimo_dia_mes))

                disp_canal_mpls = (1 - (caida_total_mpls / min_posibles_mpls)) * 100
                reporte_canales_mpls.append({
                    'nombre': prov.nombre, 'sedes_uso': conteo_sedes_mpls, 'min_caida': caida_total_mpls,
                    'min_posibles': min_posibles_mpls, 'disp': round(disp_canal_mpls, 4),
                    'indisp': round(100 - disp_canal_mpls, 4), 'cumple': (disp_canal_mpls / 100) >= meta
                })

        return render(request, 'dashboard.html', {
            'mes': mes, 'anio': anio, 'mes_nombre': calendar.month_name[mes].upper(),
            'minutos_mes': minutos_mes_total, 'meta_global': meta * 100,
            'reporte': reporte_sedes, 'canales': reporte_canales,
            'resumen_historico': meses_historial, 'lista_proveedores': proveedores,
            'sedes': sedes, 'historico_sede': historico_sede,
            'reporte_mpls': reporte_mpls, 'canales_mpls': reporte_canales_mpls,
            'sede_seleccionada': sede_obj, 'tab_activa': tab_activa
        })