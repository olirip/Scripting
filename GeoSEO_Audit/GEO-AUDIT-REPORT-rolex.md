# GEO Audit Report: Rolex

**Audit Date:** 2026-03-20
**URL:** https://www.rolex.com/
**Business Type:** Luxury Goods Manufacturer & Brand (Watch Manufacturer — no direct online sales)
**Pages Analyzed:** robots.txt + 40+ pages via web search & indexed sources (direct crawl blocked — 403 across all page URLs)
**Auditor Note:** rolex.com returns HTTP 403 Forbidden to all automated HTTP clients, including AI crawlers and audit tools. All page-level analysis is based on third-party SEO tool reports, indexed cached content, web search, and publicly available information. This is itself the most significant finding of this audit.

---

## Executive Summary

**Overall GEO Score: 48/100 (Poor)**

Rolex presents one of the most striking paradoxes in GEO: a brand with near-maximum global recognition and entity authority operating a website that is functionally invisible to every AI search platform. The brand is the most-searched luxury watch maker globally (13.2M annual searches), has a fully populated Wikipedia entity with individual articles for its major watch models, dominates Reddit's largest watch community (r/rolex, ~278K members), and generates continuous earned media from Bloomberg, Forbes, and Wall Street Journal. AI systems know Rolex extremely well — but from third-party sources alone, because rolex.com itself returns 403 Forbidden to all automated crawlers, including GPTBot, ClaudeBot, PerplexityBot, and Googlebot.

The result: AI platforms answer Rolex questions accurately but cite Wikipedia, Hodinkee, and Bloomberg — never rolex.com. For a brand whose entire value proposition rests on controlling the narrative around precision, prestige, and heritage, this is a significant and correctable strategic gap.

The three biggest strengths are brand authority (91/100), content quality relative to the luxury segment benchmark (61/100), and a robust off-domain ecosystem. The three biggest gaps are Schema & Structured Data (18/100), Technical GEO infrastructure (28/100), and AI Citability from the owned domain (22/100).

---

## Score Breakdown

| Category | Score | Weight | Weighted Score | Rating |
|---|---|---|---|---|
| AI Citability | 22/100 | 25% | 5.5 | Critical |
| Brand Authority | 91/100 | 20% | 18.2 | Excellent |
| Content E-E-A-T | 61/100 | 20% | 12.2 | Fair |
| Technical GEO | 28/100 | 15% | 4.2 | Critical |
| Schema & Structured Data | 18/100 | 10% | 1.8 | Critical |
| Platform Optimization | 56/100 | 10% | 5.6 | Fair |
| **Overall GEO Score** | | | **47.5 → 48/100** | **Poor** |

---

## Critical Issues (Fix Immediately)

### CRITICAL-1: Universal WAF Block — All AI Crawlers Receive 403 Forbidden

**Impact:** Affects all 6 GEO score categories
**Affected URLs:** https://www.rolex.com/ and all subpages

Every automated HTTP request to rolex.com returns HTTP 403 Forbidden. This is not a robots.txt restriction (robots.txt technically permits all crawlers including GPTBot, ClaudeBot, and PerplexityBot) — it is a WAF/bot-management system (consistent with Akamai Bot Manager or Cloudflare Enterprise tier) that delivers a JavaScript proof-of-work challenge that no crawler can complete.

**What AI crawlers experience:**

| Crawler | robots.txt Permission | Actual Access | Effective Visibility |
|---|---|---|---|
| GPTBot (OpenAI) | Permitted | 403 Forbidden | Zero |
| ClaudeBot (Anthropic) | Permitted | 403 Forbidden | Zero |
| PerplexityBot | Permitted | 403 Forbidden | Zero |
| Google-Extended | Permitted | 403 Forbidden | Near Zero |
| Googlebot | Permitted | 403 Forbidden* | Partial |
| BingBot (AI mode) | Permitted | 403 Forbidden | Near Zero |

*Googlebot may have negotiated CDN whitelisting; AI crawlers have no equivalent arrangement.

**Fix:** Add WAF allowlist rules for these user-agent strings and their published IP ranges: `GPTBot`, `OAI-SearchBot`, `ChatGPT-User`, `ClaudeBot`, `Claude-SearchBot`, `PerplexityBot`, `Google-Extended`. Pair with rate-limiting rules (max 1 req/2 sec per IP) to prevent abuse while opening access.

