// Lightweight static server for Bun to load the gyroscope demo on device
const root = new URL('./', import.meta.url);
const keyFile = Bun.file(new URL('./localhost+3-key.pem', import.meta.url));
const certFile = Bun.file(new URL('./localhost+3.pem', import.meta.url));

function resolvePath(pathname) {
  const decoded = decodeURIComponent(pathname);
  const normalized = decoded.replace(/(\.\.\/?)+/g, '');
  const finalPath = normalized.endsWith('/') ? normalized + 'index.html' : normalized;
  return new URL(finalPath.slice(1), root);
}

async function fetchHandler(request) {
  const url = new URL(request.url);
  const fileUrl = resolvePath(url.pathname);
  const file = Bun.file(fileUrl);

  if (!(await file.exists())) {
    return new Response('Not found', { status: 404 });
  }

  return new Response(file, {
    headers: { 'Content-Type': file.type || 'application/octet-stream' },
  });
}

const desiredPort = Number(process.env.PORT) || 4000;

function startServer(port) {
  return Bun.serve({
    port,
    fetch: fetchHandler,
    tls: {
      key: keyFile,
      cert: certFile,
    },
  });
}

let server;
try {
  server = startServer(desiredPort);
} catch (err) {
  if (err?.code === 'EADDRINUSE') {
    console.warn(`Port ${desiredPort} in use, falling back to a random port.`);
    server = startServer(0); // random available port
  } else {
    throw err;
  }
}

const scheme = server?.tls ? 'https' : 'http';
console.log(`Gyroscopique server running at ${scheme}://localhost:${server.port}`);
