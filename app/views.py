from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
import calendar

from .models import Sede, Evento, ConfiguracionGlobal, Proveedor


# ---> NUEVO: Función auxiliar agregada para la matriz histórica
def restar_meses(anio, mes, meses_a_restar):
    nuevo_mes = mes - meses_a_restar
    nuevo_anio = anio
    while nuevo_mes <= 0:
        nuevo_mes += 12
        nuevo_anio -= 1
    return nuevo_anio, nuevo_mes


def dashboard_kpi(request):
    # 1. Configuración de tiempo
    hoy = timezone.now()
    mes = int(request.GET.get('mes', hoy.month))
    anio = int(request.GET.get('anio', hoy.year))

    config = ConfiguracionGlobal.objects.first()
    meta = config.meta_disponibilidad if config else 0.99
    minutos_dia = config.minutos_dia if config else 1440

    tz = timezone.get_current_timezone()
    primer_dia_mes = timezone.make_aware(datetime(anio, mes, 1), tz)
    _, ultimo_dia_num = calendar.monthrange(anio, mes)
    ultimo_dia_mes = timezone.make_aware(datetime(anio, mes, ultimo_dia_num, 23, 59, 59), tz)

    minutos_mes_total = ultimo_dia_num * minutos_dia

    # ==========================================
    # TABLA 1: DISPONIBILIDAD DE SEDES (COMBINADA)
    # ==========================================
    sedes = Sede.objects.all()
    reporte_sedes = []

    for sede in sedes:
        # Filtro inteligente: Atrapa eventos del mes, incluso si no tienen fecha fin aún
        eventos_mes = Evento.objects.filter(
            Q(idsede=sede) &
            Q(fecha_inicio__lte=ultimo_dia_mes) &
            (Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True))
        )

        caida_p = 0
        caida_s = 0
        caida_simultanea = 0

        eventos_p = []
        eventos_s = []

        for ev in eventos_mes:
            inicio_real = max(ev.fecha_inicio, primer_dia_mes)
            fin_real = min(ev.fecha_fin, ultimo_dia_mes) if ev.fecha_fin else min(timezone.now(), ultimo_dia_mes)

            if inicio_real < fin_real:
                duracion = int((fin_real - inicio_real).total_seconds() / 60)
                if ev.rol == 'Principal':
                    caida_p += duracion
                    eventos_p.append((inicio_real, fin_real))
                elif ev.rol == 'Respaldo':
                    caida_s += duracion
                    eventos_s.append((inicio_real, fin_real))

        # Cálculo de Caída Simultánea (Desconexión total)
        for inicio_p, fin_p in eventos_p:
            for inicio_s, fin_s in eventos_s:
                inter_inicio = max(inicio_p, inicio_s)
                inter_fin = min(fin_p, fin_s)
                if inter_inicio < inter_fin:
                    caida_simultanea += int((inter_fin - inter_inicio).total_seconds() / 60)

        indisp_p_ratio = caida_p / minutos_mes_total
        indisp_s_ratio = caida_s / minutos_mes_total

        disp_p = (1 - indisp_p_ratio) * 100
        disp_s = (1 - indisp_s_ratio) * 100
        disp_combinada = (1 - (caida_simultanea / minutos_mes_total)) * 100

        cumple = (disp_combinada / 100) >= meta

        reporte_sedes.append({
            'sede': sede.nombre,
            'canal_p': sede.canal_primario.nombre if sede.canal_primario else "N/A",
            'min_p': caida_p,
            'disp_p': round(disp_p, 4),
            'indisp_p_pct': round(indisp_p_ratio * 100, 4),
            'canal_s': sede.canal_secundario.nombre if sede.canal_secundario else "N/A",
            'min_s': caida_s,
            'disp_s': round(disp_s, 4),
            'indisp_s_pct': round(indisp_s_ratio * 100, 4),
            'disp_total': round(disp_combinada, 4),
            'cumple': cumple,
            'meta': meta * 100
        })

    # ==========================================
    # TABLA 2: DISPONIBILIDAD GLOBAL POR CANAL
    # ==========================================
    proveedores = Proveedor.objects.all()
    reporte_canales = []

    for prov in proveedores:
        sedes_que_lo_usan = Sede.objects.filter(
            Q(canal_primario=prov) | Q(canal_secundario=prov)
        ).distinct()

        conteo_sedes = sedes_que_lo_usan.count()

        if conteo_sedes > 0:
            min_posibles_global = conteo_sedes * minutos_mes_total

            eventos_prov = Evento.objects.filter(
                Q(idproveedor=prov) &
                Q(fecha_inicio__lte=ultimo_dia_mes) &
                (Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True))
            )

            caida_total_prov = 0
            for ev in eventos_prov:
                inicio_real = max(ev.fecha_inicio, primer_dia_mes)
                fin_real = min(ev.fecha_fin, ultimo_dia_mes) if ev.fecha_fin else min(timezone.now(), ultimo_dia_mes)

                if inicio_real < fin_real:
                    caida_total_prov += int((fin_real - inicio_real).total_seconds() / 60)

            indisp_ratio = caida_total_prov / min_posibles_global
            disp_canal = (1 - indisp_ratio) * 100
            cumple_canal = (disp_canal / 100) >= meta

            reporte_canales.append({
                'nombre': prov.nombre,
                'sedes_uso': conteo_sedes,
                'min_caida': caida_total_prov,
                'min_posibles': min_posibles_global,
                'disp': round(disp_canal, 4),
                'indisp': round(indisp_ratio * 100, 4),
                'cumple': cumple_canal
            })

    # ==========================================
    # ---> NUEVO: TABLA 3: MATRIZ HISTÓRICA POR PROVEEDOR
    # ==========================================
    meses_historial = []

    for i in range(5, -1, -1):  # Calcula desde hace 5 meses hasta el mes actual
        a_h, m_h = restar_meses(anio, mes, i)

        _, ult_dia = calendar.monthrange(a_h, m_h)
        p_dia_m = timezone.make_aware(datetime(a_h, m_h, 1), tz)
        u_dia_m = timezone.make_aware(datetime(a_h, m_h, ult_dia, 23, 59, 59), tz)
        min_mes_t = ult_dia * minutos_dia

        datos_mes = {
            'nombre': f"{calendar.month_name[m_h][:3].upper()} {a_h}",
            'valores_prov': []
        }

        for prov in proveedores:
            sedes_uso = Sede.objects.filter(Q(canal_primario=prov) | Q(canal_secundario=prov)).distinct().count()

            if sedes_uso > 0:
                min_pos_g = sedes_uso * min_mes_t
                eventos = Evento.objects.filter(
                    Q(idproveedor=prov) & Q(fecha_inicio__lte=u_dia_m) &
                    (Q(fecha_fin__gte=p_dia_m) | Q(fecha_fin__isnull=True))
                )

                caida = 0
                for ev in eventos:
                    ini = max(ev.fecha_inicio, p_dia_m)
                    fin = min(ev.fecha_fin, u_dia_m) if ev.fecha_fin else min(timezone.now(), u_dia_m)
                    if ini < fin:
                        caida += int((fin - ini).total_seconds() / 60)

                disp = round((1 - (caida / min_pos_g)) * 100, 2)
            else:
                disp = 100.0  # Si no se usa en ese mes, se reporta al 100%

            datos_mes['valores_prov'].append(disp)

        meses_historial.append(datos_mes)

    # ---> NUEVO: Se agregaron 'resumen_historico' y 'lista_proveedores' al final
    return render(request, 'dashboard.html', {
        'reporte': reporte_sedes,
        'canales': reporte_canales,
        'mes_nombre': calendar.month_name[mes].upper(),
        'anio': anio,
        'minutos_mes': minutos_mes_total,
        'meta_global': meta * 100,
        'resumen_historico': meses_historial,
        'lista_proveedores': proveedores,
    })