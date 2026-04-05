import { chromium } from "playwright";
import { Defuddle } from "defuddle/node";
import { writeFile, mkdir, readFile } from "fs/promises";
import { dirname, join } from "path";

// ── Config ──────────────────────────────────────────────────────────
const OUTPUT_DIR = "./content";
const PROGRESS_FILE = "./progress.json";
const ERRORS_FILE = "./errors.json";
const SLEEP_MS = 2000; // delay between page fetches
const SITEMAP_URL = "https://www.rolex.com/api/sm/en-gb/sitemap.xml";
const RETAILER_SITEMAP_URL =
  "https://www.rolex.com/api/sm/en-gb/retailer-sitemap.xml";
const NAV_TIMEOUT = 30_000;
const MAX_RETRIES = 2;

// CLI flags
const SKIP_RETAILERS = process.argv.includes("--skip-retailers");
const ONLY_RETAILERS = process.argv.includes("--only-retailers");
const RETRY_ERRORS = process.argv.includes("--retry-errors");

// ── Helpers ─────────────────────────────────────────────────────────
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function urlToFilePath(url) {
  const u = new URL(url);
  let path = u.pathname.replace(/^\/en-gb\/?/, "").replace(/^\//, "");
  if (!path) path = "index";
  path = path.replace(/\/$/, "");
  return join(OUTPUT_DIR, ...path.split("/")) + ".md";
}

async function loadJson(file) {
  try {
    return JSON.parse(await readFile(file, "utf-8"));
  } catch {
    return [];
  }
}

async function saveJson(file, data) {
  await writeFile(file, JSON.stringify(data, null, 2));
}

// ── Fetch sitemap URLs via Playwright ───────────────────────────────
async function fetchSitemapUrls(page, sitemapUrl) {
  console.log(`Fetching sitemap: ${sitemapUrl}`);
  await page.goto(sitemapUrl, {
    waitUntil: "domcontentloaded",
    timeout: NAV_TIMEOUT,
  });
  await sleep(1000);

  const urls = await page.evaluate(() => {
    const locs = document.querySelectorAll("loc");
    return Array.from(locs).map((l) => l.textContent);
  });

  console.log(`  Found ${urls.length} URLs`);
  return urls;
}

// ── Scrape a single page ────────────────────────────────────────────
async function scrapePage(page, url, retries = MAX_RETRIES) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const resp = await page.goto(url, {
        waitUntil: "networkidle",
        timeout: NAV_TIMEOUT,
      });

      if (!resp || resp.status() !== 200) {
        throw new Error(`HTTP ${resp?.status() ?? "no response"}`);
      }

      await sleep(500);

      const html = await page.content();
      const result = await Defuddle(html, url, { markdown: true });

      const frontmatter = [
        "---",
        `title: ${JSON.stringify(result.title || "")}`,
        `description: ${JSON.stringify(result.description || "")}`,
        `source: ${JSON.stringify(url)}`,
        `language: ${JSON.stringify(result.language || "en")}`,
        `word_count: ${result.wordCount || 0}`,
        `scraped_at: ${JSON.stringify(new Date().toISOString())}`,
        "---",
        "",
      ].join("\n");

      return frontmatter + (result.content || "");
    } catch (err) {
      if (attempt < retries) {
        console.log(`  retry ${attempt + 1}...`);
        await sleep(SLEEP_MS * 2);
        continue;
      }
      throw err;
    }
  }
}

// ── Main ────────────────────────────────────────────────────────────
async function main() {
  const done = new Set(await loadJson(PROGRESS_FILE));
  const errors = await loadJson(ERRORS_FILE);
  const errorUrls = new Set(errors.map((e) => e.url));

  if (RETRY_ERRORS) {
    // Clear error URLs from "done" so they get retried
    for (const e of errors) done.delete(e.url);
    await saveJson(ERRORS_FILE, []);
    errorUrls.clear();
    console.log(`Retrying ${errors.length} previously failed URLs`);
  }

  console.log(`Resuming with ${done.size} already-scraped pages\n`);

  const browser = await chromium.launch({
    headless: false,
    args: ["--disable-blink-features=AutomationControlled"],
  });

  const ctx = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    viewport: { width: 1280, height: 800 },
  });

  const page = await ctx.newPage();

  // Collect URLs from sitemaps
  let allUrls = [];

  if (!ONLY_RETAILERS) {
    const mainUrls = await fetchSitemapUrls(page, SITEMAP_URL);
    allUrls.push(...mainUrls);
    await sleep(SLEEP_MS);
  }

  if (!SKIP_RETAILERS) {
    const retailerUrls = await fetchSitemapUrls(page, RETAILER_SITEMAP_URL);
    allUrls.push(...retailerUrls);
  }

  allUrls = [...new Set(allUrls)];
  const todo = allUrls.filter((u) => !done.has(u));

  console.log(
    `\nTotal: ${allUrls.length}  |  Done: ${done.size}  |  Remaining: ${todo.length}\n`
  );

  let successCount = 0;
  let failCount = 0;
  const newErrors = [...errors.filter((e) => !RETRY_ERRORS)];

  // Graceful shutdown
  let stopping = false;
  process.on("SIGINT", () => {
    if (stopping) process.exit(1);
    stopping = true;
    console.log("\n\nGraceful shutdown… saving progress.");
  });

  for (let i = 0; i < todo.length; i++) {
    if (stopping) break;

    const url = todo[i];
    const filePath = urlToFilePath(url);
    const shortUrl = url.replace("https://www.rolex.com/en-gb/", "");

    try {
      process.stdout.write(`[${i + 1}/${todo.length}] ${shortUrl} … `);

      const markdown = await scrapePage(page, url);

      const dir = dirname(filePath);
      await mkdir(dir, { recursive: true });
      await writeFile(filePath, markdown, "utf-8");

      done.add(url);
      successCount++;
      console.log(`✓ (${markdown.length} chars)`);

      if (successCount % 10 === 0) {
        await saveJson(PROGRESS_FILE, [...done]);
      }
    } catch (err) {
      failCount++;
      newErrors.push({ url, error: err.message, time: new Date().toISOString() });
      console.log(`✗ ${err.message}`);
    }

    await sleep(SLEEP_MS);
  }

  // Save final state
  await saveJson(PROGRESS_FILE, [...done]);
  await saveJson(ERRORS_FILE, newErrors);

  console.log(
    `\nDone!  Success: ${successCount}  Failed: ${failCount}  Total scraped: ${done.size}`
  );
  await browser.close();
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
