document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    // Encontra todos os checkboxes de linha pela classe que já usam
    const rowCheckboxes = document.querySelectorAll('.edit-checkbox'); 

    if (selectAllCheckbox && rowCheckboxes.length > 0) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            
            rowCheckboxes.forEach(checkbox => {
                // Define o estado do checkbox da linha
                checkbox.checked = isChecked;
                
                // Dispara o evento 'change' no checkbox da linha
                // Isso é crucial para que o script 'produtosPage.js' 
                // seja acionado e habilite/desabilite os inputs da linha.
                const changeEvent = new Event('change');
                checkbox.dispatchEvent(changeEvent);
            });
        });
    }
});