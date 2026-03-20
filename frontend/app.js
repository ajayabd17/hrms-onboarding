// AWS Cognito Configuration
const COGNITO_CLIENT_ID = 'hp08mpeaq49rmj1l0fo36gmdq'; // Replace with your actual App Client ID
const COGNITO_REGION = 'ap-south-1'; // e.g., 'us-east-1'

document.addEventListener('DOMContentLoaded', () => {

    // Login Form Handler
    const loginForm = document.getElementById('login-form');
    const roleSelect = document.getElementById('role');
    const emailInput = document.getElementById('email');
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
            
            // Authenticate with Cognito via REST API
            const passwordInput = document.getElementById('password');
            const errorBox = document.getElementById('login-error');
            if (errorBox) errorBox.classList.add('hidden');
            
            fetch(`https://cognito-idp.${COGNITO_REGION}.amazonaws.com/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-amz-json-1.1',
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
                },
                body: JSON.stringify({
                    AuthParameters: {
                        USERNAME: emailInput.value,
                        PASSWORD: passwordInput.value
                    },
                    AuthFlow: 'USER_PASSWORD_AUTH',
                    ClientId: COGNITO_CLIENT_ID
                })
            })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(({ status, body }) => {
                if (status !== 200) {
                    throw new Error(body.message || 'Authentication failed');
                }
                
                const idToken = body.AuthenticationResult.IdToken;
                const accessToken = body.AuthenticationResult.AccessToken;
                
                sessionStorage.setItem('idToken', idToken);
                sessionStorage.setItem('accessToken', accessToken);
                
                // Decode JWT payload to extract groups
                const base64Url = idToken.split('.')[1];
                const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => 
                    '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
                ).join(''));
                
                const payload = JSON.parse(jsonPayload);
                const groups = payload['cognito:groups'] || [];
                
                if (groups.includes('HR') || groups.includes('Manager')) {
                    window.location.href = 'hr-dashboard.html';
                } else {
                    window.location.href = 'employee-dashboard.html';
                }
            })
            .catch(err => {
                if (errorBox) {
                    errorBox.textContent = err.message;
                    errorBox.classList.remove('hidden');
                } else {
                    alert(err.message);
                }
                // Reset button
                btn.style.opacity = '1';
                btn.style.pointerEvents = 'auto';
                btnText.innerHTML = 'Sign In Securely';
            });
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
