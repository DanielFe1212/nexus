/**
 * reloj.js
 * ------------------------------------------------------------------
 * Engancha Flatpickr al form de Evento del admin:
 *   - .vDateField  → calendario en español
 *   - .vTimeField  → reloj 24h con formato H:i:S (lo que Django espera)
 *
 * Adicionalmente, calcula automáticamente la duración (horas y minutos)
 * cuando ambas fechas/horas están completas.
 * ------------------------------------------------------------------ */

window.addEventListener('load', function () {

    // Verificamos que Flatpickr cargó correctamente
    if (typeof flatpickr === 'undefined') {
        console.warn('[reloj.js] Flatpickr no está cargado. ' +
                     'Verifica que flatpickr.min.js exista en static/js/vendor/.');
        return;
    }

    // 1. EL CALENDARIO (Para las fechas)
    flatpickr('.vDateField', {
        dateFormat: 'Y-m-d',
        locale:     'es',
        allowInput: true,
        disableMobile: 'true',
        onChange:   calcularDuracion
    });

    // 2. EL RELOJ DE FLATPICKR (Para las horas)
    flatpickr('.vTimeField', {
        enableTime:    true,     // Activa el modo de hora
        noCalendar:    true,     // Apaga el calendario aquí
        dateFormat:    'H:i:S',  // Formato exacto que pide Django
        time_24hr:     true,     // Formato 24 horas
        locale:        'es',
        allowInput:    true,
        disableMobile: 'true',
        onChange:      calcularDuracion
    });

    // 3. CALCULAR duración automáticamente cuando ambos campos están listos
    function calcularDuracion() {
        var fi = document.querySelector('input[name="fecha_inicio_0"]');
        var hi = document.querySelector('input[name="fecha_inicio_1"]');
        var ff = document.querySelector('input[name="fecha_fin_0"]');
        var hf = document.querySelector('input[name="fecha_fin_1"]');

        if (!fi || !hi || !ff || !hf) return;
        if (!fi.value || !hi.value || !ff.value || !hf.value) return;

        // Las fechas pueden venir en formato Y-m-d (flatpickr) o d/m/Y (Django default)
        function normalizarFecha(f) {
            if (f.indexOf('/') !== -1) {
                var p = f.split('/');
                return p[2] + '-' + p[1] + '-' + p[0];
            }
            return f;
        }

        // Si la hora viene sin segundos (H:i), agregamos :00
        function normalizarHora(h) {
            return h.length === 5 ? h + ':00' : h;
        }

        var inicio = new Date(normalizarFecha(fi.value) + 'T' + normalizarHora(hi.value));
        var fin    = new Date(normalizarFecha(ff.value) + 'T' + normalizarHora(hf.value));

        if (isNaN(inicio.getTime()) || isNaN(fin.getTime())) return;
        if (fin <= inicio) return;

        var diffMs      = fin - inicio;
        var diffMinutos = Math.round(diffMs / 60000);
        var horas       = Math.floor(diffMinutos / 60);
        var minutos     = diffMinutos % 60;

        var iHoras = document.querySelector('input[name="duracion_horas"]');
        var iMin   = document.querySelector('input[name="duracion_minutos"]');

        if (iHoras) {
            iHoras.value = horas + 'h ' + minutos + 'm';
            iHoras.classList.add('campo-solo-lectura');
        }
        if (iMin) {
            iMin.value = diffMinutos;
            iMin.classList.add('campo-solo-lectura');
        }
    }

    // 4. Bloquear edición manual de duración
    document.addEventListener('keydown', function (e) {
        var t = e.target;
        if (t && t.matches &&
            t.matches('input[name="duracion_horas"], input[name="duracion_minutos"]')) {
            e.preventDefault();
            return false;
        }
    });
    document.addEventListener('paste', function (e) {
        var t = e.target;
        if (t && t.matches &&
            t.matches('input[name="duracion_horas"], input[name="duracion_minutos"]')) {
            e.preventDefault();
            return false;
        }
    });

    // Calcular al cargar (cuando editamos un evento existente)
    calcularDuracion();
});