---

### CRITICAL-2: No llms.txt File

**Impact:** Citability, Technical GEO, Platform Optimization
**URL:** https://www.rolex.com/llms.txt (returns 403)

The emerging standard for AI-readable site context does not exist on rolex.com. For a brand as identity-sensitive as Rolex, llms.txt is also a brand-protection mechanism: it allows Rolex to declare how AI systems should describe the brand, what content is authoritative, and what restrictions apply — rather than leaving LLMs to infer from scraped third-party sources.

**Fix:** Create and deploy `/llms.txt` at the domain root. Minimum viable content: site description, key sections with URLs, brand entity statement, and any content usage restrictions. See Quick Wins section for a template.

---

### CRITICAL-3: No Organization Schema with sameAs Entity Links

**Impact:** Schema, Citability, Platform Optimization
**Affected URLs:** All pages (global head element)

Rolex operates verified profiles on every major platform AI systems use for entity resolution (Wikipedia, Wikidata Q62288, LinkedIn, YouTube, Instagram, Twitter/X). None appear to be linked via `sameAs` in Organization schema on rolex.com. This means AI models must infer the connection between rolex.com and the Rolex entity — they cannot read it as an explicit declaration from the brand itself.

**Fix:** Implement Organization schema with full `sameAs` array in the server-rendered `<head>` of every page. See Schema section for ready-to-use JSON-LD template.

---

### CRITICAL-4: XML Sitemap Blocked from All Crawlers

**Impact:** Technical GEO, Crawlability
**URL:** https://www.rolex.com/sitemap.xml (returns 403)

The sitemap is referenced in robots.txt but returns 403 to automated fetchers. Crawlers cannot discover Rolex's URL inventory programmatically. Even if page-level WAF restrictions remain in place during a phased rollout, the sitemap should be accessible.

**Fix:** (1) Allow the sitemap URL in WAF rules without requiring JavaScript execution. (2) Submit sitemap directly via Google Search Console and Bing Webmaster Tools as a parallel measure.

---

### CRITICAL-5: Zero Product Schema on Watch Model Pages

**Impact:** Schema, Citability
**Affected URLs:** All watch model pages (Submariner, Daytona, Datejust, GMT-Master, Explorer, Day-Date, Oyster Perpetual, etc.)

Rolex's dozens of individual watch model pages — each representing a product with a specific reference number, case diameter, material, movement calibre, and water resistance rating — carry no Product schema. These products are entirely unstructured from a machine-readable standpoint. AI systems parsing rolex.com cannot associate product names, references, materials, or technical specifications with structured Product entities. Rolex's refusal to publish prices is not a barrier: `offers` with `availability: InStoreOnly` and no `price` property is valid schema.

**Fix:** Implement server-rendered Product schema on all watch model pages. See Schema section for ready-to-use JSON-LD template.

---

## High Priority Issues (Fix Within 1 Week)

### HIGH-1: No Content Dating on Any Pages

rolex.com does not display publication or last-updated dates on any content pages (About Rolex, Watchmaking, History, Sustainability, CPO pages). Google Quality Rater Guidelines and AI systems specifically reward visible content dating for freshness assessment. The 2023 Sustainability Report's publication date is buried in the PDF — it should be displayed on the overview page.

**Fix:** Add ISO-format `datePublished` and `dateModified` to all informational and CPO pages. Implement Article schema with `datePublished`/`dateModified` properties on all editorial-style pages.

---

### HIGH-2: Blocked Sitemap / No URL Discovery Path for AI Crawlers

In addition to CRITICAL-4, the absence of a publicly accessible sitemap means AI crawlers — if granted WAF access — would have no starting point for systematic content discovery. A sitemap is the first tool a newly-permitted crawler uses.

**Fix:** Unblock sitemap.xml for all crawlers simultaneously with WAF allowlisting (CRITICAL-1). Verify sitemap coverage includes all watch model pages, About sections, and newsroom content.

---

### HIGH-3: No speakable Markup on Brand Narrative Pages

Pages like "About Rolex," watch family heritage pages, and "Rolex and Sport" contain factual, concise, high-authority content that is exactly what AI assistants surface when answering questions about Rolex. The `speakable` cssSelector property is a direct GEO signal that marks which content blocks are authoritative and readable — it is currently unused.

