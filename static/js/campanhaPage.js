// aplicacao_web_campanhas/static/js/campanhaPage.js

document.addEventListener('DOMContentLoaded', () => {
    const editModal = document.getElementById('edit-modal');
    if (!editModal) return;

    const modalBtnCancel = document.getElementById('modal-btn-cancel');
    const editButtons = document.querySelectorAll('.btn-edit');
    const editForm = document.getElementById('edit-form');
    const nomeInput = document.getElementById('nome_edit');
    const dataInicioInput = document.getElementById('data_inicio_edit');
    const dataFimInput = document.getElementById('data_fim_edit');

    // Função para mostrar o modal
    const showModal = (e) => {
        const button = e.currentTarget;
        const campaignId = button.dataset.id;
        const campaignName = button.dataset.nome;
        const campaignInicio = button.dataset.inicio;
        const campaignFim = button.dataset.fim;

        // CORRIGIDO: Adicionado prefixo /campanha
        editForm.action = `/campanha/editar/${campaignId}`;

        // Preenche os campos do formulário
        nomeInput.value = campaignName;
        dataInicioInput.value = campaignInicio;
        dataFimInput.value = campaignFim;

        // Mostra o modal
        editModal.classList.add('show-modal');
    };

    // Função para esconder o modal
    const closeModal = () => {
        editModal.classList.remove('show-modal');
    };

    // Adiciona os eventos
    editButtons.forEach(button => {
        button.addEventListener('click', showModal);
    });

    modalBtnCancel.addEventListener('click', closeModal);

    // Fecha o modal se clicar fora da área de conteúdo
    editModal.addEventListener('click', function(event) {
        if (event.target === this) {
            closeModal();
        }
    });

    // --- LÓGICA PARA O MODAL DE DELEÇÃO ---
    const deleteModal = document.getElementById('delete-modal');
    if (deleteModal) {
        const deleteButtons = document.querySelectorAll('.btn-delete');
        const deleteForm = document.getElementById('delete-form');
        const deleteModalBtnCancel = document.getElementById('delete-modal-btn-cancel');
        const deleteModalBtnConfirm = document.getElementById('delete-modal-btn-confirm'); 
        const campaignNameSpan = document.getElementById('delete-modal-campaign-name');
        const deleteInput = document.getElementById('delete-modal-input'); 

        let correctCampaignName = ''; 

        // Função para mostrar o modal de deleção
        const showDeleteModal = (e) => {
            const button = e.currentTarget;
            const campaignId = button.dataset.id;
            correctCampaignName = button.dataset.nome; 

            // CORRIGIDO: Adicionado prefixo /campanha
            deleteForm.action = `/campanha/deletar/${campaignId}`;

            campaignNameSpan.textContent = correctCampaignName;

            deleteInput.value = '';
            deleteModalBtnConfirm.disabled = true;

            deleteModal.classList.add('show-modal');
        };

        const closeDeleteModal = () => {
            deleteModal.classList.remove('show-modal');
            correctCampaignName = ''; 
        };

        deleteInput.addEventListener('input', () => {
            if (deleteInput.value === correctCampaignName) {
                deleteModalBtnConfirm.disabled = false; 
            } else {
                deleteModalBtnConfirm.disabled = true; 
            }
        });

        deleteButtons.forEach(button => {
            button.addEventListener('click', showDeleteModal);
        });

        deleteModalBtnCancel.addEventListener('click', closeDeleteModal);

        deleteModal.addEventListener('click', function(event) {
            if (event.target === this) {
                closeDeleteModal();
            }
        });
    }
});

/**
 * Valida um único campo de código de barras e aplica/remove a classe de erro na linha.
 * @param {HTMLElement} input - O elemento input do código de barras.
 */
function validarLinhaProduto(input) {
    const valor = input.value.trim(); // Pega o valor sem espaços
    const row = input.closest('tr');  // Encontra a linha (<tr>) pai
    
    if (!row) return; // Segurança: sai se não encontrar a linha

    // Se o campo estiver vazio, não marca como erro (opcional)
    if (valor === "") {
        row.classList.remove('row-error');
        return;
    }

    // REGRA DE VALIDAÇÃO:
    // O valor deve começar com '7', '8', '12', ou '13'
    const eValido = valor.startsWith('7') || 
                  valor.startsWith('8') || 
                  valor.startsWith('12') || 
                  valor.startsWith('13');

    // Aplica ou remove a classe de erro
    if (eValido) {
        row.classList.remove('row-error');
    } else {
        row.classList.add('row-error');
    }
}

/**
 * Valida todos os códigos de barras na tabela.
 */
function validarTodosCodigos() {
    const todosBarcodes = document.querySelectorAll('.barcode-input');
    todosBarcodes.forEach(input => {
        validarLinhaProduto(input);
    });
}

// --- Lógica Principal ---

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Lógica para habilitar/desabilitar edição ao clicar no checkbox
    //    (Baseado no seu 'produtosPage.js')
    const checkboxes = document.querySelectorAll('.edit-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('click', function() {
            const row = this.closest('tr');
            const inputs = row.querySelectorAll('input[type="text"], input[type="number"]');
            
            inputs.forEach(input => {
                if (this.checked) {
                    input.removeAttribute('disabled');
                } else {
                    input.setAttribute('disabled', 'disabled');
                }
            });
        });
    });

    // 2. Validação inicial de todos os códigos ao carregar a página
    validarTodosCodigos();

    // 3. Adiciona validação "ao vivo" (quando o usuário digita)
    //    Usamos "event delegation" para performance.
    const tableBody = document.querySelector('table tbody');
    if (tableBody) {
        tableBody.addEventListener('input', function(event) {
            // Verifica se o evento ocorreu em um campo de código de barras
            if (event.target.classList.contains('barcode-input')) {
                validarLinhaProduto(event.target);
            }
        });
    }
});