document.addEventListener('DOMContentLoaded', () => {

    // --- FUNÇÃO AUXILIAR DE VALIDAÇÃO ---
    // Verifica se o valor do input existe dentro das opções do datalist
    const isValueInDatalist = (inputValue, datalistId) => {
        const datalist = document.getElementById(datalistId);
        if (!datalist) return true; // Se não achar lista (fallback), deixa passar
        
        const options = Array.from(datalist.options).map(opt => opt.value);
        return options.includes(inputValue);
    };

    // --- LÓGICA MODAL DE CRIAÇÃO ---
    const createConfirmModal = document.getElementById('create-confirm-modal');
    const showCreateModalBtn = document.getElementById('btn-show-create-modal');
    const createForm = document.getElementById('create-parceiro-form');
    
    if (createConfirmModal && showCreateModalBtn && createForm) {
        const createModalBtnCancel = document.getElementById('create-modal-btn-cancel');
        const createModalBtnConfirm = document.getElementById('create-modal-btn-confirm');
        const createModalEmailSpan = document.getElementById('create-modal-email');
        const emailGestorInput = document.getElementById('email_gestor'); 
        const nomeFantasiaInput = document.getElementById('nome_fantasia');
        const nomeAjustadoInput = document.getElementById('nome_ajustado'); // Input do nome ajustado

        // Função para mostrar o modal
        const showCreateModal = (e) => {
            e.preventDefault();
            
            const email = emailGestorInput.value.trim();
            const nome = nomeFantasiaInput.value.trim();
            const nomeAjustado = nomeAjustadoInput ? nomeAjustadoInput.value.trim() : '';

            // 1. Validação de campos vazios
            if (!email || !nome || !nomeAjustado) {
                alert('Por favor, preencha todos os campos obrigatórios (*).');
                return;
            }

            // 2. Validação do Datalist (Nome Ajustado)
            // Certifique-se de que o ID do datalist no HTML é 'datalist_nomes'
            if (!isValueInDatalist(nomeAjustado, 'datalist_nomes')) { 
                alert('O "Nome Ajustado" digitado não é válido. Selecione uma opção exata da lista.');
                return; // Impede a abertura do modal
            }

            // Preenche os dados no modal
            createModalEmailSpan.textContent = email;
            createModalBtnConfirm.disabled = false;
            
            createConfirmModal.classList.add('show-modal');
        };

        // Função para fechar o modal
        const closeCreateModal = () => {
            createConfirmModal.classList.remove('show-modal');
        };
        
        // Função para submeter o formulário
        const handleConfirmCreation = (e) => {
            e.preventDefault();
            createForm.submit();
        };

        // Listeners
        showCreateModalBtn.addEventListener('click', showCreateModal);
        createModalBtnCancel.addEventListener('click', closeCreateModal);
        
        const closeBtn = createConfirmModal.querySelector('.close-button');
        if (closeBtn) closeBtn.addEventListener('click', closeCreateModal);

        createModalBtnConfirm.addEventListener('click', handleConfirmCreation);
        
        createConfirmModal.addEventListener('click', (event) => {
            if (event.target === createConfirmModal) closeCreateModal();
        });
    }

    // --- LÓGICA MODAL EDIÇÃO ---
    const editModal = document.getElementById('edit-modal');
    if (editModal) {
        const modalBtnCancel = document.getElementById('modal-btn-cancel');
        const editButtons = document.querySelectorAll('.btn-edit');
        const editForm = document.getElementById('edit-form');
        
        // 1. Validação no envio do formulário de edição
        if (editForm) {
            editForm.addEventListener('submit', (e) => {
                const nomeAjustadoEditInput = document.getElementById('nome_ajustado_edit');
                if (nomeAjustadoEditInput) {
                    const nomeAjustadoEdit = nomeAjustadoEditInput.value.trim();
                    
                    if (!isValueInDatalist(nomeAjustadoEdit, 'datalist_nomes')) {
                        e.preventDefault(); // Cancela o envio
                        alert('O "Nome Ajustado" digitado na edição não é válido. Selecione uma opção exata da lista.');
                    }
                }
            });
        }

        const inputs = {
            nomeAjustado: document.getElementById('nome_ajustado_edit'),
            cnpj: document.getElementById('cnpj_edit'),
            nomeFantasia: document.getElementById('nome_fantasia_edit'),
            razaoSocial: document.getElementById('razao_social_edit'),
            tipo: document.getElementById('tipo_edit'),
            gestor: document.getElementById('gestor_edit'), 
            emailGestor: document.getElementById('email_gestor_edit'), 
            telefoneGestor: document.getElementById('telefone_gestor_edit'), 
            dataEntrada: document.getElementById('data_entrada_edit'),
            dataSaida: document.getElementById('data_saida_edit'),
            contratoLabel: document.getElementById('contrato_atual_nome'),
            removerContratoDiv: document.getElementById('container-remover-contrato'),
            removerContratoCheck: document.getElementById('remover_contrato')
        };

        const showEditModal = (e) => {
            const button = e.currentTarget;
            const temContrato = button.dataset.contratoArquivo && button.dataset.contratoArquivo !== 'None';
            const data = button.dataset;
            const parceiroId = data.id;

            const fileInput = document.getElementById('contrato_arquivo_edit');
            if(fileInput) fileInput.value = '';

            if (inputs.removerContratoCheck) inputs.removerContratoCheck.checked = false;

            editForm.action = `/parceiro/editar/${parceiroId}`; 

            if (inputs.nomeAjustado) inputs.nomeAjustado.value = data.nomeAjustado || ''; 
            if (inputs.cnpj) inputs.cnpj.value = data.cnpj || '';
            if (inputs.nomeFantasia) inputs.nomeFantasia.value = data.nomeFantasia || '';
            if (inputs.razaoSocial) inputs.razaoSocial.value = data.razaoSocial || '';
            if (inputs.tipo) inputs.tipo.value = data.tipo || '';
            if (inputs.dataEntrada) inputs.dataEntrada.value = data.dataEntrada || '';
            if (inputs.dataSaida) inputs.dataSaida.value = data.dataSaida || '';
            if (inputs.gestor) inputs.gestor.value = data.gestor || ''; 
            if (inputs.telefoneGestor) inputs.telefoneGestor.value = data.telefoneGestor || ''; 
            if (inputs.emailGestor) inputs.emailGestor.value = data.emailGestor || '';

            // Lógica visual do contrato
            if (inputs.contratoLabel) {
                if (temContrato) {
                    inputs.contratoLabel.textContent = "Arquivo Anexado (envie outro para substituir)";
                    inputs.contratoLabel.style.color = "#27ae60"; // Verde
                    if(inputs.removerContratoDiv) inputs.removerContratoDiv.style.display = 'flex';
                } else {
                    inputs.contratoLabel.textContent = "Nenhum arquivo anexado";
                    inputs.contratoLabel.style.color = "#555";
                    if(inputs.removerContratoDiv) inputs.removerContratoDiv.style.display = 'none';
                }
            }

            editModal.classList.add('show-modal');
        };

        const closeEditModal = () => {
            editModal.classList.remove('show-modal');
        };

        editButtons.forEach(button => button.addEventListener('click', showEditModal));
        if (modalBtnCancel) modalBtnCancel.addEventListener('click', closeEditModal);
        
        editModal.addEventListener('click', (event) => {
            if (event.target === editModal) closeEditModal();
        });
    }

    // --- LÓGICA MODAL DELEÇÃO ---
    const deleteModal = document.getElementById('delete-modal');
    if (deleteModal) {
        const deleteButtons = document.querySelectorAll('.btn-delete');
        const deleteForm = document.getElementById('delete-form');
        const deleteModalBtnCancel = document.getElementById('delete-modal-btn-cancel');
        const deleteModalBtnConfirm = document.getElementById('delete-modal-btn-confirm');
        const parceiroNameSpan = document.getElementById('delete-modal-parceiro-name'); 
        const nameInput = document.getElementById('delete-modal-input');
        const passwordInput = document.getElementById('delete-modal-password'); 

        let correctParceiroName = '';
        
        const checkConfirmationStatus = () => {
             const isNameMatch = nameInput.value === correctParceiroName;
             deleteModalBtnConfirm.disabled = !isNameMatch;
        };

        const showDeleteModal = (e) => {
            const button = e.currentTarget;
            const parceiroId = button.dataset.id;
            correctParceiroName = button.dataset.nomeAjustado; 

            deleteForm.action = `/parceiro/deletar/${parceiroId}`; 
            parceiroNameSpan.textContent = correctParceiroName;
            
            nameInput.value = '';
            if (passwordInput) passwordInput.value = '';
            
            deleteModalBtnConfirm.disabled = true;
            deleteModal.classList.add('show-modal');
        };

        const closeDeleteModal = () => {
            deleteModal.classList.remove('show-modal');
            correctParceiroName = '';
        };

        nameInput.addEventListener('input', checkConfirmationStatus);
        
        deleteButtons.forEach(button => button.addEventListener('click', showDeleteModal));
        if (deleteModalBtnCancel) deleteModalBtnCancel.addEventListener('click', closeDeleteModal);
        
        deleteModal.addEventListener('click', (event) => {
            if (event.target === deleteModal) closeDeleteModal();
        });
    }

    // --- LÓGICA MODAL DEFINIR SENHA ---
    const senhaModal = document.getElementById('senha-modal');
    if (senhaModal) {
        const senhaButtons = document.querySelectorAll('.btn-senha');
        const senhaForm = document.getElementById('senha-form');
        const senhaModalEmail = document.getElementById('senha-modal-email');
        const senhaModalBtnClose = document.getElementById('senha-modal-btn-close');
        const senhaModalBtnCancel = document.getElementById('senha-modal-btn-cancel');
        const novaSenhaInput = document.getElementById('nova_senha');
        const confirmarSenhaInput = document.getElementById('confirmar_senha');

        const showSenhaModal = (e) => {
            const button = e.currentTarget;
            const parceiroId = button.dataset.id;
            const email = button.dataset.email;

            senhaForm.action = `/parceiro/definir-senha/${parceiroId}`;
            
            senhaModalEmail.textContent = email || 'Email não encontrado';
            novaSenhaInput.value = '';
            confirmarSenhaInput.value = '';

            senhaModal.classList.add('show-modal');
        };

        const closeSenhaModal = () => {
            senhaModal.classList.remove('show-modal');
            senhaForm.action = '';
            novaSenhaInput.value = '';
            confirmarSenhaInput.value = '';
        };

        senhaButtons.forEach(button => button.addEventListener('click', showSenhaModal));
        if (senhaModalBtnClose) senhaModalBtnClose.addEventListener('click', closeSenhaModal);
        if (senhaModalBtnCancel) senhaModalBtnCancel.addEventListener('click', closeSenhaModal);
        
        senhaModal.addEventListener('click', (event) => {
            if (event.target === senhaModal) closeSenhaModal();
        });
    }
});