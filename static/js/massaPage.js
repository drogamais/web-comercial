window.App = window.App || {};

App.massaPage = {
    init: function() {
        const selectAllCheckbox = document.getElementById('selecionar-todas');
        if (selectAllCheckbox) {
            const storeCheckboxes = document.querySelectorAll('.lojas-checklist input[type="checkbox"]');
            const storeItems = document.querySelectorAll('.lojas-checklist .loja-item');

            selectAllCheckbox.addEventListener('change', function() {
                storeCheckboxes.forEach(checkbox => {
                    checkbox.checked = this.checked;
                });
            });

            storeItems.forEach(item => {
                item.addEventListener('click', function(event) {
                    if (event.target.tagName === 'LABEL' || event.target.tagName === 'INPUT') {
                        return;
                    }
                    const checkbox = this.querySelector('input[type="checkbox"]');
                    checkbox.checked = !checkbox.checked;
                });
            });
        }
    }
};