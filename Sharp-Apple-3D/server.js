import { file } from "bun";
import { join } from "path";

const PORT = process.env.PORT || 3000;
const ROOT_DIR = import.meta.dir;

const server = Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    let pathname = url.pathname;

    // Serve index.html for root path
    if (pathname === "/" || pathname === "/index.html") {
      const indexFile = file(join(ROOT_DIR, "index.html"));
      return new Response(indexFile, {
        headers: {
          "Content-Type": "text/html",
        },
      });
    }

    // Serve static files (output directory, etc.)
    try {
      const filePath = join(ROOT_DIR, pathname);
      const fileToServe = file(filePath);
      
      // Check if file exists
      if (await fileToServe.exists()) {
        return new Response(fileToServe);
      }
    } catch (error) {
      // File doesn't exist or error reading
    }

    // 404 for everything else
    return new Response("Not Found", { status: 404 });
  },
});

console.log(`Server running at http://localhost:${PORT}`);

