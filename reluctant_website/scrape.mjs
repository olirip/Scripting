#!/usr/bin/env node
import { chromium } from "playwright";
import { Defuddle } from "defuddle/node";
import { mkdir, writeFile, readFile, access } from "fs/promises";
import { dirname, join } from "path";

const NAV_TIMEOUT = 45_000;
const SLEEP_MS = 800;
const MAX_RETRIES = 1;
const MAX_SITEMAP_DEPTH = 5;
const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function parseArgs(argv) {
  const args = {
    site: null,
    concurrency: 1,
    limit: Infinity,
    retryErrors: false,
    headless: true,
    scope: "auto",
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--concurrency") args.concurrency = parseInt(argv[++i], 10) || 1;
    else if (a === "--limit") args.limit = parseInt(argv[++i], 10) || Infinity;
    else if (a === "--retry-errors") args.retryErrors = true;
    else if (a === "--headed" || a === "--no-headless") args.headless = false;
    else if (a === "--scope") args.scope = String(argv[++i] || "auto").toLowerCase();
    else if (a === "--all") args.scope = "all";
    else if (!a.startsWith("--") && !args.site) args.site = a;
  }
  if (process.env.HEADLESS === "0") args.headless = false;
  if (!["auto", "host", "path", "all"].includes(args.scope)) {
    console.warn(`Unknown --scope "${args.scope}", falling back to "auto"`);
    args.scope = "auto";
  }
  return args;
}

