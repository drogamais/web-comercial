// static/js/indexPage.js

// Define a função de inicialização que o base.html espera
window.initIndexPage = () => {
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    // Se não houver botões (não está na index), não faz nada
    if (modalTriggers.length === 0) return;

    const modalOverlays = document.querySelectorAll('.modal-overlay');
    const modalCloseButtons = document.querySelectorAll('.modal-overlay .modal-button-cancel');

    // Função para abrir o modal
    const openModal = (e) => {
        e.preventDefault(); // Impede que o <a> suba a página
        const modalId = e.currentTarget.dataset.modalTarget; // Pega o ID (ex: "#campanha-modal")
        const targetModal = document.querySelector(modalId);
        if (targetModal) {
            targetModal.classList.add('show-modal');
        } else {
            console.error(`Modal with ID ${modalId} not found.`);
        }
    };

    // Função para fechar o modal
    const closeModal = (e) => {
        const modal = e.currentTarget.closest('.modal-overlay');
        if (modal) {
            modal.classList.remove('show-modal');
        }
    };

    // Função para fechar clicando fora
    const closeModalOutside = (event) => {
        // Se o clique foi diretamente no overlay (fundo escuro)
        if (event.target === event.currentTarget) {
            event.currentTarget.classList.remove('show-modal');
        }
    };

    // Abrir Modais (por clique)
    modalTriggers.forEach(button => {
        button.removeEventListener('click', openModal); // Evita duplicatas
        button.addEventListener('click', openModal);
    });

    // Fechar Modais pelo botão "Fechar"
    modalCloseButtons.forEach(button => {
        button.removeEventListener('click', closeModal); // Evita duplicatas
        button.addEventListener('click', closeModal);
    });

    // Fechar Modais clicando fora do conteúdo
    modalOverlays.forEach(overlay => {
        overlay.removeEventListener('click', closeModalOutside); // Evita duplicatas
        overlay.addEventListener('click', closeModalOutside);
    });

    const expiringModal = document.getElementById('expiring-partner-modal');
    if (expiringModal && !expiringModal.classList.contains('show-modal')) {
        // Atraso leve para garantir que a transição de CSS funcione
        setTimeout(() => {
            expiringModal.classList.add('show-modal');
        }, 100); 
    }
};