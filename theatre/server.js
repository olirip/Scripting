// Dev server for Bun with automatic bundling and file watching
import { build } from 'bun';
import { watch } from 'fs';

async function buildBundle() {
  try {
    const result = await build({
      entrypoints: ['src/index.jsx'],
      target: 'browser',
      format: 'esm',
      minify: false,
      outfile: 'bundle.js',
    });
    
    // Verify the file was created
    const bundleFile = Bun.file('bundle.js');
    if (await bundleFile.exists()) {
      console.log('✅ Bundle rebuilt at', new Date().toLocaleTimeString());
      return true;
    } else {
      console.error('❌ Bundle file was not created');
      return false;
    }
  } catch (error) {
    console.error('❌ Bundle error:', error);
    if (error.stack) {
      console.error(error.stack);
    }
    return false;
  }
}

// Initial build - wait for it to complete before starting server
console.log('🔨 Building initial bundle...');
const buildSuccess = await buildBundle();

if (!buildSuccess) {
  console.error('❌ Failed to build bundle. Exiting.');
  process.exit(1);
}

// Watch for file changes
console.log('👀 Watching src/ for changes...');
watch('src', { recursive: true }, async (event, filename) => {
  if (filename && (filename.endsWith('.jsx') || filename.endsWith('.js'))) {
    console.log(`🔄 ${filename} changed, rebuilding...`);
    await buildBundle();
  }
});

const server = Bun.serve({
  port: 3000,
  async fetch(req) {
    const url = new URL(req.url);
    
    // Serve index.html for root
    if (url.pathname === '/' || url.pathname === '/index.html') {
      const file = Bun.file('index.html');
      return new Response(file, {
        headers: { 'Content-Type': 'text/html' },
      });
    }
    
    // Serve bundled JavaScript
    if (url.pathname === '/bundle.js') {
      const file = Bun.file('bundle.js');
      if (await file.exists()) {
        const content = await file.text();
        return new Response(content, {
          headers: { 
            'Content-Type': 'application/javascript',
            'Cache-Control': 'no-cache',
          },
        });
      }
      console.error('⚠️  bundle.js not found when requested');
      return new Response('Bundle not found. Check server logs.', { status: 404 });
    }
    
    // Serve static assets (images, etc.)
    if (url.pathname.startsWith('/asset/')) {
      const filePath = url.pathname.slice(1); // Remove leading slash
      const file = Bun.file(filePath);
      if (await file.exists()) {
        // Determine content type based on file extension
        let contentType = 'application/octet-stream';
        if (filePath.endsWith('.jpg') || filePath.endsWith('.jpeg')) {
          contentType = 'image/jpeg';
        } else if (filePath.endsWith('.png')) {
          contentType = 'image/png';
        } else if (filePath.endsWith('.gif')) {
          contentType = 'image/gif';
        } else if (filePath.endsWith('.webp')) {
          contentType = 'image/webp';
        }
        
        return new Response(file, {
          headers: { 
            'Content-Type': contentType,
            'Cache-Control': 'public, max-age=3600',
          },
        });
      }
    }
    
    return new Response('Not Found', { status: 404 });
  },
});

console.log(`🚀 Server running at http://localhost:${server.port}`);
console.log(`📦 Open http://localhost:${server.port} in your browser`);

