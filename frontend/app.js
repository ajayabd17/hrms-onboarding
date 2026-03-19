document.addEventListener('DOMContentLoaded', () => {

    // Login Form Handler
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const btn = document.getElementById('login-btn');
            const btnText = btn.querySelector('span');
            const loader = btn.querySelector('.loader');
            
            // Simple micro-animation for the login button
            btn.style.opacity = '0.8';
            btn.style.pointerEvents = 'none';
            btnText.innerHTML = 'Authenticating...';
            
            // Check the selected role to route the user (mock auth)
            const role = document.querySelector('input[name="role"]:checked').value;
            
            // Simulate network delay for effect
            setTimeout(() => {
                if (role === 'employee') {
                    window.location.href = 'employee-dashboard.html';
                } else {
                    window.location.href = 'hr-dashboard.html';
                }
            }, 1000);
        });
    }

    // Logout Handlers
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
             window.location.href = 'index.html';
        });
    }

    // Dynamic initializations for HR Dashboard/Employee Dashboard can be added here
    // as well as AWS endpoints if available.
    
    // Add simple hover effect sound or subtle interactions here
    const cards = document.querySelectorAll('.stage-card, .pipeline-item');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = card.classList.contains('pipeline-item') 
                ? 'translateX(5px)' 
                : 'translateY(-5px)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translate(0)';
        });
    });
});
