document.addEventListener("DOMContentLoaded", function () {
    // Theme Switcher
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;

    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        body.setAttribute('data-theme', 'dark');
        themeToggle.checked = true;
    }

    // Theme toggle handler
    themeToggle.addEventListener('change', function () {
        if (this.checked) {
            body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }
    });

    // // Mobile Navigation
    // const hamburger = document.querySelector('.hamburger');
    // const navLinks = document.querySelector('.nav-links');

    // hamburger?.addEventListener('click', () => {
    //     navLinks.classList.toggle('show');
    //     hamburger.classList.toggle('active');
    // });

    // Header Shrink on Scroll
    let lastScrollTop = 0;
    const header = document.querySelector('.main-header');

    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > 100) {
            header.classList.add('header-shrink');
        } else {
            header.classList.remove('header-shrink');
        }

        lastScrollTop = scrollTop;
    });

    // Smooth Scrolling for Anchor Links
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
                navLinks.classList.remove('show');
            }
        });
    });

    document.getElementById('go-to-dashboard').addEventListener('click', function () {
        window.location.href = '/dashboard';
    });

    document.getElementById('download-txt').addEventListener('click', function(e) {
        e.preventDefault();
        window.location.href = '/samples/txt-sample-file';
    });

    document.getElementById('download-json').addEventListener('click', function(e) {
        e.preventDefault();
        window.location.href = '/samples/json-sample-file';
    });

    document.getElementById('download-docx').addEventListener('click', function(e) {
        e.preventDefault();
        window.location.href = '/samples/docx-sample-file';
    });

    // Image upload handling
    const includeImageToggle = document.getElementById('include-image-toggle');
    const imageUploadContainer = document.getElementById('image-upload-container');
    const imageInput = document.getElementById('image-input');
    const imagePreview = document.getElementById('image-preview');

    if (includeImageToggle) {
        includeImageToggle.addEventListener('change', function () {
            if (this.checked) {
                imageUploadContainer.classList.remove('hidden');
                // Animate image container appearance
                gsap.fromTo(imageUploadContainer,
                    { opacity: 0, y: -20 },
                    { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }
                );
            } else {
                // Animate image container disappearance
                gsap.to(imageUploadContainer, {
                    opacity: 0,
                    y: -20,
                    duration: 0.3,
                    ease: "power2.in",
                    onComplete: () => {
                        imageUploadContainer.classList.add('hidden');
                    }
                });
            }
        });
    }

    if (imageInput) {
        imageInput.addEventListener('change', function () {
            if (this.files && this.files[0]) {
                const reader = new FileReader();

                reader.onload = function (e) {
                    imagePreview.innerHTML = '';
                    imagePreview.style.backgroundImage = `url(${e.target.result})`;

                    // Animate image preview update
                    gsap.fromTo(imagePreview,
                        { scale: 0.8, opacity: 0.5 },
                        { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(1.7)" }
                    );
                }

                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // Tutorial video handling
    const videoOverlay = document.querySelector('.video-overlay');
    const videoContainer = document.querySelector('.video-container');
    const tutorialIframe = document.querySelector('.video-container iframe');

    if (videoOverlay && tutorialIframe) {
        videoOverlay.addEventListener('click', function () {
            // Hide overlay with animation
            gsap.to(videoOverlay, {
                opacity: 0,
                duration: 0.4,
                ease: "power2.out",
                onComplete: () => {
                    videoOverlay.style.display = 'none';

                    // Update iframe src to start playing
                    const currentSrc = tutorialIframe.src;
                    tutorialIframe.src = currentSrc + (currentSrc.includes('?') ? '&' : '?') + 'autoplay=1';
                }
            });
        });
    }

    // File Upload Handling
    const fileInput = document.getElementById('file-input');
    const dragDropArea = document.getElementById('drag-drop-area');
    const fileNameDisplay = document.querySelector('.file-selected-name');
    const uploadForm = document.getElementById('upload-form');
    const livePreview = document.getElementById('live-preview');
    const loadingAnimation = document.querySelector('.loading-animation');
    const pdfPreview = document.getElementById('pdf-preview');

    // Hide loading animation initially
    if (loadingAnimation) {
        loadingAnimation.style.display = 'none';
    }

    // File input change handler
    fileInput?.addEventListener('change', function (e) {
        if (this.files && this.files[0]) {
            fileNameDisplay.textContent = this.files[0].name;
            dragDropArea.classList.add('file-selected');
        }
    });

    // Drag and drop handlers
    dragDropArea?.addEventListener('dragover', function (e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });

    dragDropArea?.addEventListener('dragleave', function () {
        this.classList.remove('drag-over');
    });

    dragDropArea?.addEventListener('drop', function (e) {
        e.preventDefault();
        this.classList.remove('drag-over');

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            fileInput.files = e.dataTransfer.files;
            fileNameDisplay.textContent = e.dataTransfer.files[0].name;
            dragDropArea.classList.add('file-selected');
        }
    });

    // Template selection handler
    const templateCards = document.querySelectorAll('.template-card');
    const selectedTemplateInput = document.getElementById('selected-template');

    templateCards.forEach(card => {
        card.addEventListener('click', function () {
            // Remove selected class from all cards
            templateCards.forEach(c => c.classList.remove('selected'));
            // Add selected class to clicked card
            this.classList.add('selected');
            // Update hidden input value
            selectedTemplateInput.value = this.dataset.template;

            // Animate the selection with GSAP
            gsap.to(this, {
                y: -10,
                scale: 1.03,
                duration: 0.3,
                ease: "back.out(1.5)",
                onComplete: () => {
                    gsap.to(this, {
                        y: 0,
                        scale: 1,
                        duration: 0.2,
                        ease: "power2.out"
                    });
                }
            });
        });
    });


    // Update form submission to include image
    if (uploadForm) {

        const originalSubmitHandler = uploadForm.onsubmit;

        uploadForm.onsubmit = function (e) {
            e.preventDefault();

            // Create FormData object
            const formData = new FormData(this);

            // Add template selection
            formData.append('template', selectedTemplateInput.value);

            // Add image if it's enabled
            if (includeImageToggle && includeImageToggle.checked && imageInput.files[0]) {
                formData.append('profile_image', imageInput.files[0]);
            } else {
                formData.append('include_image', 'false');
            }

            // Show loading animation
            if (loadingAnimation) {
                loadingAnimation.style.display = 'flex';
            }

            // Send form data to server
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
                .then(response => response.text())
                .then(html => {
                    // Rest of the existing code for handling the response
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const downloadLink = doc.querySelector('.download-button')?.getAttribute('href');

                    if (downloadLink) {
                        // Update the page with the download link without a full reload
                        const downloadSection = document.querySelector('.download-section');
                        if (downloadSection) {
                            downloadSection.innerHTML = `
                        <a href="${downloadLink}" class="download-button">
                            <i class="fa-solid fa-download"></i>
                            <span>Download PDF</span>
                        </a>
                    `;
                        } else {
                            // Create the download section if it doesn't exist
                            const newDownloadSection = document.createElement('div');
                            newDownloadSection.className = 'download-section';
                            newDownloadSection.innerHTML = `
                        <a href="${downloadLink}" class="download-button">
                            <i class="fa-solid fa-download"></i>
                            <span>Download PDF</span>
                        </a>
                    `;
                            uploadForm.after(newDownloadSection);
                        }

                        // Update the PDF preview with the new file
                        pdfPreview.src = downloadLink.replace('/download/', '/preview/');

                        // Show success message with GSAP animation
                        const messagesDiv = document.querySelector('.messages');
                        if (messagesDiv) {
                            messagesDiv.innerHTML = `<div class="alert success"><p>File uploaded and converted successfully!</p></div>`;
                            gsap.fromTo('.alert.success',
                                { opacity: 0, y: -20 },
                                { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }
                            );
                        }

                        // Handle live preview section visibility
                        if (livePreview) {
                            gsap.to(livePreview, {
                                opacity: 1,
                                y: 0,
                                duration: 0.5,
                                ease: "power2.out",
                                onComplete: () => {
                                    // Hide loading animation once preview is ready
                                    if (loadingAnimation) {
                                        loadingAnimation.style.display = 'none';
                                    }
                                }
                            });
                        }
                    } else {
                        // Handle error case
                        const messagesDiv = document.querySelector('.messages');
                        if (messagesDiv) {
                            messagesDiv.innerHTML = `<div class="alert error"><p>An error occurred. Please try again.</p></div>`;
                            gsap.fromTo('.alert.error',
                                { opacity: 0, y: -20 },
                                { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }
                            );
                        }
                        if (loadingAnimation) {
                            loadingAnimation.style.display = 'none';
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    const messagesDiv = document.querySelector('.messages');
                    if (messagesDiv) {
                        messagesDiv.innerHTML = `<div class="alert error"><p>Network error. Please try again.</p></div>`;
                    }
                    if (loadingAnimation) {
                        loadingAnimation.style.display = 'none';
                    }
                });
        };
    }

    // Add step number animations on page load
    document.addEventListener('DOMContentLoaded', function () {
        const headings = document.querySelectorAll('.upload-section h3');

        gsap.fromTo(headings,
            { opacity: 0, x: -20 },
            {
                opacity: 1,
                x: 0,
                duration: 0.5,
                stagger: 0.2,
                ease: "power2.out"
            }
        );
    });

    // // Form submission and PDF generation
    // uploadForm?.addEventListener('submit', function (e) {
    //     e.preventDefault();

    //     // Show loading animation
    //     if (loadingAnimation) {
    //         loadingAnimation.style.display = 'flex';
    //     }

    //     // Get form data
    //     const formData = new FormData(this);

    //     // Add template selection to form data
    //     formData.append('template', selectedTemplateInput.value);

    //     // Send form data to server
    //     fetch('/upload', {
    //         method: 'POST',
    //         body: formData
    //     })
    //         .then(response => response.text())
    //         .then(html => {
    //             // Extract the download link and preview link from the response HTML
    //             // This is a simple way to extract links; a more robust approach would be to use JSON responses
    //             const parser = new DOMParser();
    //             const doc = parser.parseFromString(html, 'text/html');
    //             const downloadLink = doc.querySelector('.download-button')?.getAttribute('href');

    //             if (downloadLink) {
    //                 // Update the page with the download link without a full reload
    //                 const downloadSection = document.querySelector('.download-section');
    //                 if (downloadSection) {
    //                     downloadSection.innerHTML = `
    //                     <a href="${downloadLink}" class="download-button">
    //                         <i class="fa-solid fa-download"></i>
    //                         <span>Download PDF</span>
    //                     </a>
    //                 `;
    //                 } else {
    //                     // Create the download section if it doesn't exist
    //                     const newDownloadSection = document.createElement('div');
    //                     newDownloadSection.className = 'download-section';
    //                     newDownloadSection.innerHTML = `
    //                     <a href="${downloadLink}" class="download-button">
    //                         <i class="fa-solid fa-download"></i>
    //                         <span>Download PDF</span>
    //                     </a>
    //                 `;
    //                     uploadForm.after(newDownloadSection);
    //                 }

    //                 // Update the PDF preview with the new file
    //                 pdfPreview.src = downloadLink.replace('/download/', '/preview/');

    //                 // Show success message with GSAP animation
    //                 const messagesDiv = document.querySelector('.messages');
    //                 if (messagesDiv) {
    //                     messagesDiv.innerHTML = `<div class="alert success"><p>File uploaded and converted successfully!</p></div>`;
    //                     gsap.fromTo('.alert.success',
    //                         { opacity: 0, y: -20 },
    //                         { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }
    //                     );
    //                 }

    //                 // Handle live preview section visibility
    //                 if (livePreview) {
    //                     gsap.to(livePreview, {
    //                         opacity: 1,
    //                         y: 0,
    //                         duration: 0.5,
    //                         ease: "power2.out",
    //                         onComplete: () => {
    //                             // Hide loading animation once preview is ready
    //                             if (loadingAnimation) {
    //                                 loadingAnimation.style.display = 'none';
    //                             }
    //                         }
    //                     });
    //                 }
    //             } else {
    //                 // Handle error case
    //                 const messagesDiv = document.querySelector('.messages');
    //                 if (messagesDiv) {
    //                     messagesDiv.innerHTML = `<div class="alert error"><p>An error occurred. Please try again.</p></div>`;
    //                     gsap.fromTo('.alert.error',
    //                         { opacity: 0, y: -20 },
    //                         { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }
    //                     );
    //                 }
    //                 if (loadingAnimation) {
    //                     loadingAnimation.style.display = 'none';
    //                 }
    //             }
    //         })
    //         .catch(error => {
    //             console.error('Error:', error);
    //             const messagesDiv = document.querySelector('.messages');
    //             if (messagesDiv) {
    //                 messagesDiv.innerHTML = `<div class="alert error"><p>Network error. Please try again.</p></div>`;
    //             }
    //             if (loadingAnimation) {
    //                 loadingAnimation.style.display = 'none';
    //             }
    //         });
    // });

    // Sample JSON modal
    const sampleJsonLink = document.getElementById('sample-json');
    const sampleJsonModal = document.getElementById('sample-json-modal');
    const closeModal = document.querySelector('.close-modal');
    const copyJsonButton = document.getElementById('copy-json');
    const jsonDisplay = document.querySelector('.json-display');

    sampleJsonLink?.addEventListener('click', function (e) {
        e.preventDefault();
        sampleJsonModal.style.display = 'block';

        // Animate modal appearance with GSAP
        gsap.fromTo('.modal-content',
            { opacity: 0, y: -50 },
            { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }
        );
    });

    closeModal?.addEventListener('click', function () {
        gsap.to('.modal-content', {
            opacity: 0,
            y: -50,
            duration: 0.3,
            ease: "power2.in",
            onComplete: () => {
                sampleJsonModal.style.display = 'none';
            }
        });
    });

    // Close modal when clicking outside the content
    window.addEventListener('click', function (e) {
        if (e.target === sampleJsonModal) {
            gsap.to('.modal-content', {
                opacity: 0,
                y: -50,
                duration: 0.3,
                ease: "power2.in",
                onComplete: () => {
                    sampleJsonModal.style.display = 'none';
                }
            });
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

    // Contact form handling
    const contactForm = document.getElementById('contact-form');

    contactForm?.addEventListener('submit', function (e) {
        e.preventDefault();

        // Simple form validation
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const message = document.getElementById('message').value;

        if (name && email && message) {
            // Here you would normally send this data to your server

            // Send data to server 
            fetch('/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, email, message })
            })
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                });



            // Create success message
            const formSuccess = document.createElement('div');
            formSuccess.className = 'form-success';
            formSuccess.innerHTML = `
                <i class="fa-solid fa-check-circle"></i>
                <h3>Message Sent!</h3>
                <p>Thank you for your message. I'll get back to you soon.</p>
            `;

            // Replace form with success message
            contactForm.style.height = contactForm.offsetHeight + 'px';
            gsap.to(contactForm, {
                opacity: 0,
                duration: 0.3,
                onComplete: () => {
                    contactForm.parentNode.replaceChild(formSuccess, contactForm);
                    gsap.fromTo(formSuccess,
                        { opacity: 0, scale: 0.9 },
                        { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.5)" }
                    );
                }
            });
        }
    });

    // Scroll animations using GSAP ScrollTrigger
    if (typeof ScrollTrigger !== 'undefined') {
        // Register ScrollTrigger with GSAP
        gsap.registerPlugin(ScrollTrigger);

        // Hero section animations
        gsap.from('.hero-title', {
            scrollTrigger: {
                trigger: '.hero',
                start: 'top center',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            y: 50,
            duration: 0.8,
            ease: "power2.out"
        });

        gsap.from('.hero-subtitle', {
            scrollTrigger: {
                trigger: '.hero',
                start: 'top center',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            y: 50,
            duration: 0.8,
            delay: 0.2,
            ease: "power2.out"
        });

        gsap.from('.cta-button', {
            scrollTrigger: {
                trigger: '.hero',
                start: 'top center',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            y: 50,
            duration: 0.8,
            delay: 0.4,
            ease: "power2.out"
        });

        gsap.from('.cv-preview-placeholder', {
            scrollTrigger: {
                trigger: '.hero',
                start: 'top center',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            x: 50,
            duration: 0.8,
            delay: 0.6,
            ease: "power2.out"
        });

        // Template cards animation
        gsap.from('.template-card', {
            scrollTrigger: {
                trigger: '.templates-grid',
                start: 'top bottom',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            y: 30,
            stagger: 0.1,
            duration: 0.6,
            ease: "power2.out"
        });

        // Upload section animation
        gsap.from('.drag-drop-area', {
            scrollTrigger: {
                trigger: '.upload-container',
                start: 'top bottom',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            y: 30,
            duration: 0.6,
            ease: "power2.out"
        });

        // Templates showcase animation
        gsap.from('.template-showcase-item', {
            scrollTrigger: {
                trigger: '.templates-showcase',
                start: 'top bottom',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            y: 50,
            stagger: 0.3,
            duration: 0.8,
            ease: "power2.out"
        });

        // About section animation
        gsap.from('.about-image', {
            scrollTrigger: {
                trigger: '.about-inner',
                start: 'top bottom',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            x: -50,
            duration: 0.8,
            ease: "power2.out"
        });

        gsap.from('.about-text', {
            scrollTrigger: {
                trigger: '.about-inner',
                start: 'top bottom',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            x: 50,
            duration: 0.8,
            ease: "power2.out"
        });

        // Contact form animation
        gsap.from('.form-group', {
            scrollTrigger: {
                trigger: '.contact-form',
                start: 'top bottom',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            y: 30,
            stagger: 0.1,
            duration: 0.6,
            ease: "power2.out"
        });
    }

    // Form input animations
    const formInputs = document.querySelectorAll('.form-group input, .form-group textarea');

    formInputs.forEach(input => {
        input.addEventListener('focus', function () {
            this.parentNode.classList.add('focused');
        });

        input.addEventListener('blur', function () {
            if (this.value === '') {
                this.parentNode.classList.remove('focused');
            }
        });

        // Check on load if the input has a value
        if (input.value !== '') {
            input.parentNode.classList.add('focused');
        }
    });
});