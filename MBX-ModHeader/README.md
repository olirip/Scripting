# ModHeader - Request & Cookie Modifier

A Chrome extension that allows you to modify request headers and append values to cookies for any website you visit.

## Features

- **Modify Request Headers**: Add custom headers to all HTTP requests
- **Cookie Modifications**: Append values to existing cookies
- **Per-Site Control**: Easy management through popup interface
- **Enable/Disable**: Toggle headers and cookie modifications on/off
- **Persistent Storage**: Configurations are saved and persist across browser sessions

## Installation

### Creating Icons (Required)

1. Open `create-icons.html` in your browser
2. Right-click each canvas and save as:
   - First canvas → `icon16.png`
   - Second canvas → `icon48.png`
   - Third canvas → `icon128.png`
3. Save all three icons in the extension directory

### Loading the Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right corner)
3. Click "Load unpacked"
4. Select the extension directory (MBX-ModHeader)
5. The extension icon should appear in your toolbar

## Usage

### Adding Request Headers

1. Click the ModHeader extension icon in your toolbar
2. Under "Request Headers" section:
   - Enter the header name (e.g., `X-Custom-Header`)
   - Enter the header value (e.g., `CustomValue`)
   - Click "Add Header"
3. The header will now be added to all requests

### Modifying Cookies

1. Click the ModHeader extension icon
2. Under "Cookie Modifications" section:
   - Enter the cookie name you want to modify
   - Enter the value you want to append
   - Click "Add Cookie Modifier"
3. The extension will append the specified value to that cookie

### Managing Modifications

- **Enable/Disable Individual**: Click the toggle button on any header or cookie modifier
- **Enable All**: Click "Enable All" to activate all modifications
- **Disable All**: Click "Disable All" to deactivate all modifications
- **Remove**: Click "Remove" to delete a specific modification
- **Clear All**: Click "Clear All" to remove all headers and cookie modifiers

## How It Works

### Request Headers

The extension uses Chrome's `declarativeNetRequest` API to modify request headers before they are sent. This is efficient and works for all request types (XHR, fetch, images, etc.).

### Cookie Modifications

The extension modifies cookies using two approaches:
1. **Content Script Injection**: Injects code into pages to modify cookies via `document.cookie`
2. **Chrome Cookies API**: Uses the `chrome.cookies` API to read and update cookie values

## Permissions

The extension requires the following permissions:

- `declarativeNetRequest`: To modify request headers
- `declarativeNetRequestWithHostAccess`: To apply modifications to all hosts
- `storage`: To save configurations
- `cookies`: To read and modify cookies
- `activeTab`: To get current tab information
- `tabs`: To inject scripts for cookie modification
- `<all_urls>`: To work on any website

## Use Cases

- **Testing**: Add authentication headers for API testing
- **Development**: Override headers for local development
- **Debugging**: Modify cookies to test different user states
- **Security Testing**: Test header-based security mechanisms
- **Analytics**: Append tracking data to cookies

## Notes

- All modifications apply globally to all websites
- Cookie modifications work best on cookies that already exist
- Some cookies may be protected by HttpOnly flag and cannot be modified via JavaScript
- The extension respects Chrome's security policies and cannot modify certain internal pages

## Troubleshooting

If headers or cookies aren't being modified:

1. Check that the extension is enabled in `chrome://extensions/`
2. Verify the modifications are enabled (green toggle button)
3. Refresh the page after making changes
4. Check the browser console for any error messages
5. Some secure cookies may not be modifiable due to browser security policies

## License

MIT License - Feel free to use and modify as needed.
