window.App = window.App || {};

App.formHandler = {
    init: function() {
        const btnLimpar = document.getElementById('btn-limpar');
        const confirmModal = document.getElementById('confirm-modal');
        
        if (btnLimpar && confirmModal) {
            const modalBtnConfirm = document.getElementById('modal-btn-confirm');
            const modalBtnCancel = document.getElementById('modal-btn-cancel');

            // Mostra o modal de confirmação ao clicar no botão "Limpar"
            btnLimpar.addEventListener('click', () => confirmModal.classList.add('show-modal'));
            
            // Esconde o modal ao clicar em "Cancelar"
            modalBtnCancel.addEventListener('click', () => confirmModal.classList.remove('show-modal'));

            // ALTERAÇÃO: Lógica do botão de confirmação
            modalBtnConfirm.addEventListener('click', function() {
                // Pega a URL de limpeza do atributo 'data-url' do botão
                const cleanUrl = btnLimpar.getAttribute('data-url');
                
                // Se a URL existir, redireciona a página para ela
                if (cleanUrl) {
                    window.location.href = cleanUrl;
                } else {
                    // Caso de fallback, apenas esconde o modal
                    confirmModal.classList.remove('show-modal');
                }
            });
        }
    }
};