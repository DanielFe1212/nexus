document.addEventListener("DOMContentLoaded", function () {

    // LOGO CLICK → HOME
    const logo = document.querySelector('#branding a');
    if (logo) {
        logo.href = "/admin/";
    }

    // MENÚ USUARIO
    const btn = document.getElementById('user-menu-btn');
    const menu = document.getElementById('user-dropdown');

    if (btn && menu) {
        btn.addEventListener("click", function (e) {
            e.stopPropagation();
            menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
        });

        document.addEventListener("click", function () {
            menu.style.display = 'none';
        });
    }

    // FILTROS ACTIVOS
    const changelist = document.getElementById('changelist');
    const filterPanel = document.getElementById('changelist-filter');

    if (filterPanel && changelist) {
        changelist.classList.add('filtered');
    }
});
``