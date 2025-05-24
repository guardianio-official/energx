document.addEventListener('DOMContentLoaded', function() {

    // Contact Form Interaction (Placeholder Feedback)
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent actual submission for this static site

            const feedbackElement = document.getElementById('form-feedback');
            if (feedbackElement) {
                // Basic validation check
                const name = contactForm.fullName.value;
                const email = contactForm.email.value;
                const subject = contactForm.subject.value;
                const message = contactForm.message.value;

                if (name && email && subject && message) {
                    feedbackElement.textContent = 'Thank you for your message! (This is a demo - no email was sent.)';
                    feedbackElement.style.color = 'green';
                    contactForm.reset();
                } else {
                    feedbackElement.textContent = 'Please fill out all required fields.';
                    feedbackElement.style.color = 'red';
                }
            }
        });
    }

    // Mobile Navigation Toggle (Conceptual - Basic Implementation)
    // This requires specific HTML structure for the toggle button and nav menu.
    // For this example, let's assume a button with id="mobile-nav-toggle" and nav ul.
    
    const nav = document.querySelector('header nav ul');
    const logo = document.querySelector('header nav .logo'); // To ensure it's always visible

    if (nav) {
        // Create a toggle button if it doesn't exist (for simplicity in this example)
        let mobileNavToggle = document.getElementById('mobile-nav-toggle');
        if (!mobileNavToggle && window.innerWidth <= 768) { // Only create if not present and on smaller screens
            mobileNavToggle = document.createElement('button');
            mobileNavToggle.setAttribute('id', 'mobile-nav-toggle');
            mobileNavToggle.textContent = 'Menu';
            mobileNavToggle.style.display = 'block'; // Initially hidden by CSS @media query, shown here for smaller screens
            mobileNavToggle.style.position = 'absolute';
            mobileNavToggle.style.top = '20px';
            mobileNavToggle.style.right = '20px';
            mobileNavToggle.style.padding = '10px';
            mobileNavToggle.style.backgroundColor = '#00796b';
            mobileNavToggle.style.color = 'white';
            mobileNavToggle.style.border = 'none';
            mobileNavToggle.style.cursor = 'pointer';
            mobileNavToggle.style.zIndex = '1001'; // Above nav
            
            const headerNav = document.querySelector('header nav');
            if(headerNav) {
                 headerNav.insertBefore(mobileNavToggle, headerNav.firstChild); // Insert before the logo or ul
            }
        }


        if (mobileNavToggle) {
            mobileNavToggle.addEventListener('click', function() {
                if (nav.style.display === 'flex' || nav.style.display === '') { // Check current computed style if more complex
                    nav.style.display = 'none';
                    mobileNavToggle.textContent = 'Menu';
                } else {
                    nav.style.display = 'flex'; // Or 'block' depending on desired mobile layout
                    nav.style.flexDirection = 'column'; // Ensure vertical layout on mobile
                    mobileNavToggle.textContent = 'Close';
                }
            });

            // Initial setup based on screen size
            function handleResize() {
                if (window.innerWidth > 768) {
                    nav.style.display = 'flex'; // Horizontal for desktop
                    nav.style.flexDirection = 'row';
                    if(mobileNavToggle) mobileNavToggle.style.display = 'none'; // Hide toggle on desktop
                } else {
                    nav.style.display = 'none'; // Hide nav by default on mobile
                    if(mobileNavToggle) mobileNavToggle.style.display = 'block'; // Show toggle on mobile
                    mobileNavToggle.textContent = 'Menu';
                }
            }

            window.addEventListener('resize', handleResize);
            handleResize(); // Call on load
        }
    }

    // Active navigation link highlighting
    const currentLocation = window.location.pathname.split("/").pop();
    const navLinks = document.querySelectorAll('header nav ul li a');

    navLinks.forEach(link => {
        const linkPage = link.getAttribute('href').split("/").pop();
        if (currentLocation === linkPage || (currentLocation === '' && linkPage === 'index.html')) {
            link.classList.add('active');
        }
    });

});
