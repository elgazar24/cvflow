


document.addEventListener("DOMContentLoaded", function () {

    const header = document.getElementById('site-header');
    const navToggle = document.querySelector('.nav-toggle');
    const mainMenu = document.getElementById('main-menu');
    const themeToggle = document.getElementById('theme-toggle');
    const dropdownToggles = document.querySelectorAll('.nav-dropdown-toggle');
    const announcementClose = document.querySelector('.announcement-close');
    const announcementBanner = document.querySelector('.announcement-banner');

    // Handle scroll effects
    function handleScroll() {
        if (window.scrollY > 10) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }

    // Toggle mobile menu
    if (navToggle) {
        navToggle.addEventListener('click', function () {
            const expanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', !expanded);
            document.body.style.overflow = expanded ? '' : 'hidden';
        });
    }

    // Handle dropdowns
    if (dropdownToggles.length > 0) {
        dropdownToggles.forEach(toggle => {
            toggle.addEventListener('click', function () {
                const expanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', !expanded);
            });
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', function (e) {
            dropdownToggles.forEach(toggle => {
                if (!toggle.contains(e.target)) {
                    toggle.setAttribute('aria-expanded', 'false');
                }
            });
        });
    }

    // Handle theme toggle
    if (themeToggle) {
        // Check for saved theme preference or respect OS preference
        if (localStorage.getItem('theme') === 'dark' ||
            (!localStorage.getItem('theme') &&
                window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.setAttribute('data-theme', 'dark');
            themeToggle.checked = true;
        }

        themeToggle.addEventListener('change', function () {
            if (this.checked) {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
            }
        });
    }

    // Close announcement banner
    if (announcementClose && announcementBanner) {
        console.log( "Close Clicked" );
        announcementClose.addEventListener('click', function () {
            announcementBanner.style.display = 'none';
            localStorage.setItem('announcement-closed', 'true');
        });

        // Check if announcement was previously closed
        if (localStorage.getItem('announcement-closed') === 'true') {
            announcementBanner.style.display = 'none';
        }
    }

    // Register scroll event listener
    window.addEventListener('scroll', handleScroll);

    // Initialize scroll state
    handleScroll();

    // ===== SAMPLE JSON MODAL =====
    const sampleJsonLink = document.getElementById('sample-json');
    const sampleJsonModal = document.getElementById('sample-json-modal');
    const closeModal = document.querySelector('.close-modal');
    const copyJsonButton = document.getElementById('copy-json');
    const jsonDisplay = document.querySelector('.json-display');

    // Modal open/close handlers
    sampleJsonLink?.addEventListener('click', function (e) {
        e.preventDefault();
        sampleJsonModal.style.display = 'block';
    });

    closeModal?.addEventListener('click', function () {
        sampleJsonModal.style.display = 'none';
    });

    // Close modal when clicking outside
    window.addEventListener('click', function (e) {
        if (e.target === sampleJsonModal) {
            sampleJsonModal.style.display = 'none';
        }
    });

    // Copy JSON to clipboard
    copyJsonButton?.addEventListener('click', function () {
        const jsonText = jsonDisplay.textContent;
        navigator.clipboard.writeText(jsonText)
            .then(() => {
                // Change button text temporarily
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fa-solid fa-check"></i><span>Copied!</span>';
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            })
            .catch(err => {
                console.error('Could not copy text: ', err);
            });
    });
});