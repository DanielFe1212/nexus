/**
 * filtros_toggle.js  (v3)
 * ------------------------------------------------------------------
 * Botón "Mostrar / Ocultar Filtros" en el changelist del admin.
 *
 * Cuando se ocultan los filtros:
 *   - Se añade .filtro-oculto al panel #changelist-filter (lo esconde).
 *   - Se añade .filtros-ocultos al <body> (señaliza al CSS que la tabla
 *     debe expandirse al 100%, anulando el max-width nativo de Django 6
 *     que reservaba 270px para el panel).
 * ------------------------------------------------------------------ */

document.addEventListener('DOMContentLoaded', function () {

    var filtroPanel = document.getElementById('changelist-filter');
    if (!filtroPanel) return;  // Vista sin filtros — nada que hacer

    var btn       = document.createElement('button');
    btn.id        = 'btn-toggle-filtros';
    btn.type      = 'button';
    btn.innerHTML = '&#9776; Mostrar Filtros';
    btn.setAttribute('aria-controls', 'changelist-filter');
    btn.setAttribute('aria-expanded', 'false');

    var anchor =
        document.getElementById('toolbar') ||
        document.querySelector('#changelist .actions') ||
        document.getElementById('changelist-form') ||
        document.getElementById('changelist') ||
        document.getElementById('content-main');

    if (!anchor) { console.warn('[filtros_toggle] sin anclaje'); return; }

    if (anchor.id === 'toolbar' || anchor.classList.contains('actions')) {
        anchor.insertAdjacentElement('afterend', btn);
    } else {
        anchor.insertAdjacentElement('beforebegin', btn);
    }

    var visible = false;

    function setVisible(v) {
        visible = v;
        btn.setAttribute('aria-expanded', String(v));
        if (v) {
            filtroPanel.classList.remove('filtro-oculto');
            document.body.classList.remove('filtros-ocultos');
            btn.innerHTML = '&#10005; Ocultar Filtros';
        } else {
            filtroPanel.classList.add('filtro-oculto');
            document.body.classList.add('filtros-ocultos');
            btn.innerHTML = '&#9776; Mostrar Filtros';
        }
    }

    // Estado inicial: oculto
    setVisible(false);

    btn.addEventListener('click', function () { setVisible(!visible); });

    // Si la URL trae filtros activos, mostrar el panel
    var urlParams   = new URLSearchParams(window.location.search);
    var adminParams = ['p', 'q', 'o', 'all', 'e'];
    var hayFiltros  = Array.from(urlParams.keys()).some(function (k) {
        return !adminParams.includes(k);
    });

    if (hayFiltros) setVisible(true);
});
