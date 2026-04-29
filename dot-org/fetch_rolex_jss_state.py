#!/usr/bin/env python3
import argparse
import gzip
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


USER_AGENT = "rolex-jss-state-fetcher/1.0 (+https://rolex.org)"


def fetch_url(url, timeout=30):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        encoding = resp.headers.get("Content-Encoding", "").lower()
        if encoding == "gzip":
            data = gzip.decompress(data)
        charset = resp.headers.get_content_charset() or "utf-8"
        return data.decode(charset, errors="replace")


def parse_sitemap_xml(xml_text):
    root = ET.fromstring(xml_text)
    tag = root.tag.lower()
    urls = []
    sitemaps = []

    if tag.endswith("sitemapindex"):
        for loc in root.findall(".//{*}loc"):
            if loc.text:
                sitemaps.append(loc.text.strip())
    elif tag.endswith("urlset"):
        for loc in root.findall(".//{*}loc"):
            if loc.text:
                urls.append(loc.text.strip())

    return sitemaps, urls


def load_all_sitemaps(start_url, timeout=30):
    queue = [start_url]
    seen = set()
    urls = []

    while queue:
        sitemap_url = queue.pop(0)
        if sitemap_url in seen:
            continue
        seen.add(sitemap_url)

        xml_text = fetch_url(sitemap_url, timeout=timeout)
        child_sitemaps, child_urls = parse_sitemap_xml(xml_text)
        queue.extend(child_sitemaps)
        urls.extend(child_urls)

    return urls


def _extract_balanced_object(text, start_idx):
    if start_idx >= len(text) or text[start_idx] != "{":
        return None

    depth = 0
    in_str = False
    esc = False
    for i in range(start_idx, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start_idx : i + 1]
    return None


def extract_jss_state(html_text):
    marker = "window.__JSS_STATE__"
    idx = html_text.find(marker)
    if idx == -1:
        return None

    # Find assignment
    assign = html_text.find("=", idx)
    if assign == -1:
        return None

    cursor = assign + 1
    while cursor < len(html_text) and html_text[cursor].isspace():
        cursor += 1

    # Case 1: JSON object
    if cursor < len(html_text) and html_text[cursor] == "{":
        obj_text = _extract_balanced_object(html_text, cursor)
        if obj_text:
            return json.loads(obj_text)

    # Case 2: JSON.parse("...")
    m = re.match(r'JSON\.parse\((["\'])(.*?)\1\)', html_text[cursor:], re.DOTALL)
    if m:
        raw = m.group(2)
        unescaped = json.loads(f'"{raw}"')
        return json.loads(unescaped)

    # Case 3: quoted JSON string
    m = re.match(r'(["\'])(.*?)\1', html_text[cursor:], re.DOTALL)
    if m:
        raw = m.group(2)
        unescaped = json.loads(f'"{raw}"')
        return json.loads(unescaped)

    return None


def url_to_output_path(data_dir, url):
    parsed = urllib.parse.urlparse(url)
    netloc = parsed.netloc
    path = parsed.path or "/"
    if path.endswith("/"):
        out_path = os.path.join(data_dir, netloc, path.lstrip("/"), "index.json")
    else:
        base, ext = os.path.splitext(path)
        if ext:
            out_path = os.path.join(data_dir, netloc, base.lstrip("/") + ".json")
        else:
            out_path = os.path.join(data_dir, netloc, path.lstrip("/") + ".json")
    return out_path


def ensure_parent_dir(path):
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch window.__JSS_STATE__ JSON from rolex.org pages listed in sitemap.xml"
    )
    parser.add_argument(
        "--sitemap",
        default="https://www.rolex.org/sitemap.xml",
        help="Root sitemap URL (default: https://www.rolex.org/sitemap.xml)",
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Output data directory (default: data)",
    )
    parser.add_argument("--sleep", type=float, default=0.2, help="Sleep between requests")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--max-urls", type=int, default=0, help="Max URLs to process (0 = no limit)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if output file exists")
    args = parser.parse_args()

    urls = load_all_sitemaps(args.sitemap, timeout=args.timeout)
    if not urls:
        print("No URLs found in sitemap.", file=sys.stderr)
        return 1

    processed = 0
    for url in urls:
        if args.max_urls and processed >= args.max_urls:
            break

        out_path = url_to_output_path(args.data_dir, url)
        if args.skip_existing and os.path.exists(out_path):
            continue

        try:
            html_text = fetch_url(url, timeout=args.timeout)
            jss_state = extract_jss_state(html_text)
            if jss_state is None:
                print(f"[WARN] No __JSS_STATE__ found: {url}")
                continue

            ensure_parent_dir(out_path)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(jss_state, f, ensure_ascii=False, indent=2)
            processed += 1
            print(f"[OK] {url} -> {out_path}")
        except Exception as exc:
            print(f"[ERR] {url}: {exc}", file=sys.stderr)
        finally:
            if args.sleep > 0:
                time.sleep(args.sleep)

    print(f"Done. Saved {processed} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
