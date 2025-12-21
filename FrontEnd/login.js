document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const phoneInput = document.getElementById('phone');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const phone = phoneInput.value.trim();
        if (!phone) return alert('Please enter a phone number');

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone })
            });
            if (res.ok) {
                localStorage.setItem('eagle_user', phone);
                window.location.href = '/';
            } else {
                alert('Login failed');
            }
        } catch (err) {
            console.error('Login error', err);
            alert('Login failed (see console)');
        }
    });
});