(function() {
    document.addEventListener('DOMContentLoaded', function() {

        const actionContainer = document.querySelector('.actions');
        if (!actionContainer) return;

        const actionSelect = actionContainer.querySelector('select[name="action"]');
        const runButton = actionContainer.querySelector('button[name="index"]');

        if (actionSelect && runButton) {

            const deleteBtn = document.createElement('button');
            deleteBtn.innerHTML = '🗑️ Eliminar Seleccionados';
            deleteBtn.className = 'btn-eliminar-custom';

            deleteBtn.onclick = function(e) {
                e.preventDefault();

                const seleccionados = document.querySelectorAll('.action-select:checked').length;

                if (seleccionados === 0) {
                    alert('⚠️ Selecciona registros primero.');
                    return;
                }

                actionSelect.value = 'delete_selected';
                runButton.click();
            };

            actionContainer.prepend(deleteBtn);
        }
    });
})();