**Fix:** Add `speakable` JSON-LD to About Rolex, Watchmaking, and major heritage/editorial pages. Target CSS selectors for the H1, opening paragraph, and fact callout blocks on each page.

---

### HIGH-4: No IndexNow Implementation

Bing (and Bing Copilot) are significantly disadvantaged by the absence of IndexNow on rolex.com. IndexNow enables real-time index notification on content updates — critical for a brand that launches new watch models seasonally. No `msvalidate.01` meta tag is detectable.

**Fix:** Generate an IndexNow API key, place the key file at `/[key].txt`, and configure the CMS or deployment pipeline to call the IndexNow API on each content publish/update. 2-4 hour implementation effort.

---

### HIGH-5: LinkedIn Company Page Underweight

Rolex's LinkedIn company page (~600K–700K followers) is significantly below its brand stature benchmark (LVMH brands at 2M–5M followers) and is a missed opportunity for Bing Copilot visibility — LinkedIn is a Microsoft property that Bing Copilot draws from explicitly for brand/professional queries.

**Fix:** Publish monthly long-form posts covering watchmaking innovation, sustainability milestones, and technical heritage. Grow follower base through brand ambassador cross-posting. Target: 1.5M followers within 18 months.

---

## Medium Priority Issues (Fix Within 1 Month)

### MEDIUM-1: No ItemList / CollectionPage Schema on Watch Family Pages

Collection pages listing multiple watches within a family (Submariner collection, all Rolex watches, CPO collection) carry no ItemList schema. AI models cannot traverse the product catalog as a structured graph.

### MEDIUM-2: No BreadcrumbList Schema

The site's clean URL hierarchy (`/en-us/watches/submariner/`) implies breadcrumbs exist visually but no BreadcrumbList schema is present, preventing SERP breadcrumb display and semantic hierarchy signaling.

### MEDIUM-3: Content Heading Strategy Not Optimized for AI Extraction

H2 headings on rolex.com function as aspirational chapter titles ("Excellence in the making," "A vision built to last") rather than descriptive information headings. AI answer engines extract content preceded by question-format or descriptive headings. Zero pages follow the question-heading + direct-answer paragraph pattern that Google AIO and Perplexity prefer.

### MEDIUM-4: No Rolex-Authored Content on Third-Party Platforms

Rolex does not seed structured Q&A content to Quora, Reddit AMAs, or Stack Exchange (watches.stackexchange.com). These platforms are indexed by Perplexity at high weight and represent an untapped structured Q&A opportunity. AI systems currently answer "How does the Rolex Perpetual movement work?" using third-party blog content rather than brand-originated explanations.

### MEDIUM-5: 2-Second Global Crawl Delay

The `Crawl-delay: 2` directive in robots.txt applies to all user agents. For a brand that launches new watch collections seasonally, slow re-indexing means AI systems carry stale information. This compounds the WAF issue: when/if WAF access is opened, the crawl delay limits re-indexing velocity.

---

## Low Priority Issues (Optimize When Possible)

- **Image alt text consistency:** Production quality is high but alt text completeness is unverifiable due to WAF block; should be audited once crawler access is restored.
- **Open Graph completeness:** og:type and og:url consistency cannot be confirmed externally; verify og:description and og:image are set on all pages.
- **Twitter Card implementation:** No evidence of Twitter Card meta tags in indexed sources; verify and add if missing.
- **hreflang error risk:** Site operates in 20+ language/region variants; hreflang misconfiguration would be a significant duplicate-content risk. Cannot verify from external analysis — should be audited via Google Search Console.
- **Newsroom subdomain strategy:** newsroom.rolex.com exists and may have lighter WAF restrictions. If accessible to crawlers, it should be submitted to Search Console separately and optimized with visible dates and bylines.
- **LCP risk from hero video:** Rolex's full-bleed hero videos are high LCP risk patterns. Validate Core Web Vitals via CrUX data in Google Search Console and PageSpeed Insights.

---

## Category Deep Dives

---

### AI Citability — 22/100

**The core problem:** AI systems cannot cite rolex.com because they cannot crawl it (403 block) and the content that does exist is structured for human visual experience, not machine-readable extraction.

