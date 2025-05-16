
document.addEventListener('DOMContentLoaded', function () {
    // Select all elements with animation classes
    const fadeElements = document.querySelectorAll('.fade-up, .fade-left, .fade-right');

    // Create an Intersection Observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            // If element is in view
            if (entry.isIntersecting) {
                // Add animation class
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translate(0, 0)';
                // Stop observing the element
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1, // Trigger when 10% of the element is visible
        rootMargin: '0px 0px -50px 0px' // Start animation a bit before the element enters the viewport
    });

    // Observe each element
    fadeElements.forEach(element => {
        // Set initial state
        element.style.opacity = 0;
        element.style.transform = element.classList.contains('fade-up') ? 'translateY(20px)' :
            element.classList.contains('fade-left') ? 'translateX(-20px)' : 'translateX(20px)';
        element.style.transition = 'opacity 0.8s ease, transform 0.8s ease';

        // Add delay if specified
        if (element.classList.contains('delay-1')) element.style.transitionDelay = '0.2s';
        if (element.classList.contains('delay-2')) element.style.transitionDelay = '0.4s';
        if (element.classList.contains('delay-3')) element.style.transitionDelay = '0.6s';
        if (element.classList.contains('delay-4')) element.style.transitionDelay = '0.8s';
        if (element.classList.contains('delay-5')) element.style.transitionDelay = '1s';

        observer.observe(element);
    });
});
