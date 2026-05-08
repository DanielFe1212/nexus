document.addEventListener("DOMContentLoaded", function () {

    const btn = document.getElementById('user-menu-btn');
    const menu = document.getElementById('user-dropdown');

    if (btn && menu) {

        btn.addEventListener("click", function (e) {
            e.stopPropagation();
            menu.style.display =
                menu.style.display === 'flex' ? 'none' : 'flex';
        });

        document.addEventListener("click", function () {
            menu.style.display = 'none';
        });
    }
});