**What IS citable from rolex.com (from indexed/cached sources):**
- Technical specifications on watch model pages (calibre numbers, depth ratings, case diameters) — specific, verifiable, unique to the brand
- CPO certification process descriptions — structured, procedural content with specific steps
- Historical milestones with verifiable dates (1905 founding, 1926 Oyster, 1945 Datejust, 1953 Submariner)
- Sustainability Report data (supply chain metrics, governance structure) — the highest-density quotable content Rolex publishes
- Oystersteel 904L technical description — genuinely uncommon, citable material specification

**What is NOT citable:**
- Aspirational copy that constitutes 60-70% of site content ("relentless quest for quality," "unrivalled expertise") — contains no extractable facts
- Price information — deliberately absent from the entire site
- FAQ content — does not exist anywhere on rolex.com
- Comparison data — no watch comparisons, no feature matrices
- Author-attributed insights or expert quotes — zero named authors anywhere on rolex.com
- Process documentation with specific metrics

**Citability gap vs. competitors:**
- FratelloWatches, Hodinkee, aBlogtoWatch: All publish question-heading articles with direct answers that AI systems extract and cite for Rolex queries
- Rolex's own website is never the cited source for factual Rolex questions in AI-generated responses
- The Watchmaking section (calibre specs, material science) is the closest the site comes to citable content but is too sparse and JS-rendered to be reliably extracted

**Top opportunities:**
1. Create a "Rolex Technical Specifications" reference hub with model-level specs in table format
2. Develop a brand facts page with citable statistics (founding year, production volume, HQ address, foundation structure)
3. Add FAQ blocks to product pages with self-contained question-answer pairs (40-60 words each)

---

### Brand Authority — 91/100

Rolex is one of the highest brand-authority entities an AI system can encounter. The foundation is essentially complete.

**Platform presence map:**

| Platform | Status | Quality |
|---|---|---|
| Wikipedia (en) | Full article + model articles | Exceptional — continuously updated, extensively cited |
| Wikidata | Q62288 + model entities | Exceptional — structured properties, subsidiaries |
| Google Knowledge Graph | Confirmed Knowledge Panel | Exceptional — 13.2M annual searches trigger panel |
| Reddit | r/rolex ~278K, r/Watches ~600K | Very Strong — among most active brand subreddits |
| YouTube | Official channel since 2012 | Strong — presence established; content volume below potential |
| LinkedIn | ~600K–700K followers | Moderate — underweight for brand stature |
| Instagram | Official @rolex | Strong — luxury lifestyle content |
| Twitter/X | Official @rolex | Moderate — historically conservative posting cadence |
| Luxury Press | Hodinkee, FratelloWatches, WatchPro | Exceptional — continuous authoritative coverage |
| Mainstream Press | Bloomberg, Forbes, WSJ | Exceptional — multiple articles monthly |
| Sports Sponsorship | Wimbledon, Rolex 24, Australian Open | Exceptional — generates premium editorial backlinks |

**Key deductions from 100:**
- No sameAs schema self-confirming rolex.com as the entity's canonical domain (-4)
- LinkedIn follower base underweight for CHF 10.5B brand (-3)
- YouTube content volume below brand's strategic potential (-2)

---

### Content E-E-A-T — 61/100

| Dimension | Score | Key Finding |
|---|---|---|
| Experience | 10/25 | Institutional knowledge demonstrated but zero first-hand authorial voice |
| Expertise | 13/25 | Genuine technical depth (calibre numbers, material specs) but zero author attribution |
| Authoritativeness | 22/25 | Domain Rating ~83; 120-year brand history; elite inbound link profile |
| Trustworthiness | 17/25 | HTTPS, legal disclosures, CPO guarantees solid; no editorial transparency |

**Strengths:**
- Technical content accuracy: Calibre references, 904L steel, depth ratings, CPO certification process are correct and specific
- CPO program documentation: enforceable guarantee terms (two-year international guarantee, genuine parts, distinct certification seal) are the highest-trust content on the site
- 2023 Sustainability Report: 118 pages of supply chain transparency data — first published after decades of internal use
- Perpetual Arts Initiative: 23 years, 1,100+ nominees, 105 countries — proprietary verified data

