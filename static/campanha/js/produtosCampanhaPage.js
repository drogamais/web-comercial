// static/js/produtosCampanhaPage.js

document.addEventListener('DOMContentLoaded', function() {
    
    if (window.ProductTableUtils && window.ProductTableUtils.init) {

        // --- Configuração Específica da Página de Produtos de Campanha ---
        const config = {
            tableSelector: '#form-edit-delete table', // Seletor da tabela
            precoNormalSelector: 'input[name*="preco_normal_"]',
            precoDesconto1Selector: 'input[name*="preco_desconto_"]',
            precoDesconto2Selector: null, // Campanha não tem segundo preço de desconto relevante para validação direta
            validateGtinUrl: '/campanha/{id}/produtos/validar_gtins' // URL da API (com placeholder)
        };

        // Inicializa as funcionalidades da tabela IMEDIATAMENTE
        window.ProductTableUtils.init(config);

    } else {
        console.error("ProductTableUtils não foi carregado.");
    }    
    
// --- LÓGICA PARA O MODAL DE DELEÇÃO EM MASSA (PRODUTOS) ---
    const deleteBulkModal = document.getElementById('delete-bulk-modal');
    const showDeleteBulkModalBtn = document.getElementById('btn-show-delete-bulk-modal');
    
    if (deleteBulkModal && showDeleteBulkModalBtn) {
        const closeBulkModalBtn = document.getElementById('delete-bulk-modal-btn-close');
        const cancelBulkModalBtn = document.getElementById('delete-bulk-modal-btn-cancel');
        const deleteBulkForm = document.getElementById('delete-bulk-form');
        const passwordInput = document.getElementById('delete-bulk-modal-password');
        const confirmBulkDeleteBtn = document.getElementById('delete-bulk-modal-btn-confirm');
        const bulkDeleteCountSpan = document.getElementById('delete-bulk-modal-count');

        // *** CORREÇÃO: Senha 'REQUIRED_PASSWORD' removida daqui ***
        
        const mainForm = document.getElementById('form-edit-delete');

        const showModal = () => {
            const selectedCheckboxes = document.querySelectorAll('.edit-checkbox:checked');
            const selectedCount = selectedCheckboxes.length;

            if (selectedCount === 0) {
                alert('Selecione pelo menos um produto para deletar.');
                return;
            }
            
            // Limpa o estado anterior
            passwordInput.value = '';
            confirmBulkDeleteBtn.disabled = true; // Começa desabilitado

            bulkDeleteCountSpan.textContent = selectedCount;

            deleteBulkModal.classList.add('show-modal');
        };

        const closeModal = () => {
            deleteBulkModal.classList.remove('show-modal');
            passwordInput.value = '';
            confirmBulkDeleteBtn.disabled = true;
        };

        // *** CORREÇÃO: Habilita o botão se o campo de senha NÃO estiver vazio ***
        const checkPassword = () => {
            const isPasswordEntered = passwordInput.value.trim() !== '';
            confirmBulkDeleteBtn.disabled = !isPasswordEntered;
        };
        
        const handleConfirmDeletion = (e) => {
            e.preventDefault(); 
            
            // *** CORREÇÃO: Validação de senha REMOVIDA do JavaScript ***
            // O backend (Python) fará a validação.
            
            const deleteAction = showDeleteBulkModalBtn.getAttribute('data-delete-action'); 
            
            // 1. Altera temporariamente a action do formulário principal para a rota de deleção
            const originalAction = mainForm.action;
            mainForm.action = deleteAction; 

            // 2. Adiciona o campo de senha ao formulário principal para envio
            let passwordHiddenInput = document.getElementById('hidden-bulk-password');
            if (!passwordHiddenInput) {
                passwordHiddenInput = document.createElement('input');
                passwordHiddenInput.type = 'hidden';
                passwordHiddenInput.name = 'confirmation_password_bulk';
                passwordHiddenInput.id = 'hidden-bulk-password';
                mainForm.appendChild(passwordHiddenInput);
            }
            passwordHiddenInput.value = passwordInput.value;

            // 3. Submete o formulário principal (que contém os checkboxes selecionados)
            mainForm.submit();
        };

        // Função para controlar o estado do botão "Deletar Selecionados"
        const checkDeleteButtonState = () => {
             const selectedCheckboxes = document.querySelectorAll('.edit-checkbox:checked');
             showDeleteBulkModalBtn.disabled = selectedCheckboxes.length === 0;
        };
        
        // --- Listeners ---
        showDeleteBulkModalBtn.addEventListener('click', showModal);
        
        closeBulkModalBtn.addEventListener('click', closeModal);
        cancelBulkModalBtn.addEventListener('click', closeModal);
        
        deleteBulkModal.addEventListener('click', function(event) {
            if (event.target === this) {
                closeModal();
            }
        });
        
        // O listener 'checkPassword' agora apenas verifica se o campo está preenchido
        passwordInput.addEventListener('input', checkPassword);
        confirmBulkDeleteBtn.addEventListener('click', handleConfirmDeletion);
        
        // Listeners para os checkboxes para controlar o botão do modal
        document.querySelectorAll('.edit-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', checkDeleteButtonState);
        });
        
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox) {
             selectAllCheckbox.addEventListener('change', checkDeleteButtonState);
        }
        
        // Verifica o estado inicial
        checkDeleteButtonState();
    }
});