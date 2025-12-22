document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const passwordInput = document.getElementById('password');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = usernameInput.value.trim();
        const email = emailInput.value.trim();
        const phone = phoneInput.value.trim();
        const password = passwordInput.value.trim();
        
        if (!username || !email || !phone || !password) {
            alert('Please fill in all fields');
            return;
        }

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, phone, password })
            });
            if (res.ok) {
                // Store user data
                localStorage.setItem('eagle_user', JSON.stringify({ username, email, phone, password }));
                window.location.href = '/dashboard';
            } else {
                alert('Login failed. Please check your information.');
            }
        } catch (err) {
            console.error('Login error', err);
            alert('Login failed (see console)');
        }
    });
});