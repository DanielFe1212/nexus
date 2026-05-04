"""
==============================================================================
ARCHIVO: views.py
==============================================================================
Propósito:
    Controladores de la aplicación (Lógica de negocio).
    Aquí se reciben los filtros del HTML, se procesan los eventos de la BD,
    se aplican las fórmulas de SLA y se devuelven diccionarios renderizados.
==============================================================================
"""

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
import calendar

from .models import Sede, Evento, ConfiguracionGlobal, Proveedor

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def calcular_minutos_caida_reales(eventos, inicio_periodo, fin_periodo, rol_filtro):
    """ Unifica tiempos de caídas para que los minutos no se cuenten dobles. """
    intervalos = []
    for ev in eventos:
        if ev.rol == rol_filtro:
            inicio = max(ev.fecha_inicio, inicio_periodo)
            fin = min(ev.fecha_fin or timezone.now(), fin_periodo)
            if inicio < fin:
                intervalos.append((inicio, fin))

    if not intervalos: return 0

    intervalos.sort(key=lambda x: x[0])
    merged = [intervalos[0]]
    for current_start, current_end in intervalos[1:]:
        last_start, last_end = merged[-1]
        if current_start <= last_end:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))

    return sum(int((f - i).total_seconds() / 60) for i, f in merged)


