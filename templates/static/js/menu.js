(function() {
    'use strict';
    
    function initMenu() {
        const hamBurger = document.querySelector(".toggle-btn");
        const toggleBar = document.querySelector("#toggle-bar");
        const sidebar = document.querySelector("#sidebar");
        const sidebarWrapper = document.querySelector("#sidebar-wrapper");

        if (!sidebar || !sidebarWrapper) {
            console.warn('Elementos do menu não encontrados');
            return;
        }

        function toggleSidebar(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            sidebar.classList.toggle("expand");
            sidebarWrapper.classList.toggle("expand");
        }

        if (hamBurger) {
            hamBurger.addEventListener("click", toggleSidebar);
        }

        if (toggleBar) {
            toggleBar.addEventListener("click", toggleSidebar);
            toggleBar.style.pointerEvents = 'auto';
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMenu);
    } else {
        initMenu();
    }
})();