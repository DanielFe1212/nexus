$(document).ready(function() {
    // 1. El relojito para las horas
    $('.vTimeField').clockpicker({
        autoclose: true,
        donetext: 'Listo',
        placement: 'bottom',
        align: 'left',
        twelvehour: false
    });

    // 2. 🔥 EL NUEVO CALENDARIO
    flatpickr(".vDateField", {
        dateFormat: "Y-m-d", // El formato exacto que pide la base de datos de Django
        locale: "es",        // Lo ponemos en perfecto español
        allowInput: true,    // Permite escribir si el usuario prefiere teclear
        disableMobile: "true" // Evita conflictos en celulares
    });
});