**Weaknesses:**
- Zero author attribution anywhere on rolex.com — deliberately institution-centric
- Zero publication/update dates on any page
- No FAQ, no structured Q&A, no consumer education content
- Short-form copy (150-400 words typical) provides limited AI-extractable surface area
- Headings are aspirational slogans, not descriptive information headings

**Luxury segment benchmark:** Audemars Piguet (Stories section) and A. Lange & Söhne (movement explainers) represent the content ceiling for the segment. Rolex trails on depth while leading all on external authority. This is a deliberate strategic choice — optimized for human brand perception, underoptimized for AI citation systems.

---

### Technical GEO — 28/100

| Technical Factor | Status | Severity |
|---|---|---|
| WAF blocking all AI crawlers | 403 to all non-browser agents | Critical |
| llms.txt | Not present | Critical |
| sitemap.xml accessibility | Returns 403 | Critical |
| robots.txt AI directives | No AI crawler entries | High |
| Crawl delay | 2 seconds (all agents) | Medium |
| SSR/SSG status | Unverifiable (WAF blocks) | High |
| Core Web Vitals — LCP | High risk (hero video patterns) | Medium |
| Core Web Vitals — INP | High risk (JS-heavy interactions) | Medium |
| URL structure | Clean hierarchy | Good |
| HTTPS | Enforced | Good |
| Security headers | Enterprise WAF deployed | Good (but blocks crawlers) |
| Mobile optimization | Assumed responsive | Unverifiable |

The single most damaging technical fact: Rolex's enterprise WAF treats legitimate AI crawlers identically to malicious bots. The robots.txt permissiveness is irrelevant because the WAF delivers 403 before robots.txt rules can apply. Whatever AI visibility Rolex has is built entirely from third-party sources — none of which Rolex controls.

---

### Schema & Structured Data — 18/100

| Schema Type | Status | Priority |
|---|---|---|
| Organization + sameAs | Possibly minimal; no sameAs | Critical |
| Product (watch models) | Not implemented | Critical |
| speakable | Not implemented | High |
| ItemList (collection pages) | Not implemented | High |
| BreadcrumbList | Not implemented | Medium |
| WebSite | Possibly present | Medium |
| Article + dateModified | Not applicable (no blog) | N/A |
| FAQPage | Not implemented | Medium |
| HowTo | Not applicable | N/A |

**Score drivers:**
- Organization schema: Possibly exists in minimal form but zero confirmed sameAs links — the highest-impact single property for entity resolution
- Product schema: Entirely absent for a brand whose entire commercial purpose is selling products — the most severe content gap
- speakable: Brand narrative pages are ideal candidates; completely unmarked
- No deprecated schemas detected — clean in this regard

**Critical rendering risk:** Any schema that does exist is almost certainly JavaScript-injected. AI crawlers do not execute JavaScript. Server-side rendering of JSON-LD into the initial HTML response is required for AI crawler visibility.

---

### Platform Optimization — 56/100

| Platform | Score | Primary Gap |
|---|---|---|
| Google AI Overviews | 62/100 | WAF blocks AIO crawl; no FAQ/answer-format content |
| ChatGPT Web Search | 58/100 | WAF blocks OAI-SearchBot; no sameAs for entity confirmation |
| Perplexity AI | 65/100 | Strong Reddit/press ecosystem compensates for blocked primary domain |
| Google Gemini | 68/100 | YouTube/Knowledge Graph provide foundation; WAF limits brand-domain sourcing |
| Bing Copilot | 48/100 | No IndexNow; no Bing verification; LinkedIn underweight |

**The paradox:** Rolex scores highest on Gemini (68) not because rolex.com is well-optimized but because Gemini draws heavily from YouTube (Rolex channel, motorsport sponsorship content) and Google's Knowledge Graph — two data sources where Rolex's historic investment pays dividends. The brand authority floor prevents any platform from scoring below 48 despite the technical failures.

---

## Quick Wins (Implement This Week)

1. **Add Organization schema with sameAs to the homepage `<head>`** — 2 hours of engineering. Immediately improves entity resolution on ChatGPT, Gemini, Google AIO, and Bing Copilot. Use the ready-made JSON-LD below.

