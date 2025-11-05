// MUDANÇAS EM: drogamais/web-comercial/web-comercial-52b1f30afe463afa8ea727b0006a204b245c30d4/static/campanha/js/campanhasListPage.js

// Define a função de inicialização que o base.html espera
window.initCampanhasListPage = () => {
    const editModal = document.getElementById('edit-modal');
    // Se o modal não estiver nesta página, não faz nada
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
        // Remove listener antigo para evitar duplicação
        button.removeEventListener('click', showModal); 
        button.addEventListener('click', showModal);
    });

    modalBtnCancel.removeEventListener('click', closeModal);
    modalBtnCancel.addEventListener('click', closeModal);

    // Fecha o modal se clicar fora da área de conteúdo
    editModal.removeEventListener('click', closeModalOutside);
    editModal.addEventListener('click', closeModalOutside);
    
    function closeModalOutside(event) {
        if (event.target === this) {
            closeModal();
        }
    }

    // --- LÓGICA PARA O MODAL DE DELEÇÃO ---
    const deleteModal = document.getElementById('delete-modal');
    if (deleteModal) {
        const deleteButtons = document.querySelectorAll('.btn-delete');
        const deleteForm = document.getElementById('delete-form');
        const deleteModalBtnCancel = document.getElementById('delete-modal-btn-cancel');
        const deleteModalBtnConfirm = document.getElementById('delete-modal-btn-confirm'); 
        const campaignNameSpan = document.getElementById('delete-modal-campaign-name');
        const deleteInput = document.getElementById('delete-modal-input'); 
        const passwordInput = document.getElementById('delete-modal-password');

        let correctCampaignName = ''; 
        
        // ALTERAÇÃO: Esta função agora verifica APENAS o nome
        const checkConfirmationStatus = () => {
             const isNameMatch = deleteInput.value === correctCampaignName;
             // Habilita o botão APENAS se o nome bater
             deleteModalBtnConfirm.disabled = !isNameMatch;
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
            if (passwordInput) passwordInput.value = ''; 
            
            // Garante que o botão comece desabilitado
            deleteModalBtnConfirm.disabled = true;

            deleteModal.classList.add('show-modal');
        };

        const closeDeleteModal = () => {
            deleteModal.classList.remove('show-modal');
            correctCampaignName = ''; 
        };

        // ALTERAÇÃO: Listener apenas no input do NOME
        deleteInput.removeEventListener('input', checkConfirmationStatus);
        deleteInput.addEventListener('input', checkConfirmationStatus);
        
        // O listener de senha foi removido daqui

        deleteButtons.forEach(button => {
            button.removeEventListener('click', showDeleteModal);
            button.addEventListener('click', showDeleteModal);
        });

        deleteModalBtnCancel.removeEventListener('click', closeDeleteModal);
        deleteModalBtnCancel.addEventListener('click', closeDeleteModal);

        deleteModal.removeEventListener('click', closeDeleteModalOutside);
        deleteModal.addEventListener('click', closeDeleteModalOutside);
        
        function closeDeleteModalOutside(event) {
            if (event.target === this) {
                closeDeleteModal();
            }
        }
    }
};