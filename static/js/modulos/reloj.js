$(document).ready(function() {
    // 1. El reloj (Intacto)
    $('.vTimeField').clockpicker({
        autoclose: true,
        donetext: 'Listo',
        placement: 'bottom',
        align: 'left',
        twelvehour: false
    });

    // 2. El calendario Inteligente
    $('.vDateField').each(function() {
        var valorOriginal = this.value; // Atrapa el texto exacto que envía Django

        // Detectamos automáticamente el formato
        // Si tiene barras (/), usamos formato d/m/Y. Si no, usamos Y-m-d.
        var formatoCorrecto = "Y-m-d";
        if (valorOriginal && valorOriginal.includes('/')) {
            formatoCorrecto = "d/m/Y";
        }

        flatpickr(this, {
            dateFormat: formatoCorrecto,
            locale: "es",
            allowInput: true,
            disableMobile: true
            // Ya no forzamos defaultDate, dejamos que Flatpickr lea el valor automáticamente
            // usando el formato correcto que acabamos de detectar.
        });
    });
});