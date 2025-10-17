// Adiciona o módulo 'main' ao nosso objeto global 'App'
window.App = window.App || {};

App.main = {
    // A função init será chamada quando a página carregar
    init: function() {
        const menuButton = document.querySelector('.dropbtn');
        if (menuButton) {
            menuButton.addEventListener('click', this.toggleMenu);
        }
        window.addEventListener('click', this.closeMenuOnClickOutside);
    },

    toggleMenu: function() {
        document.getElementById("myDropdown").classList.toggle("show");
    },

    closeMenuOnClickOutside: function(event) {
        if (!event.target.matches('.dropbtn')) {
            const dropdowns = document.getElementsByClassName("dropdown-content");
            for (let i = 0; i < dropdowns.length; i++) {
                let openDropdown = dropdowns[i];
                if (openDropdown.classList.contains('show')) {
                    openDropdown.classList.remove('show');
                }
            }
        }
    }
};