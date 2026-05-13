/**
 * evento_proveedores.js
 * ------------------------------------------------------------------
 * En el formulario de Evento del admin:
 * cuando el usuario cambia la sede (#id_idsede), llama al endpoint
 *   /admin/api/proveedores-de-sede/<id>/
 * y reemplaza las opciones del select #id_idproveedor por los
 * 3 canales asignados a esa sede (primario, secundario, MPLS).
 *
 * Si NO se ha elegido sede aún, el select queda deshabilitado con
 * un mensaje de "Primero selecciona una sede".
 * ------------------------------------------------------------------ */

document.addEventListener('DOMContentLoaded', function () {

    var selectSede      = document.getElementById('id_idsede');
    var selectProveedor = document.getElementById('id_idproveedor');

    if (!selectSede || !selectProveedor) {
        // No estamos en el form de Evento — salir.
        return;
    }

    // Guardamos el valor inicial del proveedor (para preservarlo al editar)
    var proveedorInicial = selectProveedor.value;

    function vaciarOpciones() {
        selectProveedor.innerHTML = '';
        var opt = document.createElement('option');
        opt.value = '';
        opt.textContent = '— Primero selecciona una sede —';
        selectProveedor.appendChild(opt);
        selectProveedor.disabled = true;
    }

    function cargarProveedores(sedeId, preseleccionar) {
        if (!sedeId) { vaciarOpciones(); return; }

        fetch('/admin/api/proveedores-de-sede/' + sedeId + '/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin'
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            selectProveedor.innerHTML = '';
            selectProveedor.disabled  = false;

            // Opción vacía
            var optVacio = document.createElement('option');
            optVacio.value = '';
            optVacio.textContent = '---------';
            selectProveedor.appendChild(optVacio);

            // Opciones reales
            (data.proveedores || []).forEach(function (p) {
                var opt = document.createElement('option');
                opt.value       = p.id;
                opt.textContent = p.nombre;
                if (preseleccionar && String(p.id) === String(preseleccionar)) {
                    opt.selected = true;
                }
                selectProveedor.appendChild(opt);
            });

            if (!data.proveedores || data.proveedores.length === 0) {
                var optNone = document.createElement('option');
                optNone.value = '';
                optNone.textContent = '(Esta sede no tiene proveedores asignados)';
                optNone.disabled = true;
                selectProveedor.appendChild(optNone);
            }
        })
        .catch(function (err) {
            console.error('[evento_proveedores] Error al cargar:', err);
        });
    }

    // ── Estado inicial ─────────────────────────────────────────────
    if (selectSede.value) {
        // Al editar un evento existente, cargamos y mantenemos selección.
        cargarProveedores(selectSede.value, proveedorInicial);
    } else {
        vaciarOpciones();
    }

    // ── Listener al cambiar sede ───────────────────────────────────
    selectSede.addEventListener('change', function () {
        cargarProveedores(this.value, null);
    });
});
