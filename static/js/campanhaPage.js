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

        // Atualiza a action do formulário para a URL correta
        editForm.action = `/campanhas/editar/${campaignId}`;

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

    // --- NOVA LÓGICA PARA O MODAL DE DELEÇÃO (Atualizada) ---
    const deleteModal = document.getElementById('delete-modal');
    if (deleteModal) {
        const deleteButtons = document.querySelectorAll('.btn-delete');
        const deleteForm = document.getElementById('delete-form');
        const deleteModalBtnCancel = document.getElementById('delete-modal-btn-cancel');
        const deleteModalBtnConfirm = document.getElementById('delete-modal-btn-confirm'); // Botão de confirmar
        const campaignNameSpan = document.getElementById('delete-modal-campaign-name');
        const deleteInput = document.getElementById('delete-modal-input'); // Input de texto

        let correctCampaignName = ''; // Variável para guardar o nome correto

        // Função para mostrar o modal de deleção
        const showDeleteModal = (e) => {
            const button = e.currentTarget;
            const campaignId = button.dataset.id;
            correctCampaignName = button.dataset.nome; // Armazena o nome

            // Atualiza a action do formulário do modal
            deleteForm.action = `/campanhas/deletar/${campaignId}`;

            // Preenche o nome da campanha no label de confirmação
            campaignNameSpan.textContent = correctCampaignName;

            // Limpa o input e desabilita o botão de confirmação
            deleteInput.value = '';
            deleteModalBtnConfirm.disabled = true;

            // Mostra o modal
            deleteModal.classList.add('show-modal');
        };

        // Função para esconder o modal de deleção
        const closeDeleteModal = () => {
            deleteModal.classList.remove('show-modal');
            correctCampaignName = ''; // Limpa o nome ao fechar
        };

        // Event listener para o input de texto
        deleteInput.addEventListener('input', () => {
            // Compara o valor do input com o nome armazenado
            if (deleteInput.value === correctCampaignName) {
                deleteModalBtnConfirm.disabled = false; // Habilita o botão
            } else {
                deleteModalBtnConfirm.disabled = true; // Desabilita o botão
            }
        });

        // Adiciona os eventos para todos os botões "Deletar"
        deleteButtons.forEach(button => {
            button.addEventListener('click', showDeleteModal);
        });

        // Adiciona evento para o botão "Cancelar" do modal
        deleteModalBtnCancel.addEventListener('click', closeDeleteModal);

        // Adiciona evento para fechar o modal clicando fora
        deleteModal.addEventListener('click', function(event) {
            if (event.target === this) {
                closeDeleteModal();
            }
        });
    }
    // --- FIM DA NOVA LÓGICA ---
});