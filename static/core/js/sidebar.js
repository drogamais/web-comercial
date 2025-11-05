// Define a função de inicialização que o base.html espera
window.initSidebar = () => {
    const dropdownToggles = document.querySelectorAll('.sidebar-dropdown-toggle');
    // Se não houver sidebar (?), não faz nada
    if (dropdownToggles.length === 0) return;
    
    // Função para o clique no dropdown
    const toggleDropdown = (e) => {
        const toggle = e.currentTarget;
        // Alterna a classe 'active' no botão
        toggle.classList.toggle('active');
        
        // Pega o próximo elemento (que é o .sidebar-submenu)
        const submenu = toggle.nextElementSibling;
        
        // Alterna a visibilidade do submenu
        if (submenu && submenu.classList.contains('sidebar-submenu')) {
            if (submenu.style.maxHeight) {
                submenu.style.maxHeight = null; // Fecha o submenu
            } else {
                // Define a altura máxima para a altura do conteúdo do submenu
                submenu.style.maxHeight = submenu.scrollHeight + 'px'; 
            }
        }
    };

    dropdownToggles.forEach(toggle => {
        // Remove listener antigo para evitar duplicação
        toggle.removeEventListener('click', toggleDropdown);
        toggle.addEventListener('click', toggleDropdown);
    });

    // --- Abrir automaticamente o dropdown do módulo ativo ---
    // Encontra o link ativo (que tem a classe 'active')
    const activeLink = document.querySelector('.sidebar-nav a.active');
    
    if (activeLink) {
        // Encontra o container .sidebar-submenu pai mais próximo
        const activeSubmenu = activeLink.closest('.sidebar-submenu');
        
        if (activeSubmenu) {
            // Pega o botão que controla este submenu (o elemento anterior)
            const activeToggle = activeSubmenu.previousElementSibling;
            
            // Abre o submenu
            activeSubmenu.style.maxHeight = activeSubmenu.scrollHeight + 'px';
            
            // Marca o botão como 'active'
            if (activeToggle && activeToggle.classList.contains('sidebar-dropdown-toggle')) {
                activeToggle.classList.add('active');
            }
        }
    }
};