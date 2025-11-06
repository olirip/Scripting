#!/usr/bin/env python3
"""
Sitemap to CSV Converter

This script fetches a sitemap URL, parses it, and saves all URLs to a CSV file.
Supports both regular sitemaps and sitemap index files.
"""

import csv
import sys
import os
import re
import argparse
from datetime import datetime
import requests
from xml.etree import ElementTree as ET
from urllib.parse import urljoin, urlparse


def filter_rmc_url(url):
    """
    Filter out URLs where the last part is an RMC.

    An RMC is defined as starting with 'm' or 'a', containing a '-' and numbers.

    Args:
        url: The URL to check

    Returns:
        The URL if it's NOT an RMC, None otherwise
    """
    parsed = urlparse(url)
    path_parts = parsed.path.rstrip('/').split('/')

    if not path_parts:
        return url

    last_part = path_parts[-1]

    # Check if last part is an RMC:
    # - starts with 'm' or 'a'
    # - contains a '-'
    # - contains numbers
    if re.match(r'^[ma]', last_part, re.IGNORECASE) and '-' in last_part and re.search(r'\d', last_part):
        return None

    return url


def filter_language_url(url, languages=None):
    """
    Filter out URLs containing specific language codes.

    Args:
        url: The URL to check
        languages: List of language codes to filter out (e.g., ['zh-hans', 'fr'])

    Returns:
        The URL if it doesn't contain filtered languages, None otherwise
    """
    if not languages:
        return url

    url_lower = url.lower()

    for lang in languages:
        # Check for /lang/ pattern
        if f'/{lang}/' in url_lower:
            return None
        # Check for lang anywhere in the URL
        if lang in url_lower:
            return None

    return url


def fetch_sitemap(url):
    """Fetch sitemap content from URL."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error fetching sitemap: {e}", file=sys.stderr)
        sys.exit(1)


def parse_sitemap(content):
    """Parse sitemap XML and extract URLs."""
    urls = []

    try:
        root = ET.fromstring(content)

        # Handle namespace
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Check if it's a sitemap index or regular sitemap
        sitemap_elements = root.findall('.//ns:sitemap/ns:loc', namespace)

        if sitemap_elements:
            # It's a sitemap index, extract sitemap URLs
            for elem in sitemap_elements:
                urls.append({
                    'url': elem.text,
                    'type': 'sitemap'
                })
        else:
            # It's a regular sitemap, extract page URLs
            url_elements = root.findall('.//ns:url/ns:loc', namespace)
            for elem in url_elements:
                urls.append({
                    'url': elem.text
                })

            # Also try to get lastmod if available
            for url_elem in root.findall('.//ns:url', namespace):
                loc = url_elem.find('ns:loc', namespace)
                lastmod = url_elem.find('ns:lastmod', namespace)
                priority = url_elem.find('ns:priority', namespace)
                changefreq = url_elem.find('ns:changefreq', namespace)

                if loc is not None and loc.text:
                    url_data = {'url': loc.text}
                    if lastmod is not None:
                        url_data['lastmod'] = lastmod.text
                    if priority is not None:
                        url_data['priority'] = priority.text
                    if changefreq is not None:
                        url_data['changefreq'] = changefreq.text

                    # Only add if not already in urls
                    if not any(u['url'] == url_data['url'] for u in urls):
                        urls.append(url_data)

    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        sys.exit(1)

    return urls


def save_to_csv(urls, output_file):
    """Save URLs to CSV file."""
    if not urls:
        print("No URLs found in sitemap", file=sys.stderr)
        sys.exit(1)

    # Determine all keys present in the data
    fieldnames = ['url']
    additional_fields = set()
    for url_data in urls:
        additional_fields.update(url_data.keys())
    additional_fields.discard('url')
    fieldnames.extend(sorted(additional_fields))

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(urls)

        print(f"Successfully saved {len(urls)} URLs to {output_file}")

    except IOError as e:
        print(f"Error writing to file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Fetch a sitemap and save URLs to CSV file'
    )
    parser.add_argument(
        'sitemap_url',
        help='URL of the sitemap to fetch'
    )
    parser.add_argument(
        '-o', '--output',
        default='sitemap_csvs/sitemap_urls.csv',
        help='Output CSV file name (default: sitemap_csvs/sitemap_urls_YYYY-MM-DD.csv). Date is automatically added.'
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Recursively fetch sitemap index files'
    )
    parser.add_argument(
        '--filter-rmc',
        action='store_true',
        help='Filter out URLs where last part is an RMC (starts with m/a, contains - and numbers)'
    )
    parser.add_argument(
        '--exclude-lang',
        action='append',
        help='Exclude URLs containing specific language codes (e.g., --exclude-lang fr --exclude-lang zh-hans)'
    )

    args = parser.parse_args()

    # If output path has no directory component, prepend sitemap_csvs/
    if os.path.dirname(args.output) == '':
        args.output = f"sitemap_csvs/{args.output}"

    # Add today's date to filename
    today = datetime.now().strftime('%Y-%m-%d')

    # If {date} placeholder is present, replace it
    if '{date}' in args.output:
        args.output = args.output.replace('{date}', today)
    else:
        # Otherwise, insert date before the file extension
        if '.' in args.output:
            name, ext = args.output.rsplit('.', 1)
            args.output = f"{name}_{today}.{ext}"
        else:
            args.output = f"{args.output}_{today}"

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    print(f"Fetching sitemap from: {args.sitemap_url}")
    content = fetch_sitemap(args.sitemap_url)

    print("Parsing sitemap...")
    urls = parse_sitemap(content)

    # If recursive and we found sitemap indexes, fetch them too
    if args.recursive:
        sitemap_urls = [u['url'] for u in urls if u.get('type') == 'sitemap']
        if sitemap_urls:
            print(f"Found {len(sitemap_urls)} sitemap(s) in index, fetching recursively...")
            all_urls = []
            for sitemap_url in sitemap_urls:
                print(f"  Fetching: {sitemap_url}")
                sub_content = fetch_sitemap(sitemap_url)
                sub_urls = parse_sitemap(sub_content)
                all_urls.extend(sub_urls)
            urls = all_urls

    print(f"Found {len(urls)} URLs")

    # Apply RMC filter if requested
    if args.filter_rmc:
        original_count = len(urls)
        urls = [url_data for url_data in urls if filter_rmc_url(url_data.get('url'))]
        filtered_count = original_count - len(urls)
        print(f"Filtered out {filtered_count} RMC URLs ({len(urls)} remaining)")

    # Apply language filter if requested
    if args.exclude_lang:
        original_count = len(urls)
        urls = [url_data for url_data in urls if filter_language_url(url_data.get('url'), args.exclude_lang)]
        filtered_count = original_count - len(urls)
        print(f"Filtered out {filtered_count} URLs with languages {args.exclude_lang} ({len(urls)} remaining)")

    save_to_csv(urls, args.output)


if __name__ == '__main__':
    main()
