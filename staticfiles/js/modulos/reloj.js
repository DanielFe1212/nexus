/**
 * reloj.js
 * Inicializa Flatpickr (calendario) y ClockPicker (reloj) en los campos
 * de fecha/hora del admin de Django. Calcula duración automáticamente.
 */

$(document).ready(function () {

    // ----------------------------------------------------------------
    // 1. CALENDARIO — Flatpickr en todos los campos .vDateField
    // ----------------------------------------------------------------
    $('.vDateField').each(function () {
        var valorOriginal = this.value;
        var formato = (valorOriginal && valorOriginal.includes('/')) ? 'd/m/Y' : 'Y-m-d';

        flatpickr(this, {
            dateFormat:    formato,
            locale:        'es',
            allowInput:    true,
            disableMobile: true,
            onChange: calcularDuracion
        });
    });

    // ----------------------------------------------------------------
    // 2. RELOJ — ClockPicker en todos los campos .vTimeField
    // ----------------------------------------------------------------
    $('.vTimeField').clockpicker({
        autoclose:   true,
        donetext:    'Listo',
        placement:   'bottom',
        align:       'left',
        twelvehour:  false,
        afterDone:   calcularDuracion
    });

    // ----------------------------------------------------------------
    // 3. DURACIÓN AUTOMÁTICA
    //    Lee fecha_inicio + hora_inicio, fecha_fin + hora_fin.
    //    Escribe duracion_horas y duracion_minutos. Solo lectura.
    // ----------------------------------------------------------------
    function calcularDuracion() {
        var fechaInicioVal = $('input[name="fecha_inicio_0"]').val();
        var horaInicioVal  = $('input[name="fecha_inicio_1"]').val();
        var fechaFinVal    = $('input[name="fecha_fin_0"]').val();
        var horaFinVal     = $('input[name="fecha_fin_1"]').val();

        if (!fechaInicioVal || !horaInicioVal || !fechaFinVal || !horaFinVal) return;

        // Normalizar formato de fecha (d/m/Y → Y-m-d)
        function normalizarFecha(f) {
            if (f.includes('/')) {
                var p = f.split('/');
                return p[2] + '-' + p[1] + '-' + p[0];
            }
            return f;
        }

        var inicio = new Date(normalizarFecha(fechaInicioVal) + 'T' + horaInicioVal + ':00');
        var fin    = new Date(normalizarFecha(fechaFinVal)    + 'T' + horaFinVal    + ':00');

        if (isNaN(inicio.getTime()) || isNaN(fin.getTime())) return;
        if (fin <= inicio) return;

        var diffMs      = fin - inicio;
        var diffMinutos = Math.round(diffMs / 60000);
        var horas       = Math.floor(diffMinutos / 60);
        var minutos     = diffMinutos % 60;

        var inputHoras   = $('input[name="duracion_horas"]');
        var inputMinutos = $('input[name="duracion_minutos"]');

        // Escribir valores calculados
        inputHoras.val(horas + 'h ' + minutos + 'm');
        inputMinutos.val(diffMinutos);

        // Marcar visualmente como solo lectura
        inputHoras.addClass('campo-solo-lectura');
        inputMinutos.addClass('campo-solo-lectura');
    }

    // ----------------------------------------------------------------
    // 4. BLOQUEAR edición manual de duracion_horas y duracion_minutos
    // ----------------------------------------------------------------
    $(document).on('keydown paste', 'input[name="duracion_horas"], input[name="duracion_minutos"]', function (e) {
        e.preventDefault();
        return false;
    });

    // Calcular si ya vienen con valores al cargar (edición de evento existente)
    calcularDuracion();

    // Recalcular también al cambiar fecha/hora manualmente con input
    $(document).on('change', '.vDateField, .vTimeField', calcularDuracion);
});
