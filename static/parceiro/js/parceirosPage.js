// MUDANÇAS EM: drogamais/web-comercial/web-comercial-52b1f30afe463afa8ea727b0006a204b245c30d4/static/parceiro/js/parceirosPage.js

document.addEventListener('DOMContentLoaded', () => {
    // --- LÓGICA MODAL EDIÇÃO ---
    const editModal = document.getElementById('edit-modal');
    if (editModal) {
        // ... (código do modal de edição permanece o mesmo) ...
        const modalBtnCancel = document.getElementById('modal-btn-cancel');
        const editButtons = document.querySelectorAll('.btn-edit');
        const editForm = document.getElementById('edit-form');
        
        // Mapeia TODOS os inputs que existem no modal de edição
        const inputs = {
            // Campos presentes no esquema FINAL do banco de dados
            nomeAjustado: document.getElementById('nome_ajustado_edit'),
            cnpj: document.getElementById('cnpj_edit'),
            nomeFantasia: document.getElementById('nome_fantasia_edit'),
            razaoSocial: document.getElementById('razao_social_edit'),
            tipo: document.getElementById('tipo_edit'),
            gestor: document.getElementById('gestor_edit'), 
            emailGestor: document.getElementById('email_gestor_edit'), 
            telefoneGestor: document.getElementById('telefone_gestor_edit'), 
            dataEntrada: document.getElementById('data_entrada_edit'),
            dataSaida: document.getElementById('data_saida_edit')
        };

        const showEditModal = (e) => {
            const button = e.currentTarget;
            const data = button.dataset; // Pega todos os atributos data-*
            const parceiroId = data.id;

            editForm.action = `/parceiro/editar/${parceiroId}`; 

            // Preenche todos os campos do formulário do modal
            inputs.nomeAjustado.value = data.nomeAjustado || ''; 
            inputs.cnpj.value = data.cnpj || '';
            inputs.nomeFantasia.value = data.nomeFantasia || '';
            inputs.razaoSocial.value = data.razaoSocial || '';
            inputs.tipo.value = data.tipo || '';
            inputs.dataEntrada.value = data.dataEntrada || '';
            inputs.dataSaida.value = data.dataSaida || '';
            
            // Campos de contato
            inputs.gestor.value = data.gestor || ''; 
            inputs.telefoneGestor.value = data.telefoneGestor || ''; 
            inputs.emailGestor.value = data.emailGestor || ''; 

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

    // --- LÓGICA MODAL DELEÇÃO (Implementação de Senha) ---
    const deleteModal = document.getElementById('delete-modal');
    if (deleteModal) {
        const deleteButtons = document.querySelectorAll('.btn-delete');
        const deleteForm = document.getElementById('delete-form');
        const deleteModalBtnCancel = document.getElementById('delete-modal-btn-cancel');
        const deleteModalBtnConfirm = document.getElementById('delete-modal-btn-confirm');
        const parceiroNameSpan = document.getElementById('delete-modal-parceiro-name'); 
        const nameInput = document.getElementById('delete-modal-input');
        const passwordInput = document.getElementById('delete-modal-password'); // NOVO

        let correctParceiroName = '';
        
        // ALTERAÇÃO: Esta função agora verifica APENAS o nome
        const checkConfirmationStatus = () => {
             const isNameMatch = nameInput.value === correctParceiroName;
             // Habilita o botão APENAS se o nome bater
             deleteModalBtnConfirm.disabled = !isNameMatch;
        };

        const showDeleteModal = (e) => {
            const button = e.currentTarget;
            const parceiroId = button.dataset.id;
            correctParceiroName = button.dataset.nomeAjustado; 

            deleteForm.action = `/parceiro/deletar/${parceiroId}`; 
            parceiroNameSpan.textContent = correctParceiroName;
            
            // Limpa todos os campos ao abrir
            nameInput.value = '';
            passwordInput.value = '';
            
            // Garante que o botão comece desabilitado
            deleteModalBtnConfirm.disabled = true;
            deleteModal.classList.add('show-modal');
        };

        const closeDeleteModal = () => {
            deleteModal.classList.remove('show-modal');
            correctParceiroName = '';
        };

        // ALTERAÇÃO: Listener apenas no input do NOME
        nameInput.addEventListener('input', checkConfirmationStatus);
        
        // O listener de senha foi removido daqui

        deleteButtons.forEach(button => button.addEventListener('click', showDeleteModal));
        deleteModalBtnCancel.addEventListener('click', closeDeleteModal);
        deleteModal.addEventListener('click', (event) => {
            if (event.target === deleteModal) closeDeleteModal();
        });
    }
});