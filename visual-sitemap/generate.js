#!/usr/bin/env node
'use strict';

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

// ─── CONFIG ───────────────────────────────────────────────────────────────────
const CONFIG = {
  sitemapUrl: 'https://www.rolex.com/api/sm/sitemap.xml',
  outputFile: 'sitemap.html',
  maxDepth: 4,         // root(0) → section(1) → subsection(2) → page(3)
  maxLeafChildren: 12, // cap children per node, show "+N more" after
};

// ─── BRAND-SPECIFIC LABEL OVERRIDES ──────────────────────────────────────────
const LABEL_OVERRIDES = {
  'gmt-master-ii': 'GMT-Master II',
  'sea-dweller': 'Sea-Dweller',
  'deepsea': 'Deepsea',
  'sky-dweller': 'Sky-Dweller',
  'day-date': 'Day-Date',
  'lady-datejust': 'Lady-Datejust',
  'air-king': 'Air-King',
  'yacht-master': 'Yacht-Master',
  'datejust': 'Datejust',
  'submariner': 'Submariner',
  'daytona': 'Daytona',
  'explorer': 'Explorer',
  'milgauss': 'Milgauss',
  '1908': '1908',
  'cellini': 'Cellini',
  'oyster-perpetual': 'Oyster Perpetual',
  'land-dweller': 'Land-Dweller',
  'cpo': 'Certified Pre-Owned',
  'rolex': 'Rolex.com',
  'watchmaking': 'Watchmaking',
  'perpetual-initiatives': 'Perpetual Initiatives',
  'rolex-and-sports': 'Rolex & Sports',
  'about-rolex': 'About Rolex',
  'buying-a-rolex': 'Buying a Rolex',
  'rolex-family': 'Rolex Family',
  'watch-care-and-service': 'Watch Care & Service',
  'contact': 'Contact',
  'legal-notices': 'Legal Notices',
  'impressum': 'Impressum',
  'sitemap': 'Sitemap',
  'wishlist': 'Wishlist',
  'search': 'Search',
  'cookie-policy': 'Cookie Policy',
  'privacy-notice': 'Privacy Notice',
};

// ─── ONE-OFF PATHS TO GROUP UNDER "OTHER" ─────────────────────────────────────
const OTHER_SLUGS = new Set([
  'search', 'wishlist', 'legal-notices', 'impressum', 'sitemap',
  'contact', 'cookie-policy', 'privacy-notice', 'error', 'not-found',
]);

