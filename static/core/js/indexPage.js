// static/js/indexPage.js

document.addEventListener('DOMContentLoaded', () => {
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    const modalOverlays = document.querySelectorAll('.modal-overlay');
    const modalCloseButtons = document.querySelectorAll('.modal-overlay .modal-button-cancel');

    // Abrir Modais (por clique)
    modalTriggers.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault(); // Impede que o <a> suba a página
            const modalId = button.dataset.modalTarget; // Pega o ID (ex: "#campanha-modal")
            const targetModal = document.querySelector(modalId);
            if (targetModal) {
                targetModal.classList.add('show-modal');
            } else {
                console.error(`Modal with ID ${modalId} not found.`);
            }
        });
    });

    // Fechar Modais pelo botão "Fechar"
    modalCloseButtons.forEach(button => {
        button.addEventListener('click', () => {
            const modal = button.closest('.modal-overlay');
            if (modal) {
                modal.classList.remove('show-modal');
            }
        });
    });

    // Fechar Modais clicando fora do conteúdo
    modalOverlays.forEach(overlay => {
        overlay.addEventListener('click', (event) => {
            // Se o clique foi diretamente no overlay (fundo escuro)
            if (event.target === overlay) {
                overlay.classList.remove('show-modal');
            }
        });
    });

    const expiringModal = document.getElementById('expiring-partner-modal');
    if (expiringModal) {
        // Atraso leve para garantir que a transição de CSS funcione
        setTimeout(() => {
            expiringModal.classList.add('show-modal');
        }, 100); 
    }
});