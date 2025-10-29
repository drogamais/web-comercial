// static/js/parceirosPage.js

document.addEventListener('DOMContentLoaded', () => {
    // --- LÓGICA MODAL EDIÇÃO ---
    const editModal = document.getElementById('edit-modal');
    if (editModal) {
        const modalBtnCancel = document.getElementById('modal-btn-cancel');
        const editButtons = document.querySelectorAll('.btn-edit');
        const editForm = document.getElementById('edit-form');
        
        // Mapeia todos os inputs do modal de edição
        const inputs = {
            nomeAjustado: document.getElementById('nome_ajustado_edit'),
            cnpj: document.getElementById('cnpj_edit'),
            nomeFantasia: document.getElementById('nome_fantasia_edit'),
            razaoSocial: document.getElementById('razao_social_edit'),
            tipo: document.getElementById('tipo_edit'),
            email: document.getElementById('email_edit'),
            telefone: document.getElementById('telefone_edit'),
            dataEntrada: document.getElementById('data_entrada_edit'),
            dataSaida: document.getElementById('data_saida_edit'),
            status: document.getElementById('status_edit')
        };

        const showEditModal = (e) => {
            const button = e.currentTarget;
            const data = button.dataset; // Pega todos os atributos data-*
            const parceiroId = data.id;

            editForm.action = `/parceiro/editar/${parceiroId}`; // Rota de parceiro

            // Preenche todos os campos do formulário do modal
            inputs.nomeAjustado.value = data.nomeAjustado || '';
            inputs.cnpj.value = data.cnpj || '';
            inputs.nomeFantasia.value = data.nomeFantasia || '';
            inputs.razaoSocial.value = data.razaoSocial || '';
            inputs.tipo.value = data.tipo || '';
            inputs.email.value = data.email || '';
            inputs.telefone.value = data.telefone || '';
            inputs.dataEntrada.value = data.dataEntrada || '';
            inputs.dataSaida.value = data.dataSaida || '';
            inputs.status.value = data.status || 'ativo'; // 'ativo' como padrão

            editModal.classList.add('show-modal');
        };

        const closeEditModal = () => {
            editModal.classList.remove('show-modal');
        };

        editButtons.forEach(button => button.addEventListener('click', showEditModal));
        modalBtnCancel.addEventListener('click', closeEditModal);
        editModal.addEventListener('click', (event) => {
            // Fecha só se clicar no overlay (fundo)
            if (event.target === editModal) closeEditModal();
        });
    }

    // --- LÓGICA MODAL DELEÇÃO ( permanece a mesma) ---
    const deleteModal = document.getElementById('delete-modal');
    if (deleteModal) {
        const deleteButtons = document.querySelectorAll('.btn-delete');
        const deleteForm = document.getElementById('delete-form');
        const deleteModalBtnCancel = document.getElementById('delete-modal-btn-cancel');
        const deleteModalBtnConfirm = document.getElementById('delete-modal-btn-confirm');
        const parceiroNameSpan = document.getElementById('delete-modal-parceiro-name'); // ID atualizado
        const deleteInput = document.getElementById('delete-modal-input');

        let correctParceiroName = '';

        const showDeleteModal = (e) => {
            const button = e.currentTarget;
            const parceiroId = button.dataset.id;
            // 'data-nome' agora contém o 'nome_ajustado' (definido no HTML)
            correctParceiroName = button.dataset.nome; 

            deleteForm.action = `/parceiro/deletar/${parceiroId}`; // Rota de parceiro
            parceiroNameSpan.textContent = correctParceiroName;
            deleteInput.value = '';
            deleteModalBtnConfirm.disabled = true;
            deleteModal.classList.add('show-modal');
        };

        const closeDeleteModal = () => {
            deleteModal.classList.remove('show-modal');
            correctParceiroName = '';
        };

        deleteInput.addEventListener('input', () => {
            deleteModalBtnConfirm.disabled = deleteInput.value !== correctParceiroName;
        });

        deleteButtons.forEach(button => button.addEventListener('click', showDeleteModal));
        deleteModalBtnCancel.addEventListener('click', closeDeleteModal);
        deleteModal.addEventListener('click', (event) => {
            if (event.target === deleteModal) closeDeleteModal();
        });
    }
});