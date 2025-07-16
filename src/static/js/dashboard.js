// Dashboard JS for MR HUX Alpha Bot

// --- DOM Elements ---
const statsPanel = document.querySelector('.stats-panel');
const activeSourcesCount = document.getElementById('activeSourcesCount');
const messagesToday = document.getElementById('messagesToday');
const tokenMentions = document.getElementById('tokenMentions');
const alertsToday = document.getElementById('alertsToday');
const telegramSources = document.getElementById('telegramSources');
const discordSources = document.getElementById('discordSources');
const xSources = document.getElementById('xSources');
const addSourceBtn = document.getElementById('addSourceBtn');
const addSourceModal = document.getElementById('addSourceModal');
const addSourceForm = document.getElementById('addSourceForm');

// --- Modal Logic ---
addSourceBtn.onclick = () => {
  addSourceModal.style.display = 'block';
};
function closeModal() {
  addSourceModal.style.display = 'none';
}
window.closeModal = closeModal;

// --- Source Type Toggle ---
const typeBtns = document.querySelectorAll('.source-type-btn');
typeBtns.forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.form-group').forEach(g => g.classList.add('hidden'));
    if (btn.dataset.type === 'telegram') document.querySelector('.telegram-input').classList.remove('hidden');
    if (btn.dataset.type === 'discord') document.querySelector('.discord-input').classList.remove('hidden');
    if (btn.dataset.type === 'x') document.querySelector('.x-input').classList.remove('hidden');
  };
});

// --- Tab Switching Logic ---
const navBtns = document.querySelectorAll('.nav-btn');
const sections = document.querySelectorAll('.section');
navBtns.forEach(btn => {
  btn.onclick = () => {
    navBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    sections.forEach(sec => sec.classList.remove('active'));
    const section = document.getElementById(btn.dataset.section);
    if (section) section.classList.add('active');
    // Load content for the selected tab
    if (btn.dataset.section === 'monitoring') {
      loadStats();
      loadSources();
    } else if (btn.dataset.section === 'tokens') {
      loadTokens();
    } else if (btn.dataset.section === 'alerts') {
      loadAlerts();
    } else if (btn.dataset.section === 'settings') {
      loadSettings();
    }
  };
});

// --- Fetch and Render Stats ---
async function loadStats() {
  const res = await fetch('/api/stats');
  const data = await res.json();
  activeSourcesCount.textContent = data.stats.sources;
  messagesToday.textContent = data.stats.messages_today;
  tokenMentions.textContent = data.stats.token_mentions;
  alertsToday.textContent = data.stats.alerts_sent;
}

// --- Fetch and Render Sources ---
async function loadSources() {
  const res = await fetch('/api/sources');
  const data = await res.json();
  telegramSources.innerHTML = '';
  discordSources.innerHTML = '';
  xSources.innerHTML = '';
  data.sources.forEach(src => {
    const el = document.createElement('div');
    el.className = 'source-item';
    el.textContent = src.name;
    if (src.type === 'telegram') telegramSources.appendChild(el);
    if (src.type === 'discord') discordSources.appendChild(el);
    if (src.type === 'x') xSources.appendChild(el);
  });
}

// --- Add Source Form ---
addSourceForm.onsubmit = async (e) => {
  e.preventDefault();
  let type, name;
  if (!document.querySelector('.telegram-input').classList.contains('hidden')) {
    type = 'telegram';
    name = addSourceForm.telegramId.value;
  } else if (!document.querySelector('.discord-input').classList.contains('hidden')) {
    type = 'discord';
    name = addSourceForm.discordId.value;
  } else if (!document.querySelector('.x-input').classList.contains('hidden')) {
    type = 'x';
    name = addSourceForm.xHandle.value;
  }
  if (name) {
    await fetch('/api/sources', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, name })
    });
    closeModal();
    loadSources();
  }
};

// --- Load Tokens (Placeholder) ---
async function loadTokens() {
  const tokensList = document.getElementById('tokensList');
  tokensList.innerHTML = '<p>Loading tokens...</p>';
  try {
    const res = await fetch('/api/tokens');
    const data = await res.json();
    if (data.tokens && data.tokens.length > 0) {
      tokensList.innerHTML = data.tokens.map(token => `<div class="token-summary">${token.name} (${token.symbol}) - <b>${token.address}</b></div>`).join('');
    } else {
      tokensList.innerHTML = '<p>No tokens found.</p>';
    }
  } catch (e) {
    tokensList.innerHTML = '<p>Failed to load tokens.</p>';
  }
}

// --- Load Alerts (Placeholder) ---
async function loadAlerts() {
  const alertsList = document.getElementById('alertsList');
  alertsList.innerHTML = '<p>Loading alerts...</p>';
  try {
    const res = await fetch('/api/alerts');
    const data = await res.json();
    if (data.alerts && data.alerts.length > 0) {
      alertsList.innerHTML = data.alerts.map(alert => `<div class="alert-item">${alert.message} <span class="alert-type">[${alert.type}]</span></div>`).join('');
    } else {
      alertsList.innerHTML = '<p>No recent alerts.</p>';
    }
  } catch (e) {
    alertsList.innerHTML = '<p>Failed to load alerts.</p>';
  }
}

// --- Load Settings (Placeholder) ---
async function loadSettings() {
  const settingsPanel = document.getElementById('settingsPanel');
  settingsPanel.innerHTML = '<p>Loading settings...</p>';
  try {
    const res = await fetch('/api/config');
    const data = await res.json();
    settingsPanel.innerHTML = `<pre>${JSON.stringify(data.config, null, 2)}</pre>`;
  } catch (e) {
    settingsPanel.innerHTML = '<p>Failed to load settings.</p>';
  }
}

// --- WebSocket for Live Stats ---
function connectWebSocket() {
  const ws = new WebSocket(`ws://${window.location.host}/ws/dashboard`);
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'stats') {
      activeSourcesCount.textContent = msg.data.sources;
      alertsToday.textContent = msg.data.alerts_sent;
    }
  };
  ws.onclose = () => setTimeout(connectWebSocket, 2000);
}

// --- Initial Load ---
window.onload = () => {
  loadStats();
  loadSources();
  connectWebSocket();
};
