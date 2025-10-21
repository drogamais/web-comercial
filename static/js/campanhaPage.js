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
    const len = valor.length;
    const eValido = (len === 7) || (len === 8) || (len === 12) || (len === 13);

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

    // 4. LÓGICA DO NOVO BOTÃO DE VALIDAÇÃO (dbDrogamais)
    const validateGtinBtn = document.getElementById('btn-validar-gtins');
    const formEditDelete = document.getElementById('form-edit-delete');
    
    if (validateGtinBtn && formEditDelete) {
        
        // Pega o ID da campanha pela URL do botão 'Salvar'
        const saveButton = formEditDelete.querySelector('button[formaction*="atualizar"]');
        let campanhaId = null;
        if (saveButton) {
            try {
                // Tenta extrair o ID da URL (ex: /campanha/123/produtos/atualizar)
                const match = saveButton.formAction.match(/\/campanha\/(\d+)\/produtos/);
                if (match) {
                    campanhaId = match[1];
                }
            } catch (e) {
                console.error("Não foi possível extrair o ID da campanha da URL do formulário.", e);
            }
        }

        if (!campanhaId) {
            console.error("Botão de validação não conseguiu encontrar o ID da campanha.");
            validateGtinBtn.disabled = true;
            validateGtinBtn.textContent = "Erro: ID da Campanha não encontrado";
        }

        validateGtinBtn.addEventListener('click', async () => {
            if (!campanhaId) return;
            
            const originalText = validateGtinBtn.textContent;
            validateGtinBtn.textContent = 'Validando...';
            validateGtinBtn.disabled = true;

            const allBarcodeInputs = document.querySelectorAll('.barcode-input');
            const allRows = document.querySelectorAll('table tbody tr');
            const gtins = Array.from(allBarcodeInputs).map(input => input.value);

            try {
                const response = await fetch(`/campanha/${campanhaId}/produtos/validar_gtins`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ gtins: gtins })
                });

                if (!response.ok) {
                    throw new Error(`Erro do servidor: ${response.statusText}`);
                }

                const result = await response.json();
                
                // Cria um Set (lista rápida) de GTINs válidos
                const validGtinSet = new Set(result.valid_gtins);

                // Aplica os estilos
                allBarcodeInputs.forEach(input => {
                    const gtin = input.value.trim();
                    const row = input.closest('tr');
                    
                    // Limpa estilos antigos de validação
                    row.classList.remove('row-valid', 'row-invalid');

                    if (gtin === "") {
                        // Se estiver vazio, não faz nada
                        return;
                    }
                    
                    // Aplica o estilo (Válido ou Inválido)
                    if (validGtinSet.has(gtin)) {
                        row.classList.add('row-valid');
                    } else {
                        row.classList.add('row-invalid');
                    }
                });

            } catch (error) {
                console.error("Falha ao validar GTINs:", error);
                alert("Ocorreu um erro ao validar os GTINs. Verifique o console.");
            } finally {
                // Restaura o botão
                validateGtinBtn.textContent = originalText;
                validateGtinBtn.disabled = false;
            }
        });
    }

});