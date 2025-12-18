// Get current tab info
async function getCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

// Show status message
function showStatus(message, type = 'success') {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status show ${type}`;
  setTimeout(() => {
    status.classList.remove('show');
  }, 3000);
}

// Load and display current site
async function loadCurrentSite() {
  const tab = await getCurrentTab();
  if (tab && tab.url) {
    try {
      const url = new URL(tab.url);
      document.getElementById('currentSite').textContent = url.hostname;
    } catch (e) {
      document.getElementById('currentSite').textContent = 'Invalid URL';
    }
  }
}

// Load stored data
async function loadData() {
  const data = await chrome.storage.local.get(['headers', 'cookies']);
  return {
    headers: data.headers || [],
    cookies: data.cookies || []
  };
}

// Save data
async function saveData(headers, cookies) {
  await chrome.storage.local.set({ headers, cookies });
  // Notify background script to update rules
  chrome.runtime.sendMessage({ type: 'updateRules' });
}

// Render headers list
function renderHeaders(headers) {
  const container = document.getElementById('headersList');
  if (headers.length === 0) {
    container.innerHTML = '<div class="empty-state">No headers configured</div>';
    return;
  }

  container.innerHTML = headers.map((header, index) => `
    <div class="item ${header.enabled ? '' : 'disabled'}">
      <div class="item-info">
        <div class="item-name">${escapeHtml(header.name)}</div>
        <div class="item-value">${escapeHtml(header.value)}</div>
      </div>
      <div class="item-actions">
        <button class="btn-toggle ${header.enabled ? '' : 'disabled'}" data-index="${index}" data-type="header">
          ${header.enabled ? 'Disable' : 'Enable'}
        </button>
        <button class="btn-remove" data-index="${index}" data-type="header">Remove</button>
      </div>
    </div>
  `).join('');

  // Add event listeners
  container.querySelectorAll('.btn-toggle').forEach(btn => {
    btn.addEventListener('click', handleToggle);
  });
  container.querySelectorAll('.btn-remove').forEach(btn => {
    btn.addEventListener('click', handleRemove);
  });
}

// Render cookies list
function renderCookies(cookies) {
  const container = document.getElementById('cookiesList');
  if (cookies.length === 0) {
    container.innerHTML = '<div class="empty-state">No cookie modifiers configured</div>';
    return;
  }

  container.innerHTML = cookies.map((cookie, index) => `
    <div class="item ${cookie.enabled ? '' : 'disabled'}">
      <div class="item-info">
        <div class="item-name">${escapeHtml(cookie.name)}</div>
        <div class="item-value">Append: ${escapeHtml(cookie.append)}</div>
      </div>
      <div class="item-actions">
        <button class="btn-toggle ${cookie.enabled ? '' : 'disabled'}" data-index="${index}" data-type="cookie">
          ${cookie.enabled ? 'Disable' : 'Enable'}
        </button>
        <button class="btn-remove" data-index="${index}" data-type="cookie">Remove</button>
      </div>
    </div>
  `).join('');

  // Add event listeners
  container.querySelectorAll('.btn-toggle').forEach(btn => {
    btn.addEventListener('click', handleToggle);
  });
  container.querySelectorAll('.btn-remove').forEach(btn => {
    btn.addEventListener('click', handleRemove);
  });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Handle toggle
async function handleToggle(e) {
  const index = parseInt(e.target.dataset.index);
  const type = e.target.dataset.type;

  const data = await loadData();

  if (type === 'header') {
    data.headers[index].enabled = !data.headers[index].enabled;
  } else {
    data.cookies[index].enabled = !data.cookies[index].enabled;
  }

  await saveData(data.headers, data.cookies);
  renderHeaders(data.headers);
  renderCookies(data.cookies);
  showStatus('Updated successfully');
}

// Handle remove
async function handleRemove(e) {
  const index = parseInt(e.target.dataset.index);
  const type = e.target.dataset.type;

  const data = await loadData();

  if (type === 'header') {
    data.headers.splice(index, 1);
  } else {
    data.cookies.splice(index, 1);
  }

  await saveData(data.headers, data.cookies);
  renderHeaders(data.headers);
  renderCookies(data.cookies);
  showStatus('Removed successfully');
}

// Add header
document.getElementById('addHeader').addEventListener('click', async () => {
  const name = document.getElementById('headerName').value.trim();
  const value = document.getElementById('headerValue').value.trim();

  if (!name || !value) {
    showStatus('Please fill in both fields', 'error');
    return;
  }

  const data = await loadData();
  data.headers.push({ name, value, enabled: true });

  await saveData(data.headers, data.cookies);
  renderHeaders(data.headers);

  document.getElementById('headerName').value = '';
  document.getElementById('headerValue').value = '';
  showStatus('Header added successfully');
});

// Add cookie modifier
document.getElementById('addCookie').addEventListener('click', async () => {
  const name = document.getElementById('cookieName').value.trim();
  const append = document.getElementById('cookieAppend').value.trim();

  if (!name || !append) {
    showStatus('Please fill in both fields', 'error');
    return;
  }

  const data = await loadData();
  data.cookies.push({ name, append, enabled: true });

  await saveData(data.headers, data.cookies);
  renderCookies(data.cookies);

  document.getElementById('cookieName').value = '';
  document.getElementById('cookieAppend').value = '';
  showStatus('Cookie modifier added successfully');
});

// Enable all
document.getElementById('enableAll').addEventListener('click', async () => {
  const data = await loadData();
  data.headers.forEach(h => h.enabled = true);
  data.cookies.forEach(c => c.enabled = true);

  await saveData(data.headers, data.cookies);
  renderHeaders(data.headers);
  renderCookies(data.cookies);
  showStatus('All enabled');
});

// Disable all
document.getElementById('disableAll').addEventListener('click', async () => {
  const data = await loadData();
  data.headers.forEach(h => h.enabled = false);
  data.cookies.forEach(c => c.enabled = false);

  await saveData(data.headers, data.cookies);
  renderHeaders(data.headers);
  renderCookies(data.cookies);
  showStatus('All disabled');
});

// Clear all
document.getElementById('clearAll').addEventListener('click', async () => {
  if (confirm('Are you sure you want to clear all headers and cookie modifiers?')) {
    await saveData([], []);
    renderHeaders([]);
    renderCookies([]);
    showStatus('All cleared');
  }
});

// Initialize
async function init() {
  await loadCurrentSite();
  const data = await loadData();
  renderHeaders(data.headers);
  renderCookies(data.cookies);
}

init();
