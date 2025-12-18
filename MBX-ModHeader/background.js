// Background service worker for ModHeader extension

// Enable debug logging
const log = (...args) => console.log('[ModHeader]', ...args);
const logError = (...args) => console.error('[ModHeader ERROR]', ...args);

// Prevent race conditions with debouncing
let updateTimeout = null;
let isUpdating = false;

function scheduleUpdateRules() {
  log('Scheduling rule update...');

  // Clear any pending update
  if (updateTimeout) {
    clearTimeout(updateTimeout);
  }

  // Schedule update after a short delay to batch multiple changes
  updateTimeout = setTimeout(() => {
    updateRules();
  }, 100);
}

// Listen for storage changes and update rules
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local') {
    log('Storage changed:', changes);
    // Ignore activeCookieModifiers changes (internal use only)
    if (changes.activeCookieModifiers && Object.keys(changes).length === 1) {
      return;
    }
    scheduleUpdateRules();
  }
});

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  log('Received message:', message);
  if (message.type === 'updateRules') {
    scheduleUpdateRules();
  }
});

// Initialize on install
chrome.runtime.onInstalled.addListener((details) => {
  log('Extension installed/updated:', details.reason);
  updateRules();
});

// Update declarativeNetRequest rules for headers
async function updateRules() {
  // Prevent concurrent updates
  if (isUpdating) {
    log('Update already in progress, skipping...');
    return;
  }

  isUpdating = true;
  try {
    log('Starting updateRules...');
    const data = await chrome.storage.local.get(['headers', 'cookies']);
    log('Loaded data from storage:', data);

    const headers = (data.headers || []).filter(h => h.enabled);
    const cookies = (data.cookies || []).filter(c => c.enabled);

    log('Enabled headers:', headers.length, headers);
    log('Enabled cookies:', cookies.length, cookies);

    // Get existing rules
    const existingRules = await chrome.declarativeNetRequest.getDynamicRules();
    const existingRuleIds = existingRules.map(rule => rule.id);
    log('Existing rules to remove:', existingRuleIds.length);

    // Create new rules for headers
    const rules = [];
    let ruleId = 1;

    headers.forEach(header => {
      log('Creating rule for header:', header.name, '=', header.value);
      rules.push({
        id: ruleId++,
        priority: 1,
        action: {
          type: 'modifyHeaders',
          requestHeaders: [
            {
              header: header.name,
              operation: 'set',
              value: header.value
            }
          ]
        },
        condition: {
          urlFilter: '*',
          resourceTypes: [
            'main_frame',
            'sub_frame',
            'stylesheet',
            'script',
            'image',
            'font',
            'object',
            'xmlhttprequest',
            'ping',
            'csp_report',
            'media',
            'websocket',
            'webtransport',
            'webbundle',
            'other'
          ]
        }
      });
    });

    // Update rules atomically (remove old and add new in single operation)
    const updateOptions = {
      removeRuleIds: existingRuleIds
    };

    if (rules.length > 0) {
      updateOptions.addRules = rules;
    }

    log('Updating rules:', 'removing', existingRuleIds.length, 'adding', rules.length);

    await chrome.declarativeNetRequest.updateDynamicRules(updateOptions);

    log('Successfully updated rules');

    // Verify rules were added
    const verifyRules = await chrome.declarativeNetRequest.getDynamicRules();
    log('Current active rules:', verifyRules.length, verifyRules);

    // Handle cookie modifications via webRequest (needs to intercept and modify)
    // Note: Cookie modifications are handled via content script injection
    if (cookies.length > 0) {
      log('Setting up cookie modifiers...');
      updateCookieModifiers(cookies);
    }

    log('✓ Rules update completed:', rules.length, 'headers,', cookies.length, 'cookies');
  } catch (err) {
    logError('Error in updateRules:', err);
  } finally {
    isUpdating = false;
    log('Update lock released');
  }
}

// Store cookie modifiers for content script access
async function updateCookieModifiers(cookies) {
  await chrome.storage.local.set({ activeCookieModifiers: cookies });
}

// Inject content script to modify cookies when page loads
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === 'loading' && tab.url && !tab.url.startsWith('chrome://')) {
    const data = await chrome.storage.local.get(['cookies']);
    const cookies = (data.cookies || []).filter(c => c.enabled);

    if (cookies.length > 0) {
      try {
        log('Injecting cookie modifier into tab:', tabId, tab.url);
        // Try to inject the content script
        await chrome.scripting.executeScript({
          target: { tabId: tabId },
          func: modifyCookies,
          args: [cookies],
          world: 'MAIN'
        });
        log('Successfully injected cookie modifier');
      } catch (e) {
        logError('Could not inject into tab:', tabId, e.message);
      }
    }
  }
});

// Function that runs in the page context to modify cookies
function modifyCookies(cookieModifiers) {
  cookieModifiers.forEach(modifier => {
    try {
      // Get current cookies
      const cookies = document.cookie.split(';').reduce((acc, cookie) => {
        const [name, value] = cookie.trim().split('=');
        acc[name] = value || '';
        return acc;
      }, {});

      // Check if the cookie exists
      if (cookies[modifier.name] !== undefined) {
        const currentValue = cookies[modifier.name];
        const newValue = currentValue + modifier.append;

        // Set the modified cookie
        document.cookie = `${modifier.name}=${newValue}; path=/`;
        console.log(`ModHeader: Modified cookie "${modifier.name}"`);
      } else {
        // Cookie doesn't exist yet, create it with append value
        document.cookie = `${modifier.name}=${modifier.append}; path=/`;
        console.log(`ModHeader: Created cookie "${modifier.name}" with value "${modifier.append}"`);
      }
    } catch (e) {
      console.error('ModHeader: Error modifying cookie:', e);
    }
  });
}

// Alternative approach: Use chrome.cookies API to modify cookies
chrome.webRequest.onBeforeSendHeaders.addListener(
  async function(details) {
    const data = await chrome.storage.local.get(['cookies']);
    const cookieModifiers = (data.cookies || []).filter(c => c.enabled);

    if (cookieModifiers.length > 0 && details.url) {
      try {
        const url = new URL(details.url);

        for (const modifier of cookieModifiers) {
          // Get the cookie
          const cookies = await chrome.cookies.getAll({
            name: modifier.name,
            url: details.url
          });

          if (cookies.length > 0) {
            const cookie = cookies[0];
            const newValue = cookie.value + modifier.append;

            log('Modifying cookie via API:', modifier.name, 'on', details.url);

            // Remove old cookie
            await chrome.cookies.remove({
              url: details.url,
              name: modifier.name
            });

            // Set new cookie with appended value
            await chrome.cookies.set({
              url: details.url,
              name: modifier.name,
              value: newValue,
              domain: cookie.domain,
              path: cookie.path,
              secure: cookie.secure,
              httpOnly: cookie.httpOnly,
              sameSite: cookie.sameSite,
              expirationDate: cookie.expirationDate
            });

            log('Cookie modified successfully:', modifier.name);
          }
        }
      } catch (e) {
        logError('Error modifying cookies via API:', e);
      }
    }
  },
  { urls: ['<all_urls>'] },
  ['requestHeaders']
);

// Initialize
log('Initializing ModHeader extension...');
updateRules();
