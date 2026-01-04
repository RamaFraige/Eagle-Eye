// ...existing code...
/*
Features:
- Loads alerts (fetch fallback to sample data)
- Filter by category tabs + search
- Open clip modal, play clip
- Save/download clip
- Dismiss alert (persisted in localStorage)
- Open feedback modal and POST feedback to chatbot endpoint
*/

const API_ALERTS = '/api/alerts';        // replace with real backend
const API_FEEDBACK = '/api/feedback';    // replace with real backend
const CLIP_BASE = '/clips/';             // base path for clip URLs if used

document.addEventListener('DOMContentLoaded', () => {
    // ... existing code ...

    // Login/Notification setup
    const loginLink = document.getElementById('login-link');
    const notificationBell = document.getElementById('notification-bell');
    let userData = null;
    try {
        userData = JSON.parse(localStorage.getItem('eagle_user'));
    } catch (e) {
        userData = null;
    }
    let notificationsEnabled = localStorage.getItem('eagle_notifications') === 'true';
    let userPhone = userData ? userData.phone : null;

    function updateAuthUI() {
        if (userData) {
            loginLink.textContent = `Logout (${userData.username})`;
            loginLink.href = '#';
            loginLink.addEventListener('click', logout);
            notificationBell.classList.toggle('active', notificationsEnabled);
            notificationBell.style.display = 'block';
        } else {
            loginLink.textContent = 'Login';
            loginLink.href = '/';
            notificationBell.style.display = 'none';
        }
    }

    function logout(e) {
        e.preventDefault();
        localStorage.removeItem('eagle_user');
        localStorage.removeItem('eagle_notifications');
        userData = null;
        userPhone = null;
        notificationsEnabled = false;
        updateAuthUI();
    }

    notificationBell.addEventListener('click', () => {
        if (!userPhone) return;
        notificationsEnabled = !notificationsEnabled;
        localStorage.setItem('eagle_notifications', notificationsEnabled);
        updateAuthUI();
        alert(notificationsEnabled ? 'Notifications enabled' : 'Notifications disabled');
    });

    updateAuthUI();

    // ... existing code ...
    const alertsList = document.getElementById('alerts-list');
    const tabs = Array.from(document.querySelectorAll('.tab'));
    const searchInput = document.getElementById('search');
    const refreshBtn = document.getElementById('refresh');

    const playerModal = document.getElementById('player-modal');
    const clipPlayer = document.getElementById('clip-player');
    const clipImage = document.getElementById('clip-image');
    const modalAlertInfo = document.getElementById('modal-alert-info');
    const closeModal = document.getElementById('close-modal');
    const saveClipBtn = document.getElementById('save-clip');
    const dismissClipBtn = document.getElementById('dismiss-clip');
    const feedbackOpenBtn = document.getElementById('feedback-open');

    const feedbackModal = document.getElementById('feedback-modal');
    const closeFeedback = document.getElementById('close-feedback');
    const cancelFeedback = document.getElementById('cancel-feedback');
    const sendFeedbackBtn = document.getElementById('send-feedback');
    const feedbackText = document.getElementById('feedback-text');
    const feedbackStatus = document.getElementById('feedback-status');

    let alerts = [];
    let currentFilter = 'all';
    let currentAlert = null;
    const dismissedKey = 'eagle_dismissed_alerts';
    const dismissedSet = new Set(JSON.parse(localStorage.getItem(dismissedKey) || '[]'));

    async function loadAlerts() {
        console.log('Loading alerts...');
        try {
            const res = await fetch(API_ALERTS);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            alerts = await res.json();
        } catch (err) {
            console.warn('Failed to load alerts from API, using sample data. Error:', err);
            alerts = sampleAlerts();
        }
        renderList();
        
        // Send notification if enabled and there are active alerts
        console.log('User phone:', userPhone, 'Notifications enabled:', notificationsEnabled, 'Alerts count:', alerts.length);
        if (notificationsEnabled && userPhone && alerts.length > 0) {
            console.log('Sending notification SMS...');
            sendNotificationSMS(`New alerts detected: ${alerts.length} active threats.`);
        } else {
            console.log('Not sending SMS - conditions not met');
        }
    }

    async function sendNotificationSMS(message) {
        console.log('Attempting to send SMS:', message);
        try {
            const res = await fetch('/api/send_sms', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: userPhone, message })
            });
            console.log('SMS response:', res.status);
            if (res.ok) {
                console.log('SMS sent successfully');
            } else {
                console.log('SMS failed with status:', res.status);
            }
        } catch (err) {
            console.error('SMS send failed', err);
        }
    }

    function sampleAlerts() {
        // Minimal sample data; fields: id, type, title, message, time, clipUrl
        const now = new Date();
        return [
            { id: 'a1', type: 'weapon', title: 'Weapon detected', message: 'Possible weapon seen near gate', time: now.toISOString(), clipUrl: CLIP_BASE + 'a1.mp4' },
            { id: 'a2', type: 'smoke', title: 'Smoke detected', message: 'Smoke in parking area', time: now.toISOString(), clipUrl: CLIP_BASE + 'a2.mp4' },
            { id: 'a3', type: 'fight', title: 'Fight detected', message: 'Group altercation', time: now.toISOString(), clipUrl: CLIP_BASE + 'a3.mp4' },
            { id: 'a4', type: 'entry', title: 'Unauthorized entry', message: 'Door breach at back entrance', time: now.toISOString(), clipUrl: CLIP_BASE + 'a4.mp4' },
        ];
    }

    function renderList() {
        const q = (searchInput.value || '').toLowerCase().trim();
        const visible = alerts.filter(a => {
            if (dismissedSet.has(a.id)) return false;
            if (currentFilter !== 'all' && a.type !== currentFilter) return false;
            if (!q) return true;
            return (a.title + ' ' + a.message + ' ' + a.type).toLowerCase().includes(q);
        });

        alertsList.innerHTML = '';
        if (visible.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'empty';
            empty.textContent = 'No active alerts.';
            alertsList.appendChild(empty);
            return;
        }

        visible.forEach(a => {
            const card = document.createElement('article');
            card.className = 'alert-card';
            card.innerHTML = `
                <div class="card-left">
                    <div class="type ${a.type}">${a.type.toUpperCase()}</div>
                </div>
                <div class="card-main">
                    <h3>${escapeHtml(a.title)}</h3>
                    <p class="muted">${escapeHtml(a.message)}</p>
                    <div class="meta">${new Date(a.time).toLocaleString()}</div>
                </div>
                <div class="card-actions">
                    <button class="play" data-id="${a.id}">View Clip</button>
                    <button class="save" data-id="${a.id}">Save</button>
                    <button class="dismiss" data-id="${a.id}">Dismiss</button>
                </div>
            `;
            alertsList.appendChild(card);
        });

        // attach handlers
        alertsList.querySelectorAll('.play').forEach(b => b.addEventListener('click', e => openAlert(e.target.dataset.id)));
        alertsList.querySelectorAll('.save').forEach(b => b.addEventListener('click', e => saveClipById(e.target.dataset.id)));
        alertsList.querySelectorAll('.dismiss').forEach(b => b.addEventListener('click', e => dismissById(e.target.dataset.id)));
    }

    function openAlert(id) {
        currentAlert = alerts.find(a => a.id === id);
        if (!currentAlert) return;
        const isImage = currentAlert.clipUrl && currentAlert.clipUrl.match(/\.jpe?g$|\.png$/i);
        if (isImage) {
            clipPlayer.classList.add('hidden');
            clipPlayer.pause();
            clipPlayer.removeAttribute('src');
            clipImage.classList.remove('hidden');
            clipImage.src = currentAlert.clipUrl;
        } else {
            clipImage.classList.add('hidden');
            clipImage.removeAttribute('src');
            clipPlayer.classList.remove('hidden');
            clipPlayer.pause();
            clipPlayer.removeAttribute('src');
            clipPlayer.src = currentAlert.clipUrl;
            clipPlayer.load();
        }
        modalAlertInfo.textContent = `${currentAlert.title} — ${new Date(currentAlert.time).toLocaleString()}`;
        showModal(playerModal);
    }

    function showModal(el) {
        el.classList.remove('hidden');
        el.focus?.();
    }
    function hideModal(el) {
        el.classList.add('hidden');
    }
    
    async function saveClipById(id) {
        const a = alerts.find(x => x.id === id);
        if (!a || !a.clipUrl) return alert('Clip not found');
        const ext = (a.clipUrl.split('.').pop() || 'mp4').toLowerCase();
        const filename = `${a.id || 'alert'}_${a.type}_${new Date(a.time).toISOString().replace(/[:.]/g,'-')}.${ext}`;
        try {
            await downloadFile(a.clipUrl, filename);
            alert('Clip saved.');
        } catch (err) {
            console.error('Save failed', err);
            alert('Failed to save clip (see console)');
        }
    }

    async function downloadFile(url, filename) {
        // Attempt CORS-friendly streaming download, fallback to anchor download
        const res = await fetch(url);
        if (!res.ok) throw new Error('Download failed');
        const blob = await res.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(link.href);
    }
    
    function dismissById(id) {
        const ok = confirm('Dismiss this alert?');
        if (!ok) return;
        dismissedSet.add(id);
        persistDismissed();
        renderList();
    }

    function persistDismissed() {
        localStorage.setItem(dismissedKey, JSON.stringify(Array.from(dismissedSet)));
    }

    // feedback flow
    feedbackOpenBtn.addEventListener('click', () => {
        if (!currentAlert) return alert('Open an alert first.');
        feedbackText.value = `Alert ${currentAlert.id}: `;
        feedbackStatus.textContent = '';
        showModal(feedbackModal);
    });

    sendFeedbackBtn.addEventListener('click', async () => {
        if (!currentAlert) return alert('No alert open');
        const text = feedbackText.value.trim();
        if (!text) { feedbackStatus.textContent = 'Please enter feedback.'; return; }
        feedbackStatus.textContent = 'Sending...';
        try {
            const res = await fetch(API_FEEDBACK, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    alertId: currentAlert.id, 
                    message: text,
                    userData: userData  // Include user information
                })
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            feedbackStatus.textContent = json.bot_response || 'Feedback sent.';
            // optionally read bot response and show
            // show bot reply...
            setTimeout(() => hideModal(feedbackModal), 2000);
        } catch (err) {
            console.error('Feedback error', err);
            feedbackStatus.textContent = 'Failed to send feedback (see console)';
        }
    });

    // modal close handlers
    closeModal.addEventListener('click', () => { clipPlayer.pause(); hideModal(playerModal); });
    closeFeedback.addEventListener('click', () => hideModal(feedbackModal));
    cancelFeedback.addEventListener('click', () => hideModal(feedbackModal));

    // top modal buttons (player)
    saveClipBtn.addEventListener('click', () => { if (currentAlert) saveClipById(currentAlert.id); });
    dismissClipBtn.addEventListener('click', () => { if (currentAlert) { dismissById(currentAlert.id); hideModal(playerModal); } });

    // tabs and search
    tabs.forEach(t => t.addEventListener('click', () => {
        tabs.forEach(x => x.classList.remove('active'));
        t.classList.add('active');
        currentFilter = t.dataset.type;
        renderList();
    }));
    searchInput.addEventListener('input', debounce(renderList, 250));
    refreshBtn.addEventListener('click', loadAlerts);

    // keyboard: Esc closes modals
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (!playerModal.classList.contains('hidden')) { clipPlayer.pause(); hideModal(playerModal); }
            if (!feedbackModal.classList.contains('hidden')) hideModal(feedbackModal);
        }
    });

    // initial load
    loadAlerts();

    // helpers
    function escapeHtml(s = '') {
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    }
    function debounce(fn, wait) {
        let t;
        return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
    }
});