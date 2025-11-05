// aplicacao_web_campanhas/static/js/tabloidePage.js

// Define a função de inicialização que o base.html espera
window.initTabloideListPage = () => {
    const editModal = document.getElementById('edit-modal');
    // Se não houver modal nesta página, não faz nada
    if (!editModal) return;

    const modalBtnCancel = document.getElementById('modal-btn-cancel');
    const editButtons = document.querySelectorAll('.btn-edit');
    const editForm = document.getElementById('edit-form');
    const nomeInput = document.getElementById('nome_edit');
    const dataInicioInput = document.getElementById('data_inicio_edit');
    const dataFimInput = document.getElementById('data_fim_edit');

    // ... (código do modal de edição permanece o mesmo) ...
    // Função para mostrar o modal
    const showModal = (e) => {
        const button = e.currentTarget;
        const campaignId = button.dataset.id;
        const campaignName = button.dataset.nome;
        const campaignInicio = button.dataset.inicio;
        const campaignFim = button.dataset.fim;

        // Modificado: aponta para a rota de tabloide
        editForm.action = `/tabloide/editar/${campaignId}`;

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
        button.removeEventListener('click', showModal); // Evita duplicatas
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

            // Modificado: aponta para a rota de tabloide
            deleteForm.action = `/tabloide/deletar/${campaignId}`;

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
        
        // (Listeners de fechar o modal permanecem os mesmos)
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