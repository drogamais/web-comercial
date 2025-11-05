// Define a função de inicialização que o base.html espera
window.initSelectAll = () => {
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    // Se não houver checkbox "select-all" nesta página, não faz nada
    if (!selectAllCheckbox) return;

    const rowCheckboxes = document.querySelectorAll('.edit-checkbox'); 

    const handleSelectAll = (e) => {
        const isChecked = e.currentTarget.checked;
        
        rowCheckboxes.forEach(checkbox => {
            // Define o estado do checkbox da linha
            checkbox.checked = isChecked;
            
            // Dispara o evento 'change' no checkbox da linha
            // Isso é crucial para que o script 'produtosPage.js' 
            // seja acionado e habilite/desabilite os inputs da linha.
            const changeEvent = new Event('change');
            checkbox.dispatchEvent(changeEvent);
        });
    };

    if (rowCheckboxes.length > 0) {
        selectAllCheckbox.removeEventListener('change', handleSelectAll); // Evita duplicatas
        selectAllCheckbox.addEventListener('change', handleSelectAll);
    }
};