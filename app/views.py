"""
==============================================================================
ARCHIVO: views.py
==============================================================================
Propósito:
    Controladores de la aplicación (lógica de negocio).
    PUNTO 7: Optimizado con select_related/prefetch_related para reducir
    el número de queries a la base de datos (N+1 eliminado).
==============================================================================
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Q, Prefetch
from datetime import datetime
import calendar

from .models import Sede, Evento, ConfiguracionGlobal, Proveedor

# ============================================================================
# CONSTANTES
# ============================================================================

MESES_ESPANOL = {
    1: 'Enero',    2: 'Febrero',   3: 'Marzo',    4: 'Abril',
    5: 'Mayo',     6: 'Junio',     7: 'Julio',     8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def calcular_minutos_caida_reales(eventos, inicio_periodo, fin_periodo, rol_filtro):
    """
    Fusiona intervalos de caída solapados para no contar minutos dobles.
    Recibe una lista de objetos Evento ya cargados en memoria (sin hit a BD).
    """
    intervalos = []
    for ev in eventos:
        if ev.rol != rol_filtro:
            continue
        inicio = max(ev.fecha_inicio, inicio_periodo)
        fin    = min(ev.fecha_fin or timezone.now(), fin_periodo)
        if inicio < fin:
            intervalos.append((inicio, fin))

    if not intervalos:
        return 0

    intervalos.sort(key=lambda x: x[0])
    merged = [intervalos[0]]
    for c_inicio, c_fin in intervalos[1:]:
        u_inicio, u_fin = merged[-1]
        if c_inicio <= u_fin:
            merged[-1] = (u_inicio, max(u_fin, c_fin))
        else:
            merged.append((c_inicio, c_fin))

    return sum(int((f - i).total_seconds() / 60) for i, f in merged)


def _rango_mes(anio, mes, tz, minutos_dia):
    """Devuelve (primer_dia, ultimo_dia, minutos_totales) de un mes."""
    _, ult_num = calendar.monthrange(anio, mes)
    p_dia = timezone.make_aware(datetime(anio, mes, 1), tz)
    u_dia = timezone.make_aware(datetime(anio, mes, ult_num, 23, 59, 59), tz)
    return p_dia, u_dia, ult_num * minutos_dia


# ============================================================================
# VISTA PRINCIPAL DEL DASHBOARD
# ============================================================================

def dashboard_kpi(request):
    hoy = timezone.now()

    # ── Parámetros GET ────────────────────────────────────────────────────────
    mes_gen      = int(request.GET.get('mes_gen',    hoy.month))
    anio_gen     = int(request.GET.get('anio_gen',   hoy.year))
    anio_matriz  = int(request.GET.get('anio_matriz', hoy.year))
    anio_hist    = int(request.GET.get('anio_hist',  hoy.year))
    sede_id_hist = request.GET.get('sede_hist')

    # ── Configuración ─────────────────────────────────────────────────────────
    config      = ConfiguracionGlobal.objects.first()
    meta        = config.meta_disponibilidad if config else 0.99
    minutos_dia = config.minutos_dia         if config else 1440
    tz          = timezone.get_current_timezone()

    primer_dia_mes, ultimo_dia_mes, minutos_mes_total = _rango_mes(anio_gen, mes_gen, tz, minutos_dia)

    # ── PUNTO 7: Carga eficiente — select_related elimina queries N+1 ────────
    sedes = Sede.objects.select_related(
        'idempresa', 'canal_primario', 'canal_secundario', 'canal_mpls', 'nodo_central_mpls'
    ).all()

    proveedores = Proveedor.objects.all()

    # Eventos del mes actual precargados de una sola vez
    eventos_mes_todos = list(
        Evento.objects.filter(
            Q(fecha_inicio__lte=ultimo_dia_mes) &
            (Q(fecha_fin__gte=primer_dia_mes) | Q(fecha_fin__isnull=True))
        ).select_related('idsede', 'idproveedor')
    )

    # ── TABLA 1: DISPONIBILIDAD DE SEDES ─────────────────────────────────────
    reporte_sedes = []
    for sede in sedes:
        # Filtrar en Python (ya vinieron todos de la BD)
        evs = [e for e in eventos_mes_todos if e.idsede_id == sede.pk]

        caida_p = calcular_minutos_caida_reales(evs, primer_dia_mes, ultimo_dia_mes, 'Principal')
        caida_s = calcular_minutos_caida_reales(evs, primer_dia_mes, ultimo_dia_mes, 'Respaldo')

        # Caída simultánea de ambos canales
        ints_p = [(max(e.fecha_inicio, primer_dia_mes), min(e.fecha_fin or timezone.now(), ultimo_dia_mes))
                  for e in evs if e.rol == 'Principal']
        ints_s = [(max(e.fecha_inicio, primer_dia_mes), min(e.fecha_fin or timezone.now(), ultimo_dia_mes))
                  for e in evs if e.rol == 'Respaldo']
        caida_sim = sum(
            int((min(fp, fs) - max(ip, is_)).total_seconds() / 60)
            for ip, fp in ints_p for is_, fs in ints_s
            if max(ip, is_) < min(fp, fs)
        )

        disp_comb = (1 - caida_sim / minutos_mes_total) * 100 if minutos_mes_total else 100
        reporte_sedes.append({
            'sede':        sede.nombre,
            'canal_p':     sede.canal_primario.nombre   if sede.canal_primario   else 'N/A',
            'min_p':       caida_p,
            'disp_p':      round((1 - caida_p / minutos_mes_total) * 100, 4) if minutos_mes_total else 100,
            'indisp_p_pct': round(caida_p / minutos_mes_total * 100, 4)      if minutos_mes_total else 0,
            'canal_s':     sede.canal_secundario.nombre if sede.canal_secundario else 'N/A',
            'min_s':       caida_s,
            'disp_s':      round((1 - caida_s / minutos_mes_total) * 100, 4) if minutos_mes_total else 100,
            'indisp_s_pct': round(caida_s / minutos_mes_total * 100, 4)      if minutos_mes_total else 0,
            'disp_total':  round(disp_comb, 4),
            'cumple':      (disp_comb / 100) >= meta,
            'meta':        meta * 100,
        })

    # ── TABLA 2: DISPONIBILIDAD GLOBAL POR CANAL ─────────────────────────────
    reporte_canales = []
    for prov in proveedores:
        sedes_uso = [s for s in sedes if prov.pk in (
            s.canal_primario_id, s.canal_secundario_id, s.canal_mpls_id
        )]
        if not sedes_uso:
            continue
        sedes_ids = {s.pk for s in sedes_uso}
        evs_prov  = [e for e in eventos_mes_todos if e.idproveedor_id == prov.pk and e.idsede_id in sedes_ids]
        min_pos   = len(sedes_uso) * minutos_mes_total
        caida     = sum(
            int((min(e.fecha_fin or timezone.now(), ultimo_dia_mes) - max(e.fecha_inicio, primer_dia_mes)).total_seconds() / 60)
            for e in evs_prov
            if max(e.fecha_inicio, primer_dia_mes) < min(e.fecha_fin or timezone.now(), ultimo_dia_mes)
        )
        disp = (1 - caida / min_pos) * 100 if min_pos else 100
        reporte_canales.append({
            'nombre':    prov.nombre,
            'sedes_uso': len(sedes_uso),
            'min_caida': caida,
            'min_posibles': min_pos,
            'disp':      round(disp, 4),
            'cumple':    (disp / 100) >= meta,
        })

    # ── TABLA 3: MATRIZ HISTÓRICA ANUAL ──────────────────────────────────────
    # Una sola query para todo el año
    p_anio = timezone.make_aware(datetime(anio_matriz, 1,  1,  0, 0, 0), tz)
    u_anio = timezone.make_aware(datetime(anio_matriz, 12, 31, 23, 59, 59), tz)
    eventos_anio = list(
        Evento.objects.filter(
            Q(fecha_inicio__lte=u_anio) &
            (Q(fecha_fin__gte=p_anio) | Q(fecha_fin__isnull=True))
        ).select_related('idproveedor')
    )

    meses_historial = []
    for num_mes in range(1, 13):
        p_m, u_m, min_m = _rango_mes(anio_matriz, num_mes, tz, minutos_dia)
        evs_mes = [e for e in eventos_anio if e.fecha_inicio <= u_m and (e.fecha_fin or timezone.now()) >= p_m]
        datos_mes = {'nombre': f"{MESES_ESPANOL[num_mes][:3].upper()} {anio_matriz}", 'valores_prov': []}
        for prov in proveedores:
            sedes_cnt = sum(1 for s in sedes if prov.pk in (s.canal_primario_id, s.canal_secundario_id, s.canal_mpls_id))
            if not sedes_cnt:
                datos_mes['valores_prov'].append(100.0)
                continue
            evs_p  = [e for e in evs_mes if e.idproveedor_id == prov.pk]
            min_p  = sedes_cnt * min_m
            caida  = sum(
                int((min(e.fecha_fin or timezone.now(), u_m) - max(e.fecha_inicio, p_m)).total_seconds() / 60)
                for e in evs_p if max(e.fecha_inicio, p_m) < min(e.fecha_fin or timezone.now(), u_m)
            )
            datos_mes['valores_prov'].append(round((1 - caida / min_p) * 100, 2) if min_p else 100.0)
        meses_historial.append(datos_mes)

    # ── TABLA 4: RENDIMIENTO MPLS ─────────────────────────────────────────────
    reporte_mpls = []
    for s in sedes:
        if not s.canal_mpls_id:
            continue
        evs_s = [e for e in eventos_mes_todos if e.idsede_id == s.pk]
        if s.nodo_central_mpls_id:
            evs_s += [e for e in eventos_mes_todos if e.idsede_id == s.nodo_central_mpls_id and e.rol == 'MPLS']
        caida_m = calcular_minutos_caida_reales(evs_s, primer_dia_mes, ultimo_dia_mes, 'MPLS')
        disp_m  = round((1 - caida_m / minutos_mes_total) * 100, 4) if minutos_mes_total else 100
        reporte_mpls.append({
            'sede':      s.nombre,
            'proveedor': s.canal_mpls.nombre,
            'min_caida': caida_m,
            'disp':      disp_m,
            'indisp':    round(100 - disp_m, 4),
            'cumple':    (disp_m / 100) >= meta,
        })

    # ── TABLA 5: GLOBAL PROVEEDORES MPLS ─────────────────────────────────────
    canales_mpls = []
    for prov in proveedores:
        s_mpls = [s for s in sedes if s.canal_mpls_id == prov.pk]
        if not s_mpls:
            continue
        m_pos   = len(s_mpls) * minutos_mes_total
        c_total = 0
        for s in s_mpls:
            evs_s = [e for e in eventos_mes_todos if e.idsede_id == s.pk]
            if s.nodo_central_mpls_id:
                evs_s += [e for e in eventos_mes_todos if e.idsede_id == s.nodo_central_mpls_id and e.rol == 'MPLS']
            c_total += calcular_minutos_caida_reales(evs_s, primer_dia_mes, ultimo_dia_mes, 'MPLS')
        d = (1 - c_total / m_pos) * 100 if m_pos else 100
        canales_mpls.append({
            'nombre':    prov.nombre,
            'sedes_uso': len(s_mpls),
            'min_caida': c_total,
            'min_posibles': m_pos,
            'disp':      round(d, 4),
            'cumple':    (d / 100) >= meta,
        })

    # ── TABLA 6: HISTÓRICO POR SEDE ───────────────────────────────────────────
    sedes_agrupadas = {}
    for s in sorted(sedes, key=lambda x: (x.idempresa.nombre, x.pais or '', x.nombre)):
        grupo = f"{s.idempresa.nombre} - {s.pais or 'General'}"
        sedes_agrupadas.setdefault(grupo, []).append(s)

    sede_obj     = next((s for s in sedes if str(s.pk) == str(sede_id_hist)), None) or (list(sedes)[0] if sedes else None)
    historico_sede = []

    if sede_obj:
        p_anio_h = timezone.make_aware(datetime(anio_hist, 1,  1,  0, 0, 0), tz)
        u_anio_h = timezone.make_aware(datetime(anio_hist, 12, 31, 23, 59, 59), tz)
        ids_filtro = {sede_obj.pk}
        if sede_obj.nodo_central_mpls_id:
            ids_filtro.add(sede_obj.nodo_central_mpls_id)

        eventos_hist = list(
            Evento.objects.filter(
                Q(idsede_id__in=ids_filtro) &
                Q(fecha_inicio__lte=u_anio_h) &
                (Q(fecha_fin__gte=p_anio_h) | Q(fecha_fin__isnull=True))
            )
        )

        for num_mes in range(1, 13):
            p_h, u_h, m_h = _rango_mes(anio_hist, num_mes, tz, minutos_dia)
            evs_h = [e for e in eventos_hist if e.fecha_inicio <= u_h and (e.fecha_fin or timezone.now()) >= p_h]
            # Filtrar herencia MPLS
            evs_filtrados = [e for e in evs_h if e.idsede_id == sede_obj.pk or e.rol == 'MPLS']
            historico_sede.append({
                'mes':    f"{MESES_ESPANOL[num_mes][:3].upper()} {anio_hist}",
                'disp_p': round((1 - calcular_minutos_caida_reales(evs_filtrados, p_h, u_h, 'Principal') / m_h) * 100, 2) if m_h else 100.0,
                'disp_s': round((1 - calcular_minutos_caida_reales(evs_filtrados, p_h, u_h, 'Respaldo')  / m_h) * 100, 2) if m_h else 100.0,
                'disp_m': round((1 - calcular_minutos_caida_reales(evs_filtrados, p_h, u_h, 'MPLS')      / m_h) * 100, 2) if m_h else 100.0,
            })

    return render(request, 'dashboard.html', {
        'mes_gen':          mes_gen,
        'anio_gen':         anio_gen,
        'mes_nombre':       MESES_ESPANOL[mes_gen].upper(),
        'anio_matriz':      anio_matriz,
        'anio_hist':        anio_hist,
        'sede_obj':         sede_obj,
        'minutos_mes':      minutos_mes_total,
        'meta_global':      meta * 100,
        'reporte':          reporte_sedes,
        'canales':          reporte_canales,
        'resumen_historico': meses_historial,
        'lista_proveedores': proveedores,
        'sedes':            sedes,
        'sedes_agrupadas':  sedes_agrupadas,
        'historico_sede':   historico_sede,
        'reporte_mpls':     reporte_mpls,
        'canales_mpls':     canales_mpls,
    })


# ============================================================================
# API — Proveedores asignados a una sede (para filtro dinámico en form Evento)
# ============================================================================

@staff_member_required
def proveedores_de_sede(request, sede_id):
    """
    Devuelve los proveedores asignados a una sede como JSON.
    Lo consume el JS evento_proveedores.js que filtra el select de
    Idproveedor según la Idsede elegida por el operador.

    Endpoint: GET /admin/api/proveedores-de-sede/<id_sede>/
    Respuesta: {"proveedores": [{"id": 1, "nombre": "Cirion"}, ...]}
    """
    try:
        sede = Sede.objects.select_related(
            'canal_primario', 'canal_secundario', 'canal_mpls'
        ).get(pk=sede_id)
    except Sede.DoesNotExist:
        return JsonResponse({'proveedores': []})

    proveedores = []
    vistos = set()
    for canal in (sede.canal_primario, sede.canal_secundario, sede.canal_mpls):
        if canal and canal.pk not in vistos:
            proveedores.append({'id': canal.pk, 'nombre': canal.nombre})
            vistos.add(canal.pk)

    return JsonResponse({'proveedores': proveedores})
