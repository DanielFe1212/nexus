/**
 * filtros_toggle.js
 * Agrega un botón "Mostrar / Ocultar Filtros" sobre la tabla de cambios.
 * Funciona en todas las vistas de lista del admin.
 */

document.addEventListener('DOMContentLoaded', function () {

    var filtroPanel = document.getElementById('changelist-filter');
    if (!filtroPanel) return;  // Si no hay filtros, no hacer nada

    // Crear botón toggle
    var btn = document.createElement('button');
    btn.id        = 'btn-toggle-filtros';
    btn.type      = 'button';
    btn.innerHTML = '&#9776; Mostrar Filtros';

    // Insertar el botón antes del panel de filtros o antes de la tabla
    var toolbar = document.getElementById('toolbar');
    var changelist = document.getElementById('changelist');

    if (toolbar) {
        toolbar.insertAdjacentElement('afterend', btn);
    } else if (changelist) {
        changelist.insertAdjacentElement('beforebegin', btn);
    }

    // Estado inicial: filtros ocultos
    var visible = false;
    filtroPanel.classList.add('filtro-oculto');

    // Toggle al hacer click
    btn.addEventListener('click', function () {
        visible = !visible;
        if (visible) {
            filtroPanel.classList.remove('filtro-oculto');
            btn.innerHTML = '&#10005; Ocultar Filtros';
        } else {
            filtroPanel.classList.add('filtro-oculto');
            btn.innerHTML = '&#9776; Mostrar Filtros';
        }
    });

    // Si hay filtros activos (URL tiene parámetros de filtro), mostrarlos por defecto
    var urlParams   = new URLSearchParams(window.location.search);
    var paramsArr   = Array.from(urlParams.keys());
    var adminParams = ['p', 'q', 'o', 'all'];  // parámetros propios del admin, no de filtros
    var hayFiltros  = paramsArr.some(function(k) { return !adminParams.includes(k); });

    if (hayFiltros) {
        visible = true;
        filtroPanel.classList.remove('filtro-oculto');
        btn.innerHTML = '&#10005; Ocultar Filtros';
    }
});
