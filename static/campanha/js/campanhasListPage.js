// MUDANÇAS EM: drogamais/web-comercial/web-comercial-52b1f30afe463afa8ea727b0006a204b245c30d4/static/campanha/js/campanhasListPage.js

document.addEventListener('DOMContentLoaded', () => {
    const editModal = document.getElementById('edit-modal');
    if (!editModal) return;

    const modalBtnCancel = document.getElementById('modal-btn-cancel');
    const editButtons = document.querySelectorAll('.btn-edit');
    const editForm = document.getElementById('edit-form');
    const nomeInput = document.getElementById('nome_edit');
    const dataInicioInput = document.getElementById('data_inicio_edit');
    const dataFimInput = document.getElementById('data_fim_edit');
    const parceiroIdInput = document.getElementById('parceiro_id_edit'); // <-- ADICIONADO

    // Função para mostrar o modal
    const showModal = (e) => {
        const button = e.currentTarget;
        const campaignId = button.dataset.id;
        const campaignName = button.dataset.nome;
        const campaignInicio = button.dataset.inicio;
        const campaignFim = button.dataset.fim;
        const campaignParceiroId = button.dataset.parceiroId; // <-- ADICIONADO

        // CORRIGIDO: Adicionado prefixo /campanha
        editForm.action = `/campanha/editar/${campaignId}`;

        // Preenche os campos do formulário
        nomeInput.value = campaignName;
        dataInicioInput.value = campaignInicio;
        dataFimInput.value = campaignFim;
        parceiroIdInput.value = campaignParceiroId || ''; // <-- ADICIONADO

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
        // ADICIONADO: Pega o input de senha
        const passwordInput = document.getElementById('delete-modal-password');
        const REQUIRED_PASSWORD = '123'; // Senha hardcoded para validação no front-end

        let correctCampaignName = ''; 
        
        // NOVO: Função para verificar se a confirmação de nome e senha estão corretas
        const checkConfirmationStatus = () => {
             const isNameMatch = deleteInput.value === correctCampaignName;
             // Verifica se o elemento existe antes de tentar ler o valor
             const isPasswordMatch = passwordInput && passwordInput.value === REQUIRED_PASSWORD;
             deleteModalBtnConfirm.disabled = !(isNameMatch && isPasswordMatch);
        };
        
        // Função para mostrar o modal de deleção
        const showDeleteModal = (e) => {
            const button = e.currentTarget;
            const campaignId = button.dataset.id;
            correctCampaignName = button.dataset.nome; 

            // CORRIGIDO: Adicionado prefixo /campanha
            deleteForm.action = `/campanha/deletar/${campaignId}`;

            campaignNameSpan.textContent = correctCampaignName;

            deleteInput.value = '';
            // ADICIONADO: Limpa a senha ao abrir
            if (passwordInput) passwordInput.value = ''; 
            deleteModalBtnConfirm.disabled = true;

            deleteModal.classList.add('show-modal');
        };

        const closeDeleteModal = () => {
            deleteModal.classList.remove('show-modal');
            correctCampaignName = ''; 
        };

        // ALTERADO: Troca o listener antigo pelos novos
        deleteInput.addEventListener('input', checkConfirmationStatus);
        // ADICIONADO: Listener para o campo de senha
        if (passwordInput) passwordInput.addEventListener('input', checkConfirmationStatus);

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