function normalizeSite(input) {
  let s = input.trim();
  if (!/^https?:\/\//i.test(s)) s = "https://" + s;
  const u = new URL(s);
  const hasSitemapPath = /sitemap[^/]*\.xml$/i.test(u.pathname);
  // Path prefix used to scope discovered URLs. For a sitemap URL we use the
  // directory containing the sitemap; for a regular URL we use its pathname
  // (with a trailing slash so "/blog" matches "/blog/..." but not "/blogger").
  let pathPrefix = "/";
  if (hasSitemapPath) {
    const dir = u.pathname.replace(/[^/]*$/, "");
    pathPrefix = dir || "/";
  } else if (u.pathname && u.pathname !== "/") {
    pathPrefix = u.pathname.endsWith("/") ? u.pathname : u.pathname + "/";
  }
  return {
    origin: u.origin,
    host: u.hostname,
    hasSitemapPath,
    pathPrefix,
    full: u.toString(),
  };
}

function urlInScope(url, site, scope) {
  if (scope === "all") return true;
  let u;
  try {
    u = new URL(url);
  } catch {
    return false;
  }
  if (u.hostname !== site.host) return false;
  // "host" scope: any path on the same hostname.
  if (scope === "host") return true;
  // "path" or "auto": restrict to the path prefix when one was given.
  if (site.pathPrefix && site.pathPrefix !== "/") {
    const p = u.pathname.endsWith("/") ? u.pathname : u.pathname + "/";
    return p.startsWith(site.pathPrefix);
  }
  return true;
}

async function fileExists(p) {
  try {
    await access(p);
    return true;
  } catch {
    return false;
  }
}

async function loadJson(file, fallback) {
  try {
    return JSON.parse(await readFile(file, "utf-8"));
  } catch {
    return fallback;
  }
}

async function saveJson(file, data) {
  await mkdir(dirname(file), { recursive: true });
  await writeFile(file, JSON.stringify(data, null, 2));
}

async function fetchXml(page, url) {
  const resp = await page.goto(url, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
  if (!resp) throw new Error(`no response from ${url}`);
  // Cloudflare interstitial mitigation
  const title = await page.title().catch(() => "");
  if (/just a moment|attention required/i.test(title)) {
    try {
      await page.waitForLoadState("networkidle", { timeout: 20_000 });
    } catch {}
  }
  // Most sitemap servers return XML wrapped in <pre> by the browser, or raw text.
  const xml = await page.evaluate(() => {
    const pre = document.querySelector("pre");
    if (pre && pre.textContent && pre.textContent.trim().startsWith("<")) return pre.textContent;
    return document.documentElement.outerHTML;
  });
  return xml;
}

function parseSitemapXml(xml) {
  // Returns { sitemaps: [...], pages: [...] }
  const sitemaps = [];
  const pages = [];
  const isIndex = /<sitemapindex[\s>]/i.test(xml);
  const locRegex = /<loc>\s*([^<\s][^<]*?)\s*<\/loc>/gi;
  let m;
  while ((m = locRegex.exec(xml))) {
    const loc = decodeXmlEntities(m[1].trim());
    if (isIndex) sitemaps.push(loc);
    else pages.push(loc);
  }
  return { sitemaps, pages };
}

function decodeXmlEntities(s) {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
}

async function discoverSitemapUrls(page, site) {
  const candidates = [];
  if (site.hasSitemapPath) {
    candidates.push(site.full);
  } else {
    candidates.push(site.origin + "/sitemap.xml");
    candidates.push(site.origin + "/sitemap_index.xml");
    // robots.txt fallback
    try {
      const resp = await page.goto(site.origin + "/robots.txt", { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
      if (resp && resp.ok()) {
        const txt = await page.evaluate(() => document.body?.innerText || "");
        for (const line of txt.split(/\r?\n/)) {
          const m = line.match(/^\s*sitemap:\s*(\S+)/i);
          if (m) candidates.push(m[1].trim());
        }
      }
    } catch {}
  }
  return [...new Set(candidates)];
}

async function walkSitemaps(page, seedUrls) {
  const visited = new Set();
  const allPages = new Set();
  const queue = seedUrls.map((u) => ({ url: u, depth: 0 }));
  while (queue.length) {
    const { url, depth } = queue.shift();
    if (visited.has(url)) continue;
    visited.add(url);
    if (depth > MAX_SITEMAP_DEPTH) {
      console.warn(`  depth cap reached, skipping ${url}`);
      continue;
    }
    let xml;
    try {
      console.log(`Sitemap: ${url}`);
      xml = await fetchXml(page, url);
    } catch (err) {
      console.warn(`  failed to fetch sitemap ${url}: ${err.message}`);
      continue;
    }
    const { sitemaps, pages } = parseSitemapXml(xml);
    if (sitemaps.length) console.log(`  -> ${sitemaps.length} child sitemap(s)`);
    if (pages.length) console.log(`  -> ${pages.length} page URL(s)`);
    for (const s of sitemaps) queue.push({ url: s, depth: depth + 1 });
    for (const p of pages) allPages.add(p);
  }
  return [...allPages];
}

function urlToFilePath(rootDir, url) {
  const u = new URL(url);
  let path = u.pathname.replace(/^\//, "").replace(/\/$/, "");
  if (!path) path = "index";
  // Sanitize path segments (strip query, fragment already gone)
  const segments = path.split("/").map((seg) => seg.replace(/[<>:"|?*]/g, "_"));
  return join(rootDir, ...segments) + ".md";
}

function buildFrontmatter(url, result) {
  const lines = [
    "---",
    `title: ${JSON.stringify(result.title || "")}`,
    `description: ${JSON.stringify(result.description || "")}`,
    `source: ${JSON.stringify(url)}`,
    `language: ${JSON.stringify(result.language || "")}`,
    `word_count: ${result.wordCount || 0}`,
    `scraped_at: ${JSON.stringify(new Date().toISOString())}`,
    "---",
    "",
  ];
  return lines.join("\n");
}

async function scrapePage(page, url) {
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const resp = await page.goto(url, { waitUntil: "networkidle", timeout: NAV_TIMEOUT });
      if (!resp) throw new Error("no response");
      const status = resp.status();
      if (status >= 400) throw new Error(`HTTP ${status}`);
      // Cloudflare wait
      const title = await page.title().catch(() => "");
      if (/just a moment|attention required/i.test(title)) {
        try {
          await page.waitForLoadState("networkidle", { timeout: 20_000 });
        } catch {}
      }
      const html = await page.content();
      const result = await Defuddle(html, url, { markdown: true });
      return buildFrontmatter(url, result) + (result.content || "");
    } catch (err) {
      if (attempt < MAX_RETRIES) {
        await sleep(SLEEP_MS * 2);
        continue;
      }
      throw err;
    }
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.site) {
    console.error("Usage: node scrape.mjs <site> [--concurrency N] [--limit N] [--retry-errors] [--headed]");
    process.exit(1);
  }
  const site = normalizeSite(args.site);
  // Pick output dir: hostname, plus a sanitized path slug when the user scoped
  // the run to a subpath (e.g. /blog → satisfyrunning.com/blog).
  let rootDir = `./${site.host}`;
  if (args.scope !== "all" && args.scope !== "host" && site.pathPrefix && site.pathPrefix !== "/") {
    const slug = site.pathPrefix.replace(/^\/|\/$/g, "").replace(/[<>:"|?*\/]/g, "_");
    if (slug) rootDir = `./${site.host}/${slug}`;
  }
  const errorsFile = join(rootDir, "_errors.json");

  await mkdir(rootDir, { recursive: true });
  console.log(`Output: ${rootDir}`);

  const browser = await chromium.launch({
    headless: args.headless,
    args: ["--disable-blink-features=AutomationControlled"],
  });
  const context = await browser.newContext({
    userAgent: UA,
    viewport: { width: 1280, height: 800 },
  });
  const page = await context.newPage();

  try {
    const seeds = await discoverSitemapUrls(page, site);
    if (!seeds.length) {
      console.error("No sitemap candidates found.");
      process.exit(2);
    }
    let urls = await walkSitemaps(page, seeds);
    urls = [...new Set(urls)];
    const totalDiscovered = urls.length;
    if (args.scope !== "all") {
      const before = urls.length;
      urls = urls.filter((u) => urlInScope(u, site, args.scope));
      const dropped = before - urls.length;
      if (dropped) {
        const scopeDesc =
          args.scope === "host"
            ? `host ${site.host}`
            : site.pathPrefix && site.pathPrefix !== "/"
            ? `${site.host}${site.pathPrefix}`
            : `host ${site.host}`;
        console.log(`Filtered ${dropped} URL(s) outside scope (${scopeDesc})`);
      }
    }
    console.log(`\nDiscovered ${urls.length} unique page URL(s) (of ${totalDiscovered} found)`);

    // Resume: keep URLs whose output file doesn't exist
    let todo = [];
    for (const u of urls) {
      const fp = urlToFilePath(rootDir, u);
      if (!(await fileExists(fp))) todo.push(u);
    }
    const skipped = urls.length - todo.length;
    if (skipped) console.log(`Skipping ${skipped} already-scraped page(s)`);

    // Optional: re-queue previously failed URLs
    let priorErrors = await loadJson(errorsFile, []);
    if (args.retryErrors && priorErrors.length) {
      const priorUrls = new Set(priorErrors.map((e) => e.url));
      todo = [...new Set([...todo, ...priorUrls])];
      priorErrors = [];
      console.log(`Retrying ${priorUrls.size} previously failed URL(s)`);
    }

    if (todo.length > args.limit) todo = todo.slice(0, args.limit);
    console.log(`Scraping ${todo.length} page(s)\n`);

    const newErrors = [...priorErrors];
    let ok = 0;
    let fail = 0;
    let stopping = false;
    process.on("SIGINT", () => {
      if (stopping) process.exit(1);
      stopping = true;
      console.log("\nGraceful shutdown… saving state.");
    });

    for (let i = 0; i < todo.length; i++) {
      if (stopping) break;
      const url = todo[i];
      const fp = urlToFilePath(rootDir, url);
      const short = url.replace(site.origin, "") || "/";
      process.stdout.write(`[${i + 1}/${todo.length}] ${short} … `);
      try {
        const md = await scrapePage(page, url);
        await mkdir(dirname(fp), { recursive: true });
        await writeFile(fp, md, "utf-8");
        ok++;
        console.log(`✓ (${md.length} chars)`);
      } catch (err) {
        fail++;
        newErrors.push({ url, error: err.message, time: new Date().toISOString() });
        console.log(`✗ ${err.message}`);
      }
      await sleep(SLEEP_MS);
    }

    if (newErrors.length) await saveJson(errorsFile, newErrors);
    console.log(`\nDone. Success: ${ok}  Failed: ${fail}`);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
