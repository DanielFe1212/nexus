/**
 * custom_admin.js
 * Controla el menú desplegable del usuario en el header del admin.
 * Se ejecuta con DOMContentLoaded para garantizar que el DOM esté listo.
 */

document.addEventListener('DOMContentLoaded', function () {

    var btn  = document.getElementById('user-menu-btn');
    var menu = document.getElementById('user-dropdown');

    if (!btn || !menu) return;

    // Abrir / cerrar al hacer clic en el botón
    btn.addEventListener('click', function (e) {
        e.stopPropagation();
        var abierto = menu.style.display === 'flex';
        menu.style.display = abierto ? 'none' : 'flex';
    });

    // Cerrar al hacer clic fuera del menú
    document.addEventListener('click', function (e) {
        if (!btn.contains(e.target) && !menu.contains(e.target)) {
            menu.style.display = 'none';
        }
    });

    // Cerrar con tecla Escape
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            menu.style.display = 'none';
        }
    });
});
