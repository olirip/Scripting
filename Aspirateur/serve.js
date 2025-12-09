#!/usr/bin/env bun

import { file, serve } from 'bun';
import path from 'path';
import { parseArgs } from 'util';

const { values } = parseArgs({
  args: process.argv.slice(2),
  options: {
    port: {
      type: 'string',
      short: 'p',
      default: '3000'
    },
    dir: {
      type: 'string',
      short: 'd',
      default: './downloaded-site'
    },
    help: {
      type: 'boolean',
      short: 'h',
      default: false
    }
  }
});

if (values.help) {
  console.log(`
Usage: bun serve.js [options]

Options:
  -p, --port <number>   Port to listen on (default: 3000)
  -d, --dir <path>      Directory to serve (default: ./downloaded-site)
  -h, --help            Show this help message

Examples:
  bun serve.js
  bun serve.js -p 8080
  bun serve.js -d ./my-site -p 8080
`);
  process.exit(0);
}

const port = parseInt(values.port, 10);
const directory = path.resolve(values.dir);

serve({
  port,
  async fetch(req) {
    const url = new URL(req.url);
    let pathname = url.pathname;

    // Decode URI components
    pathname = decodeURIComponent(pathname);

    // Security: prevent directory traversal
    if (pathname.includes('..')) {
      return new Response('Forbidden', { status: 403 });
    }

    // Remove leading slash and join with directory
    let filePath = path.join(directory, pathname);

    // If path is a directory, try index.html
    try {
      const stat = await Bun.file(filePath).exists();
      if (stat) {
        const bunFile = Bun.file(filePath);
        const fileStats = await bunFile.stat();

        if (fileStats && fileStats.isDirectory) {
          filePath = path.join(filePath, 'index.html');
        }
      }
    } catch (error) {
      // File doesn't exist, will be handled below
    }

    // Try to serve the file
    const bunFile = Bun.file(filePath);
    const exists = await bunFile.exists();

    if (!exists) {
      // Try with .html extension
      const htmlPath = filePath + '.html';
      const htmlFile = Bun.file(htmlPath);
      const htmlExists = await htmlFile.exists();

      if (htmlExists) {
        return new Response(htmlFile);
      }

      // Try index.html in the path
      const indexPath = path.join(filePath, 'index.html');
      const indexFile = Bun.file(indexPath);
      const indexExists = await indexFile.exists();

      if (indexExists) {
        return new Response(indexFile);
      }

      return new Response('Not Found', { status: 404 });
    }

    return new Response(bunFile);
  },
  error(error) {
    return new Response(`Server Error: ${error.message}`, { status: 500 });
  }
});

console.log(`\n🚀 Server running at http://localhost:${port}`);
console.log(`📁 Serving: ${directory}`);
console.log(`\nPress Ctrl+C to stop\n`);
