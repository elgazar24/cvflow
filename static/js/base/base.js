document.addEventListener("DOMContentLoaded", function () {
    // ===== THEME SWITCHER =====
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        body.setAttribute('data-theme', 'dark');
        themeToggle.checked = true;
    }
    
    // Theme toggle handler
    themeToggle?.addEventListener('change', function() {
        if (this.checked) {
            body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }
    });
    
    // ===== MOBILE NAVIGATION =====
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    
    hamburger?.addEventListener('click', () => {
        navLinks.classList.toggle('show');
        hamburger.classList.toggle('active');
    });
    
    // ===== HEADER SHRINK ON SCROLL =====
    const header = document.querySelector('.main-header');
    
    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > 100) {
            header?.classList.add('header-shrink');
        } else {
            header?.classList.remove('header-shrink');
        }
    });
    
    // ===== SMOOTH SCROLLING FOR ANCHOR LINKS =====
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                navLinks?.classList.remove('show');
                hamburger?.classList.remove('active');
            }
        });
    });
    
    // ===== SAMPLE JSON MODAL =====
    const sampleJsonLink = document.getElementById('sample-json');
    const sampleJsonModal = document.getElementById('sample-json-modal');
    const closeModal = document.querySelector('.close-modal');
    const copyJsonButton = document.getElementById('copy-json');
    const jsonDisplay = document.querySelector('.json-display');
    
    // Modal open/close handlers
    sampleJsonLink?.addEventListener('click', function(e) {
        e.preventDefault();
        sampleJsonModal.style.display = 'block';
    });
    
    closeModal?.addEventListener('click', function() {
        sampleJsonModal.style.display = 'none';
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target === sampleJsonModal) {
            sampleJsonModal.style.display = 'none';
        }
    });
    
    // Copy JSON to clipboard
    copyJsonButton?.addEventListener('click', function() {
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