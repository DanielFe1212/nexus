document.addEventListener("DOMContentLoaded", function () {

    function initDeleteButton() {
        const actionContainer = document.querySelector('.actions');

        if (!actionContainer) {
            setTimeout(initDeleteButton, 300);
            return;
        }

        const actionSelect = actionContainer.querySelector('select[name="action"]');
        const runButton = actionContainer.querySelector('button[name="index"]');

        if (!actionSelect || !runButton) return;

        if (document.querySelector('.btn-eliminar-custom')) return;

        const deleteBtn = document.createElement('button');
        deleteBtn.innerHTML = '🗑️ Eliminar Seleccionados';
        deleteBtn.className = 'btn-eliminar-custom';

        deleteBtn.onclick = function(e) {
            e.preventDefault();

            const seleccionados = document.querySelectorAll('.action-select:checked').length;

            if (!seleccionados) {
                alert('⚠️ Selecciona registros primero.');
                return;
            }

            actionSelect.value = 'delete_selected';
            runButton.click();
        };

        actionContainer.prepend(deleteBtn);
    }

    initDeleteButton();
});