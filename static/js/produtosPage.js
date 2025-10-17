// aplicacao_web_campanhas/static/js/produtosPage.js

document.addEventListener('DOMContentLoaded', function() {
    const editCheckboxes = document.querySelectorAll('.edit-checkbox');
    if (editCheckboxes.length > 0) {
        editCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const row = this.closest('tr');
                const inputs = row.querySelectorAll('input[type="text"], input[type="number"]');
                inputs.forEach(input => {
                    input.disabled = !this.checked;
                });
            });
        });
    }
});