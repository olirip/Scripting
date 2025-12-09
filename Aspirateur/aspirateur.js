import axios from 'axios';
import * as cheerio from 'cheerio';
import { parseString } from 'xml2js';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import sanitize from 'sanitize-filename';
import cliProgress from 'cli-progress';
import colors from 'colors';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class Aspirateur {
  constructor(sitemapUrl, options = {}) {
    this.sitemapUrl = sitemapUrl;
    this.outputDir = options.outputDir || './downloaded-site';
    this.userAgent = options.userAgent || 'Mozilla/5.0 (compatible; Aspirateur/1.0)';
    this.delay = options.delay || 500; // ms between requests
    this.maxRetries = options.maxRetries || 3;
    this.downloadAssets = options.downloadAssets !== false; // download CSS, JS, images by default
    this.urls = [];
    this.downloaded = new Set();
    this.failed = [];
    this.progressBar = null;
  }

  async run() {
    console.log(colors.cyan('🧹 Aspirateur - Website Downloader'));
    console.log(colors.gray('================================\n'));

    try {
      // Parse sitemap
      console.log(colors.yellow(`📋 Parsing sitemap: ${this.sitemapUrl}`));
      await this.parseSitemap();
      console.log(colors.green(`✓ Found ${this.urls.length} URLs\n`));

      // Create output directory
      await fs.ensureDir(this.outputDir);

      // Download all pages
      this.progressBar = new cliProgress.SingleBar({
        format: 'Progress |' + colors.cyan('{bar}') + '| {percentage}% | {value}/{total} pages | {status}',
        barCompleteChar: '\u2588',
        barIncompleteChar: '\u2591',
        hideCursor: true
      });

      this.progressBar.start(this.urls.length, 0, { status: 'Starting...' });

      for (let i = 0; i < this.urls.length; i++) {
        const url = this.urls[i];
        this.progressBar.update(i, { status: `Downloading ${new URL(url).pathname}` });

        await this.downloadPage(url);

        if (i < this.urls.length - 1) {
          await this.sleep(this.delay);
        }
      }

      this.progressBar.update(this.urls.length, { status: 'Complete!' });
      this.progressBar.stop();

      // Summary
      console.log('\n' + colors.cyan('Summary:'));
      console.log(colors.green(`✓ Successfully downloaded: ${this.downloaded.size} pages`));

      if (this.failed.length > 0) {
        console.log(colors.red(`✗ Failed: ${this.failed.length} pages`));
        console.log(colors.gray('\nFailed URLs:'));
        this.failed.forEach(({ url, error }) => {
          console.log(colors.red(`  - ${url}: ${error}`));
        });
      }

      console.log(colors.cyan(`\n📁 Output directory: ${path.resolve(this.outputDir)}`));

      // Create index file
      await this.createIndexPage();
      console.log(colors.green(`✓ Created index.html - Open this file to browse offline\n`));

    } catch (error) {
      if (this.progressBar) {
        this.progressBar.stop();
      }
      console.error(colors.red(`\n✗ Error: ${error.message}`));
      throw error;
    }
  }

  async parseSitemap() {
    try {
      const response = await axios.get(this.sitemapUrl, {
        headers: { 'User-Agent': this.userAgent },
        timeout: 30000
      });

      const xml = response.data;

      return new Promise((resolve, reject) => {
        parseString(xml, (err, result) => {
          if (err) {
            reject(new Error(`Failed to parse sitemap: ${err.message}`));
            return;
          }

          // Handle regular sitemap
          if (result.urlset && result.urlset.url) {
            this.urls = result.urlset.url.map(entry => entry.loc[0]);
            resolve();
            return;
          }

          // Handle sitemap index
          if (result.sitemapindex && result.sitemapindex.sitemap) {
            const sitemapUrls = result.sitemapindex.sitemap.map(entry => entry.loc[0]);
            this.parseSitemapIndex(sitemapUrls).then(resolve).catch(reject);
            return;
          }

          reject(new Error('Invalid sitemap format'));
        });
      });
    } catch (error) {
      throw new Error(`Failed to fetch sitemap: ${error.message}`);
    }
  }

  async parseSitemapIndex(sitemapUrls) {
    const allUrls = [];

    for (const sitemapUrl of sitemapUrls) {
      try {
        const response = await axios.get(sitemapUrl, {
          headers: { 'User-Agent': this.userAgent },
          timeout: 30000
        });

        const urls = await new Promise((resolve, reject) => {
          parseString(response.data, (err, result) => {
            if (err) {
              reject(err);
              return;
            }

            if (result.urlset && result.urlset.url) {
              resolve(result.urlset.url.map(entry => entry.loc[0]));
            } else {
              resolve([]);
            }
          });
        });

        allUrls.push(...urls);
      } catch (error) {
        console.warn(colors.yellow(`⚠ Warning: Failed to parse sitemap ${sitemapUrl}: ${error.message}`));
      }
    }

    this.urls = allUrls;
  }

  async downloadPage(url, retries = 0) {
    try {
      const response = await axios.get(url, {
        headers: { 'User-Agent': this.userAgent },
        timeout: 30000,
        responseType: 'text'
      });

      const html = response.data;
      const $ = cheerio.load(html);

      // Download assets if enabled
      if (this.downloadAssets) {
        await this.downloadPageAssets($, url);
      }

      // Convert absolute URLs to relative
      this.convertUrlsToRelative($, url);

      // Save the page
      const filePath = this.getFilePath(url);
      await fs.ensureDir(path.dirname(filePath));
      await fs.writeFile(filePath, $.html(), 'utf-8');

      this.downloaded.add(url);

    } catch (error) {
      if (retries < this.maxRetries) {
        await this.sleep(1000 * (retries + 1));
        return this.downloadPage(url, retries + 1);
      }

      this.failed.push({ url, error: error.message });
    }
  }

  async downloadPageAssets($, pageUrl) {
    const baseUrl = new URL(pageUrl);
    const assetsDir = path.join(this.outputDir, 'assets');

    // Download images
    const images = $('img[src]');
    for (let i = 0; i < images.length; i++) {
      const img = images[i];
      const src = $(img).attr('src');
      if (src) {
        const assetUrl = this.resolveUrl(src, baseUrl);
        const localPath = await this.downloadAsset(assetUrl, assetsDir);
        if (localPath) {
          $(img).attr('src', this.getRelativePath(pageUrl, localPath));
        }
      }

      // Handle srcset attribute
      const srcset = $(img).attr('srcset');
      if (srcset) {
        const srcsetParts = srcset.split(',').map(s => s.trim());
        const newSrcset = [];

        for (const part of srcsetParts) {
          const [url, ...descriptor] = part.split(/\s+/);
          if (url) {
            const assetUrl = this.resolveUrl(url, baseUrl);
            const localPath = await this.downloadAsset(assetUrl, assetsDir);
            if (localPath) {
              const relativePath = this.getRelativePath(pageUrl, localPath);
              newSrcset.push([relativePath, ...descriptor].join(' '));
            } else {
              newSrcset.push(part);
            }
          }
        }

        if (newSrcset.length > 0) {
          $(img).attr('srcset', newSrcset.join(', '));
        }
      }
    }

    // Download CSS
    const stylesheets = $('link[rel="stylesheet"]');
    for (let i = 0; i < stylesheets.length; i++) {
      const link = stylesheets[i];
      const href = $(link).attr('href');
      if (href) {
        const assetUrl = this.resolveUrl(href, baseUrl);
        const localPath = await this.downloadAsset(assetUrl, assetsDir);
        if (localPath) {
          $(link).attr('href', this.getRelativePath(pageUrl, localPath));
        }
      }
    }

    // Download JavaScript
    const scripts = $('script[src]');
    for (let i = 0; i < scripts.length; i++) {
      const script = scripts[i];
      const src = $(script).attr('src');
      if (src) {
        const assetUrl = this.resolveUrl(src, baseUrl);
        const localPath = await this.downloadAsset(assetUrl, assetsDir);
        if (localPath) {
          $(script).attr('src', this.getRelativePath(pageUrl, localPath));
        }
      }
    }

    // Download other link assets (favicon, preload, etc.)
    const otherLinks = $('link[href]').not('[rel="stylesheet"]');
    for (let i = 0; i < otherLinks.length; i++) {
      const link = otherLinks[i];
      const href = $(link).attr('href');
      const rel = $(link).attr('rel');

      // Only download certain types of assets
      if (href && (rel === 'icon' || rel === 'shortcut icon' || rel === 'apple-touch-icon' || rel === 'preload' || rel === 'prefetch')) {
        const assetUrl = this.resolveUrl(href, baseUrl);
        const localPath = await this.downloadAsset(assetUrl, assetsDir);
        if (localPath) {
          $(link).attr('href', this.getRelativePath(pageUrl, localPath));
        }
      }
    }

    // Download background images and other URLs in inline styles
    $('[style]').each((i, elem) => {
      const style = $(elem).attr('style');
      if (style && style.includes('url(')) {
        const updatedStyle = style.replace(/url\(['"]?((?:https?:)?\/\/[^'")\s]+)['"]?\)/gi, (match, url) => {
          try {
            const assetUrl = this.resolveUrl(url.trim(), baseUrl);
            // Note: This is sync context, so we can't await here
            // These will need to be handled differently or accepted as external
            return match;
          } catch (error) {
            return match;
          }
        });
        $(elem).attr('style', updatedStyle);
      }
    });
  }

  async downloadAsset(url, assetsDir) {
    try {
      // Skip external assets (different domain)
      const sitemapDomain = new URL(this.sitemapUrl).hostname;
      const assetDomain = new URL(url).hostname;

      if (assetDomain !== sitemapDomain) {
        return null; // Keep external URLs as-is
      }

      // Generate local path
      const urlObj = new URL(url);
      const pathParts = urlObj.pathname.split('/').filter(p => p);
      const filename = pathParts.pop() || 'index';
      const localDir = path.join(assetsDir, ...pathParts);
      const localPath = path.join(localDir, sanitize(filename));

      // Skip if already downloaded
      if (await fs.pathExists(localPath)) {
        return localPath;
      }

      // Download asset
      const response = await axios.get(url, {
        headers: { 'User-Agent': this.userAgent },
        timeout: 15000,
        responseType: 'arraybuffer'
      });

      await fs.ensureDir(localDir);
      await fs.writeFile(localPath, response.data);

      return localPath;

    } catch (error) {
      // Silently fail for assets
      return null;
    }
  }

  convertUrlsToRelative($, pageUrl) {
    const baseUrl = new URL(pageUrl);

    // Convert internal links
    $('a[href]').each((i, elem) => {
      const href = $(elem).attr('href');
      if (href && !href.startsWith('#') && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
        const absoluteUrl = this.resolveUrl(href, baseUrl);
        const sitemapDomain = new URL(this.sitemapUrl).hostname;
        const linkDomain = new URL(absoluteUrl).hostname;

        if (linkDomain === sitemapDomain) {
          const localPath = this.getFilePath(absoluteUrl);
          const relativePath = this.getRelativePath(pageUrl, localPath);
          $(elem).attr('href', relativePath);
        }
      }
    });
  }

  resolveUrl(url, baseUrl) {
    try {
      // Handle protocol-relative URLs (//example.com/path)
      if (url.startsWith('//')) {
        url = baseUrl.protocol + url;
      }
      return new URL(url, baseUrl.href).href;
    } catch (error) {
      return url;
    }
  }

  getFilePath(url) {
    const urlObj = new URL(url);
    let pathname = urlObj.pathname;

    // Remove leading slash
    if (pathname.startsWith('/')) {
      pathname = pathname.substring(1);
    }

    // Add index.html for directory paths
    if (pathname === '' || pathname.endsWith('/')) {
      pathname += 'index.html';
    } else if (!path.extname(pathname)) {
      pathname += '/index.html';
    }

    return path.join(this.outputDir, pathname);
  }

  getRelativePath(fromUrl, toAbsolutePath) {
    const fromPath = this.getFilePath(fromUrl);
    const fromDir = path.dirname(fromPath);
    const relative = path.relative(fromDir, toAbsolutePath);
    // Normalize path separators for web and ensure forward slashes
    return relative.split(path.sep).join('/');
  }

  async createIndexPage() {
    const indexPath = path.join(this.outputDir, 'index.html');

    // If there's already an index.html from the site, don't overwrite
    if (await fs.pathExists(indexPath)) {
      return;
    }

    // Create a simple index page with links to all downloaded pages
    const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Downloaded Site Index</title>
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 { color: #333; }
        ul { list-style: none; padding: 0; }
        li { margin: 10px 0; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>📁 Downloaded Site</h1>
    <p>This site has been downloaded for offline browsing.</p>
    <h2>Pages (${this.downloaded.size})</h2>
    <ul>
        ${Array.from(this.downloaded).map(url => {
          const filePath = this.getFilePath(url);
          const relativePath = path.relative(this.outputDir, filePath);
          return `<li><a href="${relativePath.replace(/\\/g, '/')}">${url}</a></li>`;
        }).join('\n        ')}
    </ul>
</body>
</html>`;

    await fs.writeFile(indexPath, html, 'utf-8');
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// CLI Usage
if (process.argv[1] === __filename) {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    console.log(colors.cyan('\n🧹 Aspirateur - Website Downloader\n'));
    console.log('Usage:');
    console.log('  node aspirateur.js <sitemap-url> [options]\n');
    console.log('Options:');
    console.log('  --output, -o <dir>     Output directory (default: ./downloaded-site)');
    console.log('  --delay, -d <ms>       Delay between requests in ms (default: 500)');
    console.log('  --no-assets            Skip downloading CSS, JS, and images');
    console.log('  --help, -h             Show this help message\n');
    console.log('Example:');
    console.log('  node aspirateur.js https://example.com/sitemap.xml');
    console.log('  node aspirateur.js https://example.com/sitemap.xml -o ./my-site -d 1000\n');
    process.exit(0);
  }

  const sitemapUrl = args[0];
  const options = {};

  // Parse options
  for (let i = 1; i < args.length; i++) {
    const arg = args[i];

    if (arg === '--output' || arg === '-o') {
      options.outputDir = args[++i];
    } else if (arg === '--delay' || arg === '-d') {
      options.delay = parseInt(args[++i], 10);
    } else if (arg === '--no-assets') {
      options.downloadAssets = false;
    }
  }

  const aspirateur = new Aspirateur(sitemapUrl, options);
  aspirateur.run().catch(error => {
    console.error(colors.red(`\n✗ Fatal error: ${error.message}`));
    process.exit(1);
  });
}

export default Aspirateur;
