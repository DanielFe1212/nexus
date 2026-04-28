window.addEventListener('load', function() {
    // Buscamos el contenedor de la barra de arriba
    var actionContainer = document.querySelector('.actions');

    if (actionContainer) {
        var actionSelect = actionContainer.querySelector('select[name="action"]');
        var runButton = actionContainer.querySelector('button[name="index"]');

        if (actionSelect && runButton) {
            // 1. Le decimos a la lista oculta que la acción por defecto es Eliminar
            actionSelect.value = 'delete_selected';

            // 2. Creamos nuestro botón rojo moderno
            var deleteBtn = document.createElement('button');
            deleteBtn.innerHTML = '🗑️ Eliminar Seleccionados';
            deleteBtn.className = 'btn-eliminar-custom';

            // 3. Qué pasa al hacerle clic
            deleteBtn.onclick = function(e) {
                e.preventDefault(); // Evitamos que la página salte

                // Revisamos si el usuario seleccionó al menos un cuadrito
                var seleccionados = document.querySelectorAll('.action-select:checked').length;

                if (seleccionados === 0) {
                    alert('⚠️ Por favor, selecciona al menos un evento marcando la casilla de la izquierda.');
                    return;
                }

                // Si todo está bien, disparamos el botón original oculto
                runButton.click();
            };

            // 4. Metemos el botón al inicio de la barra
            actionContainer.prepend(deleteBtn);
        }
    }
});