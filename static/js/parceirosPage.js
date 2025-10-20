// static/js/parceirosPage.js

document.addEventListener('DOMContentLoaded', () => {
    // --- LÓGICA MODAL EDIÇÃO ---
    const editModal = document.getElementById('edit-modal');
    if (editModal) {
        const modalBtnCancel = document.getElementById('modal-btn-cancel');
        const editButtons = document.querySelectorAll('.btn-edit');
        const editForm = document.getElementById('edit-form');
        const nomeInput = document.getElementById('nome_edit');

        const showEditModal = (e) => {
            const button = e.currentTarget;
            const parceiroId = button.dataset.id;
            const parceiroName = button.dataset.nome;

            editForm.action = `/parceiro/editar/${parceiroId}`; // Rota de parceiro
            nomeInput.value = parceiroName;
            editModal.classList.add('show-modal');
        };

        const closeEditModal = () => {
            editModal.classList.remove('show-modal');
        };

        editButtons.forEach(button => button.addEventListener('click', showEditModal));
        modalBtnCancel.addEventListener('click', closeEditModal);
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
        const parceiroNameSpan = document.getElementById('delete-modal-parceiro-name'); // ID atualizado
        const deleteInput = document.getElementById('delete-modal-input');

        let correctParceiroName = '';

        const showDeleteModal = (e) => {
            const button = e.currentTarget;
            const parceiroId = button.dataset.id;
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