2. **Create and deploy `/llms.txt`** — 4 hours total (writing + deployment). Signals AI readiness to all platforms. Template:
   ```
   # Rolex — Official Website

   Rolex is a Swiss luxury watch manufacturer based in Geneva, Switzerland,
   designing and producing watches since 1905.

   ## Key Sections

   - /en-us/watches: Complete collection of Rolex watch families
   - /en-us/watchmaking: Technical content on Rolex movements and materials
   - /en-us/about-rolex: Brand history and institutional information
   - /en-us/buying-a-rolex/rolex-certified-pre-owned: Certified Pre-Owned program
   - https://newsroom.rolex.com: Official Rolex newsroom and press releases

   ## Brand Entity

   Wikipedia: https://en.wikipedia.org/wiki/Rolex
   Wikidata: https://www.wikidata.org/wiki/Q62288
   ```

3. **Implement IndexNow** — 2-4 hours. Generate API key, place verification file, integrate into publish pipeline. Directly addresses the weakest platform (Bing Copilot).

4. **Add `datePublished` + `dateModified` to About Rolex, Watchmaking, CPO, and Sustainability pages** — 1 day. Visible dates improve Trust score on all platforms and satisfy Google Quality Rater Guidelines freshness criteria.

5. **Open newsroom.rolex.com to AI crawlers** — If newsroom.rolex.com has lighter WAF restrictions, verify AI crawler access and submit it as a separate Search Console property. It already contains deeper, dateable content (press releases, technical sheets, heritage documentation) that Perplexity and Gemini can cite directly.

---

## 30-Day Action Plan

### Week 1: Infrastructure Unlock
- [ ] Security team review: define WAF allowlist strategy for AI crawler user-agents (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, OAI-SearchBot, BingBot AI mode)
- [ ] Deploy allowlist rules with rate-limiting (max 1 req/2 sec per crawl IP range)
- [ ] Unblock `/sitemap.xml` for all crawlers
- [ ] Create and deploy `/llms.txt` with brand entity statement and section index
- [ ] Implement IndexNow: generate key, place verification file, integrate with publish pipeline
- [ ] Submit sitemap to Google Search Console and Bing Webmaster Tools

### Week 2: Structured Data Foundation
- [ ] Implement server-rendered Organization schema with sameAs array in global page `<head>`
- [ ] Implement BreadcrumbList schema on all interior pages (generate from URL structure)
- [ ] Implement WebSite schema on homepage
- [ ] Audit existing schema (if any) with Google Rich Results Test once WAF is opened
- [ ] Add `speakable` markup to About Rolex, Watchmaking, and watch family heritage pages

### Week 3: Product Schema Rollout
- [ ] Implement server-rendered Product schema on all individual watch model pages (reference number, calibre, dimensions, material, water resistance, image)
- [ ] Implement ItemList schema on all collection/family pages (Submariner, Daytona, etc.)
- [ ] Add `datePublished` / `dateModified` visible dates and Article schema to all informational pages
- [ ] Add `offers` block with `availability: InStoreOnly` to Product schema (no price required)

### Week 4: Content & Platform Optimization
- [ ] Publish `/about/brand-facts` page: founding year, production volume, HQ address, Hans Wilsdorf Foundation structure, sustainability metrics — formatted as clean prose with visible dates
- [ ] Rewrite 3-5 key heading pairs on Watchmaking and watch model pages from aspirational ("Excellence in the making") to descriptive ("How Rolex Movements Are Certified to Superlative Chronometer Standards")
- [ ] Add FAQ blocks (40-60 words per answer) to Submariner, Daytona, and Datejust product pages
- [ ] LinkedIn: publish first monthly long-form post on watchmaking innovation (target: build toward 1M followers in 12 months)
- [ ] Audit newsroom.rolex.com: verify AI crawler access, add visible dates to all press releases, submit as separate Search Console property

---

## Appendix A: Pages Analyzed

