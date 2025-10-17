window.App = window.App || {};

App.editPage = {
    init: function() {
        // Lógica existente para habilitar/desabilitar campos
        const editCheckboxes = document.querySelectorAll('.edit-checkbox');
        if (editCheckboxes.length > 0) {
            editCheckboxes.forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const row = this.closest('tr');
                    const inputs = row.querySelectorAll('input[type="date"], input[type="number"], input[type="text"], select');
                    inputs.forEach(input => {
                        // O input do assunto só deve ser habilitado se o checkbox estiver marcado
                        if (input.name.startsWith('assunto_')) {
                            input.disabled = !this.checked;
                        } else {
                            input.disabled = !this.checked;
                        }
                    });
                });
            });
        }

        // Nova lógica para o modal do assunto
        this.initAssuntoModal();
    },

    initAssuntoModal: function() {
        const assuntoCells = document.querySelectorAll('.assunto-cell');
        const assuntoModal = document.getElementById('assunto-modal');
        const assuntoModalContent = document.getElementById('assunto-modal-content');
        const assuntoModalBtnClose = document.getElementById('assunto-modal-btn-close');

        if (assuntoModal && assuntoModalContent && assuntoModalBtnClose) {
            assuntoCells.forEach(cell => {
                cell.addEventListener('click', function() {
                    const input = this.querySelector('input');
                    // Mostra o modal apenas se o campo estiver desabilitado (modo de visualização)
                    if (input && input.value && input.disabled) {
                        assuntoModalContent.textContent = input.value;
                        assuntoModal.classList.add('show-modal');
                    }
                });
            });

            // Função para fechar o modal
            const closeModal = () => assuntoModal.classList.remove('show-modal');

            assuntoModalBtnClose.addEventListener('click', closeModal);

            // Fecha o modal se clicar fora da área de conteúdo
            assuntoModal.addEventListener('click', function(event) {
                if (event.target === this) {
                    closeModal();
                }
            });
        }
    }
};