# Traductor estricto para forzar Español en todo el proyecto (PUNTO 1)
MESES_ESPANOL = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# ============================================================================
# VISTA PRINCIPAL DEL DASHBOARD
# ============================================================================
def dashboard_kpi(request):
    hoy = timezone.now()

    # 1. PARÁMETROS DEL HTML
    mes_gen = int(request.GET.get('mes_gen', hoy.month))
    anio_gen = int(request.GET.get('anio_gen', hoy.year))
    anio_matriz = int(request.GET.get('anio_matriz', hoy.year))
    anio_hist = int(request.GET.get('anio_hist', hoy.year))
    sede_id_hist = request.GET.get('sede_hist')

    # 2. CONFIGURACIÓN Y FECHAS
    config = ConfiguracionGlobal.objects.first()
    meta = config.meta_disponibilidad if config else 0.99
    minutos_dia = config.minutos_dia if config else 1440
    tz = timezone.get_current_timezone()

    sedes = Sede.objects.all()
    proveedores = Proveedor.objects.all()

    primer_dia_mes = timezone.make_aware(datetime(anio_gen, mes_gen, 1), tz)
    _, ultimo_dia_num = calendar.monthrange(anio_gen, mes_gen)
    ultimo_dia_mes = timezone.make_aware(datetime(anio_gen, mes_gen, ultimo_dia_num, 23, 59, 59), tz)
    minutos_mes_total = ultimo_dia_num * minutos_dia

    # --- TABLA 1: DISPONIBILIDAD DE SEDES ---
    reporte_sedes = []
    for sede in sedes:
        eventos_mes = Evento.objects.filter(Q(idsede=sede) & Q(fecha_inicio__lte=ultimo_dia_mes) & (Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True)))

        caida_p = calcular_minutos_caida_reales(eventos_mes, primer_dia_mes, ultimo_dia_mes, 'Principal')
        caida_s = calcular_minutos_caida_reales(eventos_mes, primer_dia_mes, ultimo_dia_mes, 'Respaldo')

        caida_simultanea = 0
        eventos_p = [(max(ev.fecha_inicio, primer_dia_mes), min(ev.fecha_fin or timezone.now(), ultimo_dia_mes)) for ev in eventos_mes if ev.rol == 'Principal']
        eventos_s = [(max(ev.fecha_inicio, primer_dia_mes), min(ev.fecha_fin or timezone.now(), ultimo_dia_mes)) for ev in eventos_mes if ev.rol == 'Respaldo']
        for inicio_p, fin_p in eventos_p:
            for inicio_s, fin_s in eventos_s:
                inter_inicio = max(inicio_p, inicio_s)
                inter_fin = min(fin_p, fin_s)
                if inter_inicio < inter_fin:
                    caida_simultanea += int((inter_fin - inter_inicio).total_seconds() / 60)

        disp_combinada = (1 - (caida_simultanea / minutos_mes_total)) * 100 if minutos_mes_total > 0 else 100
        reporte_sedes.append({
            'sede': sede.nombre, 'canal_p': sede.canal_primario.nombre if sede.canal_primario else "N/A",
            'min_p': caida_p, 'disp_p': round((1 - (caida_p / minutos_mes_total)) * 100, 4) if minutos_mes_total > 0 else 100,
            'indisp_p_pct': round((caida_p / minutos_mes_total) * 100, 4) if minutos_mes_total > 0 else 0,
            'canal_s': sede.canal_secundario.nombre if sede.canal_secundario else "N/A",
            'min_s': caida_s, 'disp_s': round((1 - (caida_s / minutos_mes_total)) * 100, 4) if minutos_mes_total > 0 else 100,
            'indisp_s_pct': round((caida_s / minutos_mes_total) * 100, 4) if minutos_mes_total > 0 else 0,
            'disp_total': round(disp_combinada, 4), 'cumple': (disp_combinada / 100) >= meta, 'meta': meta * 100
        })

    # --- TABLA 2: DISPONIBILIDAD GLOBAL POR CANAL ---
    reporte_canales = []
    for prov in proveedores:
        sedes_uso = Sede.objects.filter(Q(canal_primario=prov) | Q(canal_secundario=prov) | Q(canal_mpls=prov)).distinct()
        if sedes_uso.count() > 0:
            min_posibles = sedes_uso.count() * minutos_mes_total
            evs = Evento.objects.filter(Q(idproveedor=prov) & Q(fecha_inicio__lte=ultimo_dia_mes) & (Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True)))
            caida = sum(int((min(ev.fecha_fin or timezone.now(), ultimo_dia_mes) - max(ev.fecha_inicio, primer_dia_mes)).total_seconds() / 60) for ev in evs if max(ev.fecha_inicio, primer_dia_mes) < min(ev.fecha_fin or timezone.now(), ultimo_dia_mes))
            disp = (1 - (caida / min_posibles)) * 100 if min_posibles > 0 else 100
            reporte_canales.append({
                'nombre': prov.nombre, 'sedes_uso': sedes_uso.count(), 'min_caida': caida,
                'min_posibles': min_posibles, 'disp': round(disp, 4), 'cumple': (disp / 100) >= meta
            })

    # --- TABLA 3: MATRIZ HISTÓRICA ---
    meses_historial = []
    for num_mes in range(1, 13):
        _, ult_dia = calendar.monthrange(anio_matriz, num_mes)
        p_dia_m = timezone.make_aware(datetime(anio_matriz, num_mes, 1), tz)
        u_dia_m = timezone.make_aware(datetime(anio_matriz, num_mes, ult_dia, 23, 59, 59), tz)
        min_mes_t = ult_dia * minutos_dia

        # Nombre en español (PUNTO 1)
        nombre_corto = MESES_ESPANOL[num_mes][:3].upper()
        datos_mes = {'nombre': f"{nombre_corto} {anio_matriz}", 'valores_prov': []}

        for prov in proveedores:
            sedes_uso_m = Sede.objects.filter(Q(canal_primario=prov) | Q(canal_secundario=prov) | Q(canal_mpls=prov)).distinct().count()
            if sedes_uso_m > 0:
                min_pos_g = sedes_uso_m * min_mes_t
                evs = Evento.objects.filter(Q(idproveedor=prov) & Q(fecha_inicio__lte=u_dia_m) & (Q(fecha_fin__gte=p_dia_m) | Q(fecha_fin__isnull=True)))
                caida = sum(int((min(ev.fecha_fin or timezone.now(), u_dia_m) - max(ev.fecha_inicio, p_dia_m)).total_seconds() / 60) for ev in evs if max(ev.fecha_inicio, p_dia_m) < min(ev.fecha_fin or timezone.now(), u_dia_m))
                disp_final = round((1 - (caida / min_pos_g)) * 100, 2) if min_pos_g > 0 else 100.0
                datos_mes['valores_prov'].append(disp_final)
            else:
                datos_mes['valores_prov'].append(100.0)
        meses_historial.append(datos_mes)

    # --- PREPARACIÓN PUNTO 2: Agrupación para el Acordeón (Empresa -> País) ---
    sedes_agrupadas = {}
    for s in sedes.order_by('idempresa__nombre', 'pais', 'nombre'):
        emp = s.idempresa.nombre if s.idempresa else "Sin Empresa"
        pais = s.pais if s.pais else "General"
        grupo = f"{emp} - {pais}"
        if grupo not in sedes_agrupadas:
            sedes_agrupadas[grupo] = []
        sedes_agrupadas[grupo].append(s)

    # --- TABLA 6: HISTÓRICO POR SEDE ---
    historico_sede = []
    sede_obj = Sede.objects.filter(pk=sede_id_hist).first() if sede_id_hist else sedes.first()
    if sede_obj:
        for num_mes in range(1, 13):
            _, ult_dia = calendar.monthrange(anio_hist, num_mes)
            p_h = timezone.make_aware(datetime(anio_hist, num_mes, 1), tz)
            u_h = timezone.make_aware(datetime(anio_hist, num_mes, ult_dia, 23, 59, 59), tz)
            m_total_h = ult_dia * minutos_dia

            evs_sede = Evento.objects.filter(Q(idsede=sede_obj) & Q(fecha_inicio__lte=u_h) & (Q(fecha_fin__gte=p_h) | Q(fecha_fin__isnull=True)))

            caida_p = calcular_minutos_caida_reales(evs_sede, p_h, u_h, 'Principal')
            caida_s = calcular_minutos_caida_reales(evs_sede, p_h, u_h, 'Respaldo')
            caida_m = calcular_minutos_caida_reales(evs_sede, p_h, u_h, 'MPLS')

            # Nombre en español (PUNTO 1)
            nom_mes_es = MESES_ESPANOL[num_mes][:3].upper()
            historico_sede.append({
                'mes': f"{nom_mes_es} {anio_hist}",
                'disp_p': round((1 - (caida_p / m_total_h)) * 100, 2) if m_total_h > 0 else 100.0,
                'disp_s': round((1 - (caida_s / m_total_h)) * 100, 2) if m_total_h > 0 else 100.0,
                'disp_m': round((1 - (caida_m / m_total_h)) * 100, 2) if m_total_h > 0 else 100.0,
            })

    # --- TABLAS MPLS ---
    reporte_mpls = []
    for s in sedes.exclude(canal_mpls__isnull=True):
        evs_mpls = Evento.objects.filter(Q(idsede=s) & Q(fecha_inicio__lte=ultimo_dia_mes) & (Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True)))
        caida_mpls = calcular_minutos_caida_reales(evs_mpls, primer_dia_mes, ultimo_dia_mes, 'MPLS')
        disp_mpls = round((1 - (caida_mpls / minutos_mes_total)) * 100, 4) if minutos_mes_total > 0 else 100
        reporte_mpls.append({'sede': s.nombre, 'proveedor': s.canal_mpls.nombre, 'min_caida': caida_mpls, 'disp': disp_mpls, 'indisp': round(100 - disp_mpls, 4), 'cumple': (disp_mpls / 100) >= meta})

    canales_mpls = []
    for prov in proveedores:
        s_mpls = Sede.objects.filter(canal_mpls=prov).distinct()
        if s_mpls.count() > 0:
            m_pos = s_mpls.count() * minutos_mes_total
            evs = Evento.objects.filter(Q(idproveedor=prov) & Q(rol='MPLS') & Q(fecha_inicio__lte=ultimo_dia_mes) & (Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True)))
            c = sum(int((min(ev.fecha_fin or timezone.now(), ultimo_dia_mes) - max(ev.fecha_inicio, primer_dia_mes)).total_seconds() / 60) for ev in evs if max(ev.fecha_inicio, primer_dia_mes) < min(ev.fecha_fin or timezone.now(), ultimo_dia_mes))
            d = (1 - (c / m_pos)) * 100 if m_pos > 0 else 100
            canales_mpls.append({'nombre': prov.nombre, 'sedes_uso': s_mpls.count(), 'min_caida': c, 'min_posibles': m_pos, 'disp': round(d, 4), 'cumple': (d / 100) >= meta})

    return render(request, 'dashboard.html', {
        'mes_gen': mes_gen,
        'anio_gen': anio_gen,
        'mes_nombre': MESES_ESPANOL[mes_gen].upper(), # MES EN ESPAÑOL DINÁMICO
        'anio_matriz': anio_matriz,
        'anio_hist': anio_hist,
        'sede_obj': sede_obj,
        'minutos_mes': minutos_mes_total,
        'meta_global': meta * 100,
        'reporte': reporte_sedes,
        'canales': reporte_canales,
        'resumen_historico': meses_historial,
        'lista_proveedores': proveedores,
        'sedes': sedes,
        'sedes_agrupadas': sedes_agrupadas, # ACORDEÓN
        'historico_sede': historico_sede,
        'reporte_mpls': reporte_mpls,
        'canales_mpls': canales_mpls
    })