# Debugging ModHeader Extension

## Quick Start Debugging

### Step 1: Check Extension is Loaded
1. Go to `chrome://extensions/`
2. Find "ModHeader - Request & Cookie Modifier"
3. Make sure it's **enabled** (toggle should be on)
4. Note: After any code changes, click the **reload icon** (circular arrow)

### Step 2: Use the Debug Page
1. Open [debug.html](debug.html) in Chrome
2. Click through each test button to see what's working
3. This will show you:
   - If extension is accessible
   - What configurations are stored
   - What rules are active
   - What headers are being sent

### Step 3: Check Background Service Worker Logs
1. Go to `chrome://extensions/`
2. Find "ModHeader" extension
3. Click **"service worker"** (blue link) - this opens the background script console
4. Look for console messages like:
   - "ModHeader extension installed"
   - "Rules updated: X headers, Y cookies"
   - Any error messages in red

### Step 4: Check Network Tab
1. Open DevTools on any website (F12 or Cmd+Option+I)
2. Go to **Network** tab
3. Reload the page
4. Click on any request
5. Check **Request Headers** section to see if your custom headers are there

## Common Issues and Solutions

### Issue 1: Extension Not Loading
**Symptoms:** Extension icon doesn't appear, or clicking it shows error

**Solutions:**
1. Make sure all icon files exist (`icon16.png`, `icon48.png`, `icon128.png`)
2. Check for errors in `chrome://extensions/` - click "Errors" button if available
3. Try removing and re-adding the extension

### Issue 2: Headers Not Being Added
**Symptoms:** Custom headers don't appear in Network tab

**Debug Steps:**
1. Open the extension popup and verify headers are listed
2. Check that headers are **enabled** (not grayed out)
3. Open background service worker console:
   - Go to `chrome://extensions/`
   - Click "service worker" link
   - Check for "Rules updated" messages
   - Run: `chrome.declarativeNetRequest.getDynamicRules().then(console.log)`
4. Check if you have the necessary permissions:
   ```javascript
   chrome.permissions.getAll().then(console.log)
   ```

**Common Causes:**
- Headers not enabled in UI
- Extension reloaded but rules not updated (click "Enable All" to refresh)
- Some sites (chrome://, file://) can't be modified due to Chrome security

### Issue 3: Cookies Not Being Modified
**Symptoms:** Cookie values don't change

**Debug Steps:**
1. Check DevTools Application tab → Cookies to see current cookie values
2. Some cookies can't be modified:
   - **HttpOnly cookies**: Can't be read/written by JavaScript
   - **Secure cookies**: Only work on HTTPS sites
   - **SameSite=Strict**: May not work across domains
3. Open background service worker console and check for errors
4. Try creating a test cookie first:
   ```javascript
   document.cookie = "test_cookie=original_value; path=/"
   ```
   Then add a cookie modifier for "test_cookie" in the extension

**Cookie Modification Limitations:**
- HttpOnly cookies cannot be accessed via JavaScript
- The extension needs the cookie to exist first (or it creates a new one)
- Cookie modifications happen on page load

### Issue 4: Changes Not Taking Effect
**Symptoms:** Made changes but nothing happens

**Solutions:**
1. **Reload the extension** after code changes:
   - Go to `chrome://extensions/`
   - Click reload icon on the extension
2. **Refresh the webpage** you're testing
3. Clear browser cache if needed (Cmd+Shift+R or Ctrl+Shift+R)

### Issue 5: Extension Crashes or Stops Working
**Symptoms:** Service worker becomes inactive, extension stops responding

**Solutions:**
1. Check service worker console for errors
2. Look for infinite loops or memory issues in background.js
3. Reload the extension
4. Check Chrome's task manager (Shift+Esc) for memory usage

## Manual Testing Commands

### Check Active Rules
Open background service worker console and run:
```javascript
chrome.declarativeNetRequest.getDynamicRules().then(rules => {
  console.log('Active rules:', rules);
});
```

### Check Stored Data
```javascript
chrome.storage.local.get(['headers', 'cookies'], data => {
  console.log('Stored config:', data);
});
```

### Check Cookies via API
```javascript
chrome.cookies.getAll({ url: 'https://example.com' }, cookies => {
  console.log('Cookies:', cookies);
});
```

### Force Rules Update
Open extension popup, then in popup console:
```javascript
chrome.runtime.sendMessage({ type: 'updateRules' });
```

## Testing Workflow

### Test 1: Simple Header Test
1. Open extension popup
2. Add header: `X-Test-Header` = `TestValue`
3. Open DevTools Network tab
4. Visit any HTTP/HTTPS website
5. Check request headers - should see `X-Test-Header: TestValue`

### Test 2: Cookie Append Test
1. Open DevTools console on any site
2. Create a test cookie: `document.cookie = "mycookie=original; path=/"`
3. Verify it exists: `document.cookie`
4. Open extension popup
5. Add cookie modifier: name=`mycookie`, append=`_appended`
6. Reload the page
7. Check cookie: `document.cookie` should show `mycookie=original_appended`

### Test 3: Using httpbin.org
1. Add header `X-Custom-Header` = `MyValue`
2. Visit https://httpbin.org/headers
3. You should see your custom header in the JSON response

## Viewing Different Consoles

Chrome extensions have multiple console contexts:

1. **Popup Console**:
   - Right-click extension icon → Inspect popup
   - See popup.js logs

2. **Background Service Worker Console**:
   - chrome://extensions/ → Click "service worker"
   - See background.js logs

3. **Content Script Console**:
   - Regular DevTools console on web page
   - See injected script logs

4. **Debug Page Console**:
   - Open debug.html → F12
   - See debug page logs

## Advanced Debugging

### Enable Verbose Logging
Add this to the top of background.js:
```javascript
const DEBUG = true;
const log = (...args) => DEBUG && console.log('[ModHeader]', ...args);
```

Then replace `console.log` with `log` throughout.

### Monitor All Web Requests
In background service worker console:
```javascript
chrome.webRequest.onBeforeSendHeaders.addListener(
  details => console.log('Request:', details),
  { urls: ['<all_urls>'] },
  ['requestHeaders']
);
```

### Check Permission Status
```javascript
chrome.permissions.getAll(permissions => {
  console.log('Permissions:', permissions);
});
```

## Still Not Working?

1. Check Chrome version (needs Chrome 88+)
2. Try in Incognito mode (must enable "Allow in incognito" in chrome://extensions/)
3. Check for conflicts with other extensions
4. Export your config and share it for troubleshooting
5. Check browser console for any CSP (Content Security Policy) errors

## Getting Help

When asking for help, include:
1. Chrome version
2. Error messages from service worker console
3. Output from debug.html tests
4. Specific header/cookie configuration you're trying
5. Target website URL
6. Screenshots of Network tab showing headers
