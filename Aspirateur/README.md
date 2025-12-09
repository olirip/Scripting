# Aspirateur - Website Downloader

Download complete websites from sitemaps for offline browsing.

## Features

- Parse XML sitemaps (including sitemap indexes)
- Download all pages from a website
- Download assets (CSS, JavaScript, images)
- Convert absolute URLs to relative for offline browsing
- Progress bar with live updates
- Automatic retry on failures
- Respects rate limiting with configurable delays
- Creates an index page for easy navigation

## Installation

```bash
cd Aspirateur
npm install
```

## Usage

Basic usage:

```bash
node aspirateur.js https://example.com/sitemap.xml
```

With options:

```bash
node aspirateur.js https://example.com/sitemap.xml -o ./my-site -d 1000
```

### Command Line Options

- `--output, -o <dir>` - Output directory (default: `./downloaded-site`)
- `--delay, -d <ms>` - Delay between requests in milliseconds (default: `500`)
- `--no-assets` - Skip downloading CSS, JS, and images
- `--help, -h` - Show help message

## Examples

Download a website to a custom directory:

```bash
node aspirateur.js https://docs.example.com/sitemap.xml --output ./docs-offline
```

Download with slower rate (1 second between requests):

```bash
node aspirateur.js https://example.com/sitemap.xml --delay 1000
```

Download HTML only (no assets):

```bash
node aspirateur.js https://example.com/sitemap.xml --no-assets
```

## Serving Downloaded Sites

After downloading a site, you can serve it locally with Bun:

```bash
bun serve.js
```

This will start a local server at `http://localhost:3000` serving the downloaded site.

Options:
- `-p, --port <number>` - Port to listen on (default: 3000)
- `-d, --dir <path>` - Directory to serve (default: ./downloaded-site)

Examples:

```bash
# Serve on default port 3000
bun serve.js

# Serve on custom port
bun serve.js -p 8080

# Serve a specific directory
bun serve.js -d ./my-site -p 8080

# Or use npm script
npm run serve
```

## Output

The tool creates a directory structure that mirrors the website:

```
downloaded-site/
├── index.html          # Main index or generated page list
├── about/
│   └── index.html
├── blog/
│   ├── post-1/
│   │   └── index.html
│   └── post-2/
│       └── index.html
└── assets/
    ├── css/
    ├── js/
    └── images/
```

## How It Works

1. Fetches and parses the sitemap XML
2. Extracts all URLs from the sitemap
3. Downloads each page sequentially with rate limiting
4. Parses HTML and downloads referenced assets (images, CSS, JS)
5. Converts all internal URLs to relative paths
6. Saves files in a directory structure matching the site
7. Creates an index page for easy navigation

## Use as a Module

You can also use Aspirateur programmatically:

```javascript
import Aspirateur from './aspirateur.js';

const aspirateur = new Aspirateur('https://example.com/sitemap.xml', {
  outputDir: './my-site',
  delay: 500,
  downloadAssets: true,
  maxRetries: 3
});

await aspirateur.run();
```

## Notes

- The tool respects the same domain restriction - external assets are not downloaded
- Failed downloads are retried up to 3 times with exponential backoff
- A 500ms delay between requests is used by default to avoid overwhelming servers
- The tool is intended for personal archival purposes only

## License

MIT
