/**
 * filtros_toggle.js  (v2)
 * ------------------------------------------------------------------
 * Agrega un botón "Mostrar / Ocultar Filtros" sobre la tabla del admin.
 * Se inserta dinámicamente y prueba varios anclajes por orden de
 * preferencia, para garantizar que sea visible en todas las vistas
 * de lista del admin (Evento, Sede, Empresa, etc.).
 *
 * Si la URL ya tiene filtros activos (?idsede=3, etc.), el panel se
 * muestra automáticamente. En caso contrario, parte oculto.
 * ------------------------------------------------------------------ */

document.addEventListener('DOMContentLoaded', function () {

    var filtroPanel = document.getElementById('changelist-filter');
    if (!filtroPanel) {
        // Vista sin filtros — no hacemos nada.
        return;
    }

    // ── Crear el botón ────────────────────────────────────────────
    var btn       = document.createElement('button');
    btn.id        = 'btn-toggle-filtros';
    btn.type      = 'button';
    btn.innerHTML = '&#9776; Mostrar Filtros';
    btn.setAttribute('aria-controls', 'changelist-filter');
    btn.setAttribute('aria-expanded', 'false');

    // ── Inserción robusta con múltiples fallbacks ─────────────────
    // Probamos varios anclajes hasta encontrar uno. El botón quedará
    // visible incluso si Django cambia la estructura del template.
    var anchor =
        document.getElementById('toolbar') ||
        document.querySelector('#changelist .actions') ||
        document.getElementById('changelist-form') ||
        document.getElementById('changelist') ||
        document.getElementById('content-main');

    if (!anchor) {
        console.warn('[filtros_toggle] No se encontró anclaje para el botón.');
        return;
    }

    // Si el anclaje está ARRIBA de la tabla, ponemos el botón después;
    // si es el contenedor mismo, lo ponemos antes.
    if (anchor.id === 'toolbar' || anchor.classList.contains('actions')) {
        anchor.insertAdjacentElement('afterend', btn);
    } else {
        anchor.insertAdjacentElement('beforebegin', btn);
    }

    // ── Estado inicial: oculto ────────────────────────────────────
    var visible = false;
    filtroPanel.classList.add('filtro-oculto');

    function setVisible(v) {
        visible = v;
        btn.setAttribute('aria-expanded', String(v));
        if (v) {
            filtroPanel.classList.remove('filtro-oculto');
            btn.innerHTML = '&#10005; Ocultar Filtros';
        } else {
            filtroPanel.classList.add('filtro-oculto');
            btn.innerHTML = '&#9776; Mostrar Filtros';
        }
    }

    btn.addEventListener('click', function () { setVisible(!visible); });

    // ── Si hay filtros activos en la URL, mostrar el panel ────────
    // Excluimos parámetros propios del admin (paginación, búsqueda).
    var urlParams   = new URLSearchParams(window.location.search);
    var adminParams = ['p', 'q', 'o', 'all', 'e'];
    var hayFiltros  = Array.from(urlParams.keys()).some(function (k) {
        return !adminParams.includes(k);
    });

    if (hayFiltros) setVisible(true);
});