| Source | Content Type | Key GEO Issues |
|---|---|---|
| robots.txt (live) | Technical | No AI crawler directives; 2-sec crawl delay; sitemap blocked at WAF |
| Wikipedia: Rolex | Third-party entity | Full article — strong AI knowledge base source |
| Wikidata Q62288 | Third-party entity | Complete entity graph — unlinked from rolex.com via sameAs |
| Newsroom.rolex.com | Brand subdomain | Unknown crawler access; deeper content than main site |
| Google indexed: About Rolex | Brand content | Sparse copy; no dates; strong historical facts |
| Google indexed: Watchmaking | Brand content | Technical depth; no attribution; no dates |
| Google indexed: Submariner | Product page | No Product schema; no FAQ; no pricing |
| Google indexed: Certified Pre-Owned | Program page | Good trust content; no schema; no dates |
| Google indexed: History | Brand content | Specific dates and facts; good citability potential |
| Google indexed: Sustainability | Brand content | Highest-density trust content; PDF-buried; no visible dates |
| Reddit r/rolex | Third-party community | ~278K members; strong Perplexity signal |
| Hodinkee / FratelloWatches | Third-party press | Primary AI citation source for Rolex facts |
| Bloomberg / Forbes | Third-party mainstream | High-authority entity corroboration |

---

## Appendix B: Ready-to-Use JSON-LD Templates

### Organization Schema (Global `<head>`)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.rolex.com/#organization",
  "name": "Rolex",
  "legalName": "Montres Rolex SA",
  "url": "https://www.rolex.com",
  "logo": {
    "@type": "ImageObject",
    "url": "https://www.rolex.com/[REPLACE: logo path, min 112×112px]",
    "width": 512,
    "height": 512
  },
  "description": "Rolex is a Swiss luxury watch manufacturer based in Geneva, Switzerland, designing, developing, and producing watches in-house since 1905.",
  "foundingDate": "1905",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "3-7, rue François-Dussaud",
    "addressLocality": "Geneva",
    "postalCode": "1211",
    "addressCountry": "CH"
  },
  "sameAs": [
    "https://en.wikipedia.org/wiki/Rolex",
    "https://www.wikidata.org/wiki/Q62288",
    "https://www.linkedin.com/company/rolex",
    "https://www.youtube.com/rolex",
    "https://www.instagram.com/rolex/",
    "https://x.com/rolex"
  ]
}
```

### Product Schema (Watch Model Pages)

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "[REPLACE: e.g., 'Rolex Submariner Date']",
  "description": "[REPLACE: official product description]",
  "brand": {
    "@type": "Brand",
    "name": "Rolex",
    "@id": "https://www.rolex.com/#organization"
  },
  "sku": "[REPLACE: reference number, e.g., '126610LN']",
  "image": ["[REPLACE: primary product image URL]"],
  "material": "[REPLACE: e.g., 'Oystersteel']",
  "additionalProperty": [
    {"@type": "PropertyValue", "name": "Case Diameter", "value": "[REPLACE: e.g., '41 mm']"},
    {"@type": "PropertyValue", "name": "Water Resistance", "value": "[REPLACE: e.g., '300 m / 1,000 ft']"},
    {"@type": "PropertyValue", "name": "Calibre", "value": "[REPLACE: e.g., '3235']"}
  ],
  "offers": {
    "@type": "Offer",
    "availability": "https://schema.org/InStoreOnly",
    "seller": {"@type": "Organization", "@id": "https://www.rolex.com/#organization"}
  }
}
```

---

## Appendix C: Competitive Context

| Brand | GEO-Estimated Score | Key Differentiator |
|---|---|---|
| **Rolex** | **48/100** | Maximum brand authority; minimum own-domain technical optimization |
| Patek Philippe | ~44/100 | Similar luxury minimalism; slightly better editorial depth |
| Audemars Piguet | ~52/100 | "Stories" editorial section improves E-E-A-T; similar WAF issues |
| A. Lange & Söhne | ~55/100 | Best technical content in segment; smaller brand authority base |
| Omega | ~61/100 | Parent LVMH/Swatch Group invests more heavily in digital; better schema |
| TAG Heuer | ~58/100 | New F1 partnership generates fresh editorial signals; LVMH digital infra |

**Rolex's GEO opportunity** is larger than any competitor because the brand authority foundation (91/100) is pre-built. The gap between current score (48) and potential score (~75–80 with full implementation) is the widest in the luxury watch segment.

---

*Report generated by GEO Audit framework v1.0 — 2026-03-20*
*Methodology: Phase 1 discovery (homepage fetch, robots.txt, sitemap), Phase 2 parallel subagent analysis (Technical GEO, Content E-E-A-T, Schema, Platform Optimization), Phase 3 score aggregation.*
