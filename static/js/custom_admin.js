window.onload = function() {
    // 1. LOGO CLICKEABLE
    var headerLogo = document.querySelector('#branding h1 a') || document.querySelector('#header a');
    if (headerLogo) {
        headerLogo.href = "/";
        headerLogo.style.cursor = "pointer";
    }

    // 2. MANTENER FILTROS ABIERTOS
    // Al aplicar un filtro, Django añade la clase 'filtered' al id 'changelist'.
    // Este script asegura que el contenedor principal sepa que hay filtros activos.
    var changelist = document.getElementById('changelist');
    var filterPanel = document.getElementById('changelist-filter');

    if (filterPanel && changelist) {
        changelist.classList.add('filtered');
    }
};