// ─── FETCH WITH REDIRECT HANDLING ────────────────────────────────────────────
function fetchSitemap(sitemapUrl) {
  return new Promise((resolve, reject) => {
    const follow = (currentUrl, redirectCount) => {
      if (redirectCount > 10) return reject(new Error('Too many redirects'));
      const parsed = new URL(currentUrl);
      const lib = parsed.protocol === 'https:' ? https : http;
      const options = {
        hostname: parsed.hostname,
        port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
        path: parsed.pathname + parsed.search,
        method: 'GET',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/xml,application/xml,application/xhtml+xml,*/*',
          'Accept-Encoding': 'identity',
          'Accept-Language': 'en-US,en;q=0.9',
          'Cache-Control': 'no-cache',
        },
      };
      const req = lib.request(options, (res) => {
        if ([301, 302, 303, 307, 308].includes(res.statusCode) && res.headers.location) {
          const next = new URL(res.headers.location, currentUrl).href;
          console.log(`  ↪ Redirect ${res.statusCode} → ${next}`);
          res.resume();
          return follow(next, redirectCount + 1);
        }
        if (res.statusCode !== 200) {
          return reject(new Error(`HTTP ${res.statusCode} for ${currentUrl}`));
        }
        const chunks = [];
        res.on('data', c => chunks.push(c));
        res.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
        res.on('error', reject);
      });
      req.on('error', reject);
      req.setTimeout(30000, () => { req.destroy(); reject(new Error('Request timeout')); });
      req.end();
    };
    follow(sitemapUrl, 0);
  });
}

// ─── PARSE XML ───────────────────────────────────────────────────────────────
function parseXML(xmlString) {
  // Handle sitemap index (points to child sitemaps)
  const sitemapIndexLocs = [...xmlString.matchAll(/<sitemap>[\s\S]*?<loc>(.*?)<\/loc>/g)]
    .map(m => m[1].trim());

  if (sitemapIndexLocs.length > 0) {
    return { type: 'index', locs: sitemapIndexLocs };
  }

  // Regular sitemap
  const locs = [...xmlString.matchAll(/<loc>(.*?)<\/loc>/g)]
    .map(m => m[1].trim());

  return { type: 'urlset', locs };
}

// ─── STRIP DOMAIN AND NORMALIZE PATH ─────────────────────────────────────────
function normalizePath(rawUrl) {
  try {
    const parsed = new URL(rawUrl);
    let p = parsed.pathname.replace(/\/$/, '') || '/';
    // Remove language prefix like /en, /fr, /de etc.
    p = p.replace(/^\/[a-z]{2}(-[A-Z]{2})?(?=\/|$)/, '');
    return p || '/';
  } catch {
    return null;
  }
}

// ─── FORMAT LABEL ─────────────────────────────────────────────────────────────
function formatLabel(slug) {
  if (!slug || slug === '/') return 'Rolex.com';
  if (LABEL_OVERRIDES[slug]) return LABEL_OVERRIDES[slug];
  return slug
    .replace(/-/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

// ─── BUILD TREE FROM FLAT PATH LIST ──────────────────────────────────────────
function buildTree(paths, maxDepth) {
  const root = { slug: '', label: 'Rolex.com', path: '/', depth: 0, children: {}, isOther: false };
  const otherNode = { slug: 'other', label: 'Other', path: '/other', depth: 1, children: {}, isOther: true };
  let hasOther = false;

  for (const p of paths) {
    if (!p || p === '/') continue;
    const segments = p.split('/').filter(Boolean);

    // Check if first segment is an "other" one-off
    if (segments.length >= 1 && OTHER_SLUGS.has(segments[0])) {
      hasOther = true;
      const slug = segments[0];
      if (!otherNode.children[slug]) {
        otherNode.children[slug] = {
          slug,
          label: formatLabel(slug),
          path: '/' + slug,
          depth: 2,
          children: {},
        };
      }
      continue;
    }

    // Insert into main tree up to maxDepth
    let node = root;
    for (let i = 0; i < Math.min(segments.length, maxDepth); i++) {
      const slug = segments[i];
      if (!node.children[slug]) {
        node.children[slug] = {
          slug,
          label: formatLabel(slug),
          path: '/' + segments.slice(0, i + 1).join('/'),
          depth: i + 1,
          children: {},
        };
      }
      node = node.children[slug];
    }
  }

  if (hasOther) {
    root.children['other'] = otherNode;
  }

  return root;
}

// ─── PRUNE TREE ───────────────────────────────────────────────────────────────
function pruneTree(node, maxLeafChildren) {
  const childValues = Object.values(node.children);
  for (const child of childValues) {
    pruneTree(child, maxLeafChildren);
  }

  // Never prune the root (depth 0) — all top-level sections must be visible
  if (node.depth === 0) return;

  const childArray = Object.values(node.children);
  if (childArray.length > maxLeafChildren) {
    const kept = childArray.slice(0, maxLeafChildren);
    const overflow = childArray.length - maxLeafChildren;
    const keptMap = {};
    for (const c of kept) keptMap[c.slug] = c;
    keptMap['__overflow__'] = {
      slug: '__overflow__',
      label: `+${overflow} more`,
      path: node.path + '/...',
      depth: node.depth + 1,
      children: {},
      isOverflow: true,
    };
    node.children = keptMap;
  }
}

// ─── FLATTEN TREE TO ARRAY ────────────────────────────────────────────────────
let _idCounter = 0;
function treeToArray(node, parentId = null, result = []) {
  const id = _idCounter++;
  result.push({
    id,
    parentId,
    label: node.label,
    path: node.path,
    depth: node.depth,
    isOverflow: !!node.isOverflow,
    isOther: !!node.isOther,
    childCount: Object.keys(node.children).length,
  });
  for (const child of Object.values(node.children)) {
    treeToArray(child, id, result);
  }
  return result;
}

// ─── RENDER HTML ─────────────────────────────────────────────────────────────
function renderHTML(nodes, meta) {
  const nodesJSON = JSON.stringify(nodes);
  const metaJSON = JSON.stringify(meta);

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rolex.com — Information Architecture</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: #fff;
    color: #111;
    min-height: 100vh;
  }

  header {
    padding: 32px 40px 24px;
    border-bottom: 1px solid #E5E7EB;
    display: flex;
    align-items: flex-end;
    gap: 40px;
    flex-wrap: wrap;
  }

  .header-text h1 {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.3px;
    color: #111;
  }
  .header-text p {
    font-size: 13px;
    color: #6B7280;
    margin-top: 4px;
  }

  .legend {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-left: auto;
    align-items: center;
  }
  .legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #6B7280;
  }
  .legend-swatch {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    flex-shrink: 0;
    border: 1px solid transparent;
  }

  .diagram-wrapper {
    overflow: auto;
    padding: 40px;
    cursor: grab;
    user-select: none;
  }
  .diagram-wrapper:active { cursor: grabbing; }

  #canvas {
    position: relative;
  }

  /* ── Node styles ── */
  .node {
    position: absolute;
    border-radius: 6px;
    border: 1px solid;
    padding: 0;
    cursor: default;
    transition: box-shadow 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
  }
  .node:hover {
    box-shadow: 0 2px 10px rgba(0,0,0,0.14);
    z-index: 10;
  }
  .node-inner {
    padding: 5px 8px;
    font-size: 11px;
    line-height: 1.3;
    word-break: break-word;
    hyphens: auto;
    width: 100%;
  }

  /* depth-0: Root */
  .node.d0 {
    background: #6B7280;
    border-color: #4B5563;
    color: #fff;
    font-weight: 600;
    font-size: 12px;
  }
  /* depth-1: Section */
  .node.d1 {
    background: #2563EB;
    border-color: #1D4ED8;
    color: #fff;
    font-weight: 600;
  }
  /* depth-2: Subsection */
  .node.d2 {
    background: #EFF6FF;
    border-color: #BFDBFE;
    color: #1D4ED8;
    font-weight: 500;
  }
  /* depth-3: Page */
  .node.d3 {
    background: #F9FAFB;
    border-color: #E5E7EB;
    color: #374151;
  }
  /* Overflow pill */
  .node.overflow {
    background: #F3F4F6;
    border-color: #E5E7EB;
    color: #9CA3AF;
    font-style: italic;
  }
  /* Other section */
  .node.other.d1 {
    background: #9CA3AF;
    border-color: #6B7280;
    color: #fff;
  }
</style>
</head>
<body>

<header>
  <div class="header-text">
    <h1>Rolex.com &mdash; Information Architecture</h1>
    <p>Visual sitemap generated from <code>sitemap.xml</code> &bull; <span id="meta-stats"></span></p>
  </div>
  <div class="legend">
    <div class="legend-item">
      <div class="legend-swatch" style="background:#6B7280;border-color:#4B5563"></div> Root
    </div>
    <div class="legend-item">
      <div class="legend-swatch" style="background:#2563EB;border-color:#1D4ED8"></div> Section
    </div>
    <div class="legend-item">
      <div class="legend-swatch" style="background:#EFF6FF;border-color:#BFDBFE"></div> Subsection
    </div>
    <div class="legend-item">
      <div class="legend-swatch" style="background:#F9FAFB;border-color:#E5E7EB"></div> Page
    </div>
  </div>
</header>

<div class="diagram-wrapper" id="wrapper">
  <div id="canvas">
    <svg id="lines-svg" style="position:absolute;top:0;left:0;pointer-events:none;overflow:visible;"></svg>
  </div>
</div>

<script>
(function() {
  const NODES = ${nodesJSON};
  const META  = ${metaJSON};

  // Column layout constants
  const COL_X       = [0, 116, 296, 492, 688];  // x-start per depth
  const COL_W       = [96, 152, 168, 168, 168];  // node width per depth
  const SLOT_HEIGHT = 28;    // vertical spacing between leaf slots
  const NODE_HEIGHT = 24;    // fixed node height
  const CANVAS_PAD  = 20;

  // ── Group nodes by parentId ──────────────────────────────────────────────
  function groupByParent(nodes) {
    const map = new Map();
    for (const n of nodes) {
      if (!map.has(n.parentId)) map.set(n.parentId, []);
      map.get(n.parentId).push(n);
    }
    return map;
  }

  // ── Assign Y slots (leaves get sequential, parents get midpoint) ─────────
  function assignYSlots(nodeId, byParent, nodesById) {
    const children = byParent.get(nodeId) || [];
    const node = nodesById.get(nodeId);
    if (children.length === 0) {
      // Leaf: will be assigned in order pass
      node._isLeaf = true;
      return;
    }
    for (const c of children) {
      assignYSlots(c.id, byParent, nodesById);
    }
  }

  function assignLeafSlots(nodeId, byParent, nodesById, counter) {
    const children = byParent.get(nodeId) || [];
    const node = nodesById.get(nodeId);
    if (children.length === 0) {
      node.ySlot = counter.val++;
      return;
    }
    let firstChild = Infinity, lastChild = -Infinity;
    for (const c of children) {
      assignLeafSlots(c.id, byParent, nodesById, counter);
      firstChild = Math.min(firstChild, c.ySlot !== undefined ? c.ySlot : (c._minSlot || 0));
      lastChild  = Math.max(lastChild,  c.ySlot !== undefined ? c.ySlot : (c._maxSlot || 0));
    }
    // For internal nodes, compute ySlot as midpoint of children range
    const slots = children.map(c => c.ySlot !== undefined ? c.ySlot : ((c._minSlot + c._maxSlot) / 2));
    node.ySlot = (Math.min(...slots) + Math.max(...slots)) / 2;
    node._minSlot = Math.min(...slots);
    node._maxSlot = Math.max(...slots);
  }

  // ── Compute layout ───────────────────────────────────────────────────────
  function computeLayout(nodes) {
    const nodesById = new Map(nodes.map(n => [n.id, n]));
    const byParent  = groupByParent(nodes);

    const roots = nodes.filter(n => n.parentId === null);
    for (const r of roots) {
      assignYSlots(r.id, byParent, nodesById);
      const counter = { val: 0 };
      assignLeafSlots(r.id, byParent, nodesById, counter);
    }

    for (const n of nodes) {
      const d = Math.min(n.depth, COL_X.length - 1);
      n.x = COL_X[d] + CANVAS_PAD;
      n.w = COL_W[d];
      n.y = Math.round(n.ySlot * SLOT_HEIGHT) + CANVAS_PAD;
      n.h = NODE_HEIGHT;
    }
    return nodes;
  }

  // ── Render SVG lines ─────────────────────────────────────────────────────
  function renderLines(nodes, svg) {
    const nodesById = new Map(nodes.map(n => [n.id, n]));
    const byParent  = groupByParent(nodes);
    const paths = [];
    const dots  = [];

    for (const n of nodes) {
      if (n.parentId === null) continue;
      const parent = nodesById.get(n.parentId);
      if (!parent) continue;

      // Parent right-center → child left-center
      const x1 = parent.x + parent.w;
      const y1 = parent.y + parent.h / 2;
      const x2 = n.x;
      const y2 = n.y + n.h / 2;
      const mx = x1 + 14;   // midpoint for horizontal segment

      if (Math.abs(y1 - y2) < 1) {
        // Straight horizontal
        paths.push(\`M\${x1},\${y1} H\${x2}\`);
      } else {
        paths.push(\`M\${x1},\${y1} H\${mx} V\${y2} H\${x2}\`);
        // Junction dot at the corner where we turn
        dots.push(\`<circle cx="\${mx}" cy="\${y2}" r="3" fill="#94A3B8"/>\`);
      }
    }

    svg.innerHTML =
      \`<path d="\${paths.join(' ')}" stroke="#CBD5E1" stroke-width="1.5" fill="none" stroke-linejoin="round"/>\` +
      dots.join('');
  }

  // ── Render node divs ─────────────────────────────────────────────────────
  function renderNodes(nodes, canvas) {
    const frag = document.createDocumentFragment();
    for (const n of nodes) {
      const div = document.createElement('div');
      div.className = 'node d' + n.depth
        + (n.isOverflow ? ' overflow' : '')
        + (n.isOther    ? ' other'    : '');
      div.style.cssText = [
        \`left:\${n.x}px\`,
        \`top:\${n.y}px\`,
        \`width:\${n.w}px\`,
        \`height:\${n.h}px\`,
      ].join(';');
      div.title = n.path;

      const inner = document.createElement('div');
      inner.className = 'node-inner';
      inner.textContent = n.label;
      div.appendChild(inner);
      frag.appendChild(div);
    }
    canvas.appendChild(frag);
  }

  // ── Main ─────────────────────────────────────────────────────────────────
  function main() {
    document.getElementById('meta-stats').textContent =
      META.totalUrls + ' URLs parsed · ' + META.totalNodes + ' nodes';

    const nodes = computeLayout(NODES);

    // Size the canvas
    const maxX = Math.max(...nodes.map(n => n.x + n.w)) + CANVAS_PAD;
    const maxY = Math.max(...nodes.map(n => n.y + n.h)) + CANVAS_PAD;
    const canvas = document.getElementById('canvas');
    canvas.style.width  = maxX + 'px';
    canvas.style.height = maxY + 'px';

    const svg = document.getElementById('lines-svg');
    svg.setAttribute('width', maxX);
    svg.setAttribute('height', maxY);

    renderLines(nodes, svg);
    renderNodes(nodes, canvas);

    // ── Pan support ───────────────────────────────────────────────────────
    const wrapper = document.getElementById('wrapper');
    let isPanning = false, startX, startY, scrollLeft, scrollTop;
    wrapper.addEventListener('mousedown', e => {
      if (e.target.classList.contains('node')) return;
      isPanning = true;
      startX = e.pageX - wrapper.offsetLeft;
      startY = e.pageY - wrapper.offsetTop;
      scrollLeft = wrapper.scrollLeft;
      scrollTop  = wrapper.scrollTop;
    });
    window.addEventListener('mouseup', () => { isPanning = false; });
    wrapper.addEventListener('mousemove', e => {
      if (!isPanning) return;
      e.preventDefault();
      wrapper.scrollLeft = scrollLeft - (e.pageX - wrapper.offsetLeft - startX);
      wrapper.scrollTop  = scrollTop  - (e.pageY - wrapper.offsetTop  - startY);
    });
  }

  document.addEventListener('DOMContentLoaded', main);
})();
</script>
</body>
</html>`;
}

// ─── MAIN ─────────────────────────────────────────────────────────────────────
async function main() {
  console.log('Rolex.com Visual Sitemap Generator');
  console.log('=====================================');
  console.log(`Fetching: ${CONFIG.sitemapUrl}`);

  let allPaths = [];

  try {
    const xml = await fetchSitemap(CONFIG.sitemapUrl);
    console.log(`  ✓ Fetched ${xml.length} bytes`);

    const parsed = parseXML(xml);

    if (parsed.type === 'index') {
      console.log(`  ✓ Sitemap index found with ${parsed.locs.length} child sitemaps`);
      for (const childUrl of parsed.locs) {
        console.log(`  Fetching child: ${childUrl}`);
        try {
          const childXml = await fetchSitemap(childUrl);
          const childParsed = parseXML(childXml);
          const childPaths = childParsed.locs
            .map(normalizePath)
            .filter(p => p !== null && p !== '/');
          allPaths.push(...childPaths);
          console.log(`    ✓ ${childPaths.length} URLs`);
        } catch (e) {
          console.warn(`    ✗ Failed: ${e.message}`);
        }
      }
    } else {
      const paths = parsed.locs
        .map(normalizePath)
        .filter(p => p !== null && p !== '/');
      allPaths = paths;
    }
  } catch (err) {
    console.error(`  ✗ Fetch failed: ${err.message}`);
    console.log('\nUsing fallback sample data for demonstration...');
    allPaths = [
      '/watches', '/watches/submariner', '/watches/submariner/features',
      '/watches/datejust', '/watches/datejust/features', '/watches/datejust/models',
      '/watches/day-date', '/watches/day-date/features',
      '/watches/gmt-master-ii', '/watches/gmt-master-ii/features',
      '/watches/daytona', '/watches/daytona/features',
      '/watches/sky-dweller', '/watches/sky-dweller/features',
      '/watches/explorer', '/watches/explorer/features',
      '/watches/air-king', '/watches/air-king/features',
      '/watches/sea-dweller', '/watches/sea-dweller/features',
      '/watches/deepsea', '/watches/deepsea/features',
      '/watches/yacht-master', '/watches/yacht-master/features',
      '/watches/lady-datejust', '/watches/lady-datejust/features',
      '/watches/oyster-perpetual', '/watches/oyster-perpetual/features',
      '/watches/1908', '/watches/1908/features',
      '/watchmaking', '/watchmaking/excellence', '/watchmaking/materials',
      '/watchmaking/1905', '/watchmaking/movement',
      '/rolex-and-sports', '/rolex-and-sports/golf', '/rolex-and-sports/tennis',
      '/rolex-and-sports/yachting', '/rolex-and-sports/motor-sport',
      '/rolex-and-sports/equestrianism', '/rolex-and-sports/ski',
      '/perpetual-initiatives', '/perpetual-initiatives/arts',
      '/perpetual-initiatives/planet', '/perpetual-initiatives/ocean',
      '/about-rolex', '/about-rolex/company', '/about-rolex/sustainable-development',
      '/buying-a-rolex', '/buying-a-rolex/cpo', '/buying-a-rolex/experience',
      '/watch-care-and-service', '/watch-care-and-service/maintenance',
      '/watch-care-and-service/authenticity', '/watch-care-and-service/water-resistance',
      '/rolex-family', '/rolex-family/tennis', '/rolex-family/golf',
      '/rolex-family/motorsport', '/rolex-family/ski',
      '/search', '/wishlist', '/legal-notices', '/impressum',
    ];
  }

  // Deduplicate
  allPaths = [...new Set(allPaths)];
  console.log(`\n✓ Total unique paths: ${allPaths.length}`);

  // Build tree
  console.log('Building tree...');
  _idCounter = 0;
  const root = buildTree(allPaths, CONFIG.maxDepth);

  // Prune
  console.log('Pruning tree...');
  pruneTree(root, CONFIG.maxLeafChildren);

  // Flatten
  console.log('Flattening...');
  const nodes = treeToArray(root);
  console.log(`  ✓ ${nodes.length} nodes in diagram`);

  // Depth distribution
  const depthCounts = {};
  for (const n of nodes) {
    depthCounts[n.depth] = (depthCounts[n.depth] || 0) + 1;
  }
  console.log('  Depth distribution:', depthCounts);

  // Render HTML
  const html = renderHTML(nodes, {
    totalUrls: allPaths.length,
    totalNodes: nodes.length,
    generatedAt: new Date().toISOString(),
  });

  const outPath = path.resolve(CONFIG.outputFile);
  fs.writeFileSync(outPath, html, 'utf8');
  console.log(`\n✓ Written: ${outPath} (${(html.length / 1024).toFixed(1)} KB)`);
  console.log('\nOpen sitemap.html in your browser to view the diagram.');
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
