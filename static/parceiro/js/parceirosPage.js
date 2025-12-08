// MUDANÇAS EM: drogamais/web-comercial/web-comercial-52b1f30afe463afa8ea727b0006a204b245c30d4/static/parceiro/js/parceirosPage.js

document.addEventListener('DOMContentLoaded', () => {

    // --- LÓGICA MODAL DE CRIAÇÃO (NOVO) ---
    const createConfirmModal = document.getElementById('create-confirm-modal');
    const showCreateModalBtn = document.getElementById('btn-show-create-modal');
    const createForm = document.getElementById('create-parceiro-form');
    
    if (createConfirmModal && showCreateModalBtn && createForm) {
        const createModalBtnCancel = document.getElementById('create-modal-btn-cancel');
        const createModalBtnConfirm = document.getElementById('create-modal-btn-confirm');
        const createModalEmailSpan = document.getElementById('create-modal-email');
        const emailGestorInput = document.getElementById('email_gestor'); // Input do formulário principal
        const nomeFantasiaInput = document.getElementById('nome_fantasia'); // Outro campo obrigatório

        // Função para mostrar o modal
        const showCreateModal = (e) => {
            e.preventDefault();
            
            const email = emailGestorInput.value.trim();
            const nome = nomeFantasiaInput.value.trim();

            // Validação simples de frontend
            if (!email || !nome) {
                alert('Por favor, preencha todo os campo com *');
                return;
            }

            // Preenche os dados no modal
            createModalEmailSpan.textContent = email;
            // createModalPassword.value = ''; // REMOVIDO
            createModalBtnConfirm.disabled = false; // Botão começa HABILITADO
            
            createConfirmModal.classList.add('show-modal');
        };

        // Função para fechar o modal
        const closeCreateModal = () => {
            createConfirmModal.classList.remove('show-modal');
            // createModalPassword.value = ''; // REMOVIDO
        };
        
        // Função para submeter o formulário
        const handleConfirmCreation = (e) => {
            e.preventDefault();

            // Submete o formulário principal
            createForm.submit();
        };

        // Listeners
        showCreateModalBtn.addEventListener('click', showCreateModal);
        createModalBtnCancel.addEventListener('click', closeCreateModal);
        createConfirmModal.querySelector('.close-button').addEventListener('click', closeCreateModal);
        // Listener de input da senha REMOVIDO
        // createModalPassword.addEventListener('input', checkCreatePassword);
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

            inputs.nomeAjustado.value = data.nomeAjustado || ''; 
            inputs.cnpj.value = data.cnpj || '';
            inputs.nomeFantasia.value = data.nomeFantasia || '';
            inputs.razaoSocial.value = data.razaoSocial || '';
            inputs.tipo.value = data.tipo || '';
            inputs.dataEntrada.value = data.dataEntrada || '';
            inputs.dataSaida.value = data.dataSaida || '';
            inputs.gestor.value = data.gestor || ''; 
            inputs.telefoneGestor.value = data.telefoneGestor || ''; 
            inputs.emailGestor.value = data.emailGestor || '';

            // Lógica visual
            if (temContrato) {
                inputs.contratoLabel.textContent = "Arquivo Anexado (envie outro para substituir)";
                inputs.contratoLabel.style.color = "#27ae60"; // Verde
                
                // MOSTRA a opção de remover
                if(inputs.removerContratoDiv) inputs.removerContratoDiv.style.display = 'flex';
            } else {
                inputs.contratoLabel.textContent = "Nenhum arquivo anexado";
                inputs.contratoLabel.style.color = "#555";
                
                // ESCONDE a opção de remover
                if(inputs.removerContratoDiv) inputs.removerContratoDiv.style.display = 'none';
            }

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

    // --- LÓGICA MODAL DELEÇÃO (Implementação de Senha) ---
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
            passwordInput.value = '';
            
            deleteModalBtnConfirm.disabled = true;
            deleteModal.classList.add('show-modal');
        };

        const closeDeleteModal = () => {
            deleteModal.classList.remove('show-modal');
            correctParceiroName = '';
        };

        nameInput.addEventListener('input', checkConfirmationStatus);
        
        deleteButtons.forEach(button => button.addEventListener('click', showDeleteModal));
        deleteModalBtnCancel.addEventListener('click', closeDeleteModal);
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
        senhaModalBtnClose.addEventListener('click', closeSenhaModal);
        senhaModalBtnCancel.addEventListener('click', closeSenhaModal);
        
        senhaModal.addEventListener('click', (event) => {
            if (event.target === senhaModal) closeSenhaModal();
        });
    }
});