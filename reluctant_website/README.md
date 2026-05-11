# reluctant_website

Walk a website's `sitemap.xml` and save every page as a Markdown file using [Defuddle](https://defuddle.md/).

Pages are fetched through a real Chromium browser (Playwright), so sites behind **Cloudflare** or other JS challenges work out of the box.

## Install

```bash
npm install
npx playwright install chromium
```

## Usage

```bash
node scrape.mjs <site> [options]
```

`<site>` can be:

- a bare domain — `satisfyrunning.com`
- a subdomain — `blog.satisfyrunning.com`
- an origin URL — `https://satisfyrunning.com`
- a path-scoped URL — `https://satisfyrunning.com/blog` (only pages under `/blog` are kept)
- a direct sitemap URL — `https://satisfyrunning.com/sitemap.xml`
- a section sitemap URL — `https://satisfyrunning.com/blog/sitemap.xml` (only pages under `/blog/`)

When no sitemap path is given, the script tries `/sitemap.xml`, then `/sitemap_index.xml`, then any `Sitemap:` line found in `/robots.txt`.

### Scoping

By default (`--scope auto`), discovered URLs are filtered to:

- the same hostname as `<site>`, **and**
- the path prefix of `<site>` (the directory containing the sitemap, when a sitemap URL is given, or the URL pathname otherwise).

This means `node scrape.mjs https://example.com/blog/sitemap.xml` only saves pages under `/blog/`, even if the sitemap also lists URLs from elsewhere on the site. Subdomains are filtered too — `blog.example.com` will not pull in `www.example.com` URLs that happen to appear in a shared sitemap.

Override with:

- `--scope host` — keep any URL on the same hostname (ignore the path prefix).
- `--scope all` (or `--all`) — disable filtering entirely.

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | unlimited | Stop after `N` pages (useful for smoke tests) |
| `--retry-errors` | off | Re-queue URLs from `<host>/_errors.json` |
| `--headed` (or `HEADLESS=0`) | headless | Run Chromium with a visible window |
| `--concurrency N` | 1 | Reserved (currently sequential) |
| `--scope auto\|host\|path\|all` | `auto` | How to filter URLs found in the sitemap |
| `--all` | off | Shortcut for `--scope all` |

### Examples

```bash
# Scrape an entire site
node scrape.mjs satisfyrunning.com

# Only the blog subdomain
node scrape.mjs blog.satisfyrunning.com

# Only pages under /blog/ (path-scoped)
node scrape.mjs https://satisfyrunning.com/blog

# A specific section sitemap — only pages it lists, scoped to its directory
node scrape.mjs https://satisfyrunning.com/blog/sitemap.xml

# Use a sitemap but keep every URL it lists (no scope filtering)
node scrape.mjs https://satisfyrunning.com/sitemap.xml --all

# Quick smoke test — first 5 pages only
node scrape.mjs satisfyrunning.com --limit 5

# Re-attempt previously failed URLs
node scrape.mjs satisfyrunning.com --retry-errors

# Run headed (helpful for debugging Cloudflare blocks)
node scrape.mjs satisfyrunning.com --headed
```

## Output

A folder is created next to the script, named after the site's hostname:

```
satisfyrunning.com/
├── index.md
├── products/
│   └── moth-shorts.md
├── collections/
│   └── shorts.md
├── blogs/
│   └── post-title.md
└── _errors.json        # only if any pages failed
```

Each Markdown file has YAML frontmatter:

```markdown
---
title: "Running apparel developed to unlock the High."
description: "Running apparel developed to unlock the High. ..."
source: "https://satisfyrunning.com/"
language: "en"
word_count: 390
scraped_at: "2026-05-10T14:50:24.113Z"
---

## DESERT RATS
...
```

## How it works

1. **Discover sitemaps** — tries `/sitemap.xml`, `/sitemap_index.xml`, and `robots.txt`.
2. **Walk recursively** — if a sitemap is a `<sitemapindex>`, fetch each child (depth capped at 5). Every `<url><loc>` from `<urlset>` documents is collected and de-duplicated.
3. **Scrape each page** — Playwright loads the URL (`waitUntil: "networkidle"`), waits past any Cloudflare interstitial, and hands the rendered HTML to `Defuddle(html, url, { markdown: true })`.
4. **Write Markdown** — file path mirrors the URL pathname; root → `index.md`.

## Resume & errors

- Pages whose `.md` file already exists are skipped on re-runs — re-running the same command picks up where the previous run stopped.
- Any URL that fails (HTTP error, timeout, etc.) is appended to `<host>/_errors.json` with the reason and timestamp.
- `--retry-errors` re-queues those URLs and resets the error file.
- `Ctrl+C` triggers a graceful shutdown — failed URLs are still saved to `_errors.json`.

## Troubleshooting

- **Cloudflare keeps blocking you.** Re-run with `--headed` (or `HEADLESS=0 node scrape.mjs ...`). A visible browser session is harder to fingerprint than headless.
- **`No sitemap candidates found`.** The site doesn't expose a sitemap at the usual paths — pass the sitemap URL directly: `node scrape.mjs https://example.com/path/to/sitemap.xml`.
- **`HTTP 429` in `_errors.json`.** Increase the inter-request delay by editing `SLEEP_MS` near the top of `scrape.mjs`.

## Dependencies

- [`defuddle`](https://www.npmjs.com/package/defuddle) — HTML → Markdown extraction
- [`linkedom`](https://www.npmjs.com/package/linkedom) — DOM implementation used by `defuddle/node`
- [`playwright`](https://www.npmjs.com/package/playwright) — headless Chromium
