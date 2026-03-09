const API_BASE = "http://127.0.0.1:8001/api";

console.log("DevBrain: popup.js script started");

document.addEventListener('DOMContentLoaded', async () => {
    console.log("DevBrain: DOMContentLoaded fired");

    const loginBtn = document.getElementById('login-btn');
    const status = document.getElementById('status');
    const emailInput = document.getElementById('email');
    const passInput = document.getElementById('pass');

    if (!loginBtn) {
        console.error("DevBrain: Could not find login-btn element!");
        return;
    }

    // Check login state
    try {
        const data = await chrome.storage.local.get(['devbrain_token']);
        if (data.devbrain_token) {
            document.getElementById('login-view').style.display = 'none';
            document.getElementById('logout-view').style.display = 'block';
        }
    } catch (e) {
        console.error("DevBrain: Storage error:", e);
    }

    loginBtn.addEventListener('click', async () => {
        const email = emailInput.value.trim();
        const password = passInput.value;

        console.log("DevBrain: Secure Connect button clicked!");
        status.textContent = "Connecting...";

        if (!email || !password) {
            status.textContent = "Error: Email and password required";
            return;
        }

        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            console.log("DevBrain: Sending fetch to", `${API_BASE}/auth/login`);

            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData,
            });

            console.log("DevBrain: Fetch response status:", res.status);
            const json = await res.json();

            if (res.ok) {
                console.log("DevBrain: Login success!");
                await chrome.storage.local.set({ 'devbrain_token': json.access_token });
                status.textContent = "Connected!";
                setTimeout(() => window.location.reload(), 500);
            } else {
                console.warn("DevBrain: Login failed:", json.detail);
                status.textContent = "Login Failed: " + (json.detail || "Check credentials");
            }
        } catch (e) {
            console.error("DevBrain: Network/Fetch error:", e);
            status.textContent = "Network Error: Is the backend server running?";
        }
    });

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            await chrome.storage.local.remove('devbrain_token');
            window.location.reload();
        });
    }
});
