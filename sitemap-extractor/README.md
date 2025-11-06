# Sitemap to CSV Extractor

A Python script that fetches XML sitemaps and extracts URLs to a CSV file. Supports both regular sitemaps and sitemap index files, with optional filtering capabilities.

## Features

- Fetch and parse XML sitemaps
- Extract URLs with metadata (lastmod, priority, changefreq)
- Handle sitemap index files recursively
- Filter out RMC URLs (URLs with specific patterns)
- Export to CSV format

## Requirements

- Python 3.12+
- uv (Python package manager)

## Installation

### 1. Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone or navigate to the project

```bash
cd /Users/olivier/Developer/Scripting/sitemap-extractor
```

The dependencies will be automatically installed when you run the script with `uv run`.

## Usage

### Basic Usage

```bash
uv run sitemap_to_csv.py <sitemap_url>
```

This will:
- Fetch the sitemap from the URL
- Parse all URLs
- Create a `sitemap_csvs` folder if it doesn't exist
- Save them to `sitemap_csvs/sitemap_urls_YYYY-MM-DD.csv` (default output file)

### Command Line Options

| Option | Description |
|--------|-------------|
| `sitemap_url` | **(Required)** The URL of the sitemap to fetch |
| `-o`, `--output` | Output CSV filename (default: `sitemap_csvs/sitemap_urls_YYYY-MM-DD.csv`). Date is automatically added. |
| `-r`, `--recursive` | Recursively fetch sitemap index files |
| `--filter-rmc` | Filter out RMC URLs (starts with m/a, contains dash and numbers) |
| `--exclude-lang` | Exclude URLs containing specific language codes (can be used multiple times) |

## Examples

### Example 1: Basic sitemap extraction

```bash
uv run sitemap_to_csv.py https://example.com/sitemap.xml
```

Output: `sitemap_csvs/sitemap_urls_2025-11-06.csv` with all URLs from the sitemap (date is automatically added)

### Example 2: Custom output file

```bash
uv run sitemap_to_csv.py https://example.com/sitemap.xml -o sitemap_csvs/rolex_urls.csv
```

Output: `sitemap_csvs/rolex_urls_2025-11-06.csv` (date is automatically added before the extension)

### Example 3: Sitemap index with recursive fetching

If you have a sitemap index that references multiple sitemaps:

```bash
uv run sitemap_to_csv.py https://example.com/sitemap_index.xml --recursive
```

This will:
1. Fetch the sitemap index
2. Find all sitemap URLs within it
3. Fetch each sitemap
4. Extract all URLs from all sitemaps

### Example 4: Filter RMC URLs

```bash
uv run sitemap_to_csv.py https://example.com/sitemap.xml --filter-rmc
```

This filters out URLs where the last path segment:
- Starts with 'm' or 'a'
- Contains a dash (-)
- Contains numbers

**Filtered examples:**
- `https://example.com/page/m-123` ❌ (filtered out)
- `https://example.com/article/a-456` ❌ (filtered out)
- `https://example.com/M-789` ❌ (filtered out)

**Kept examples:**
- `https://example.com/page/article` ✓
- `https://example.com/page/b-123` ✓
- `https://example.com/page/m123` ✓ (no dash)

### Example 5: Exclude language URLs

```bash
uv run sitemap_to_csv.py https://example.com/sitemap.xml \
  --exclude-lang fr \
  --exclude-lang zh-hans
```

This filters out URLs containing specific language codes (case-insensitive).

**Filtered examples:**

- `https://example.com/fr/newsroom` ❌ (contains /fr/)
- `https://example.com/zh-hans/watches` ❌ (contains zh-hans)
- `https://example.com/news/french-watches` ❌ (contains 'fr')

**Kept examples:**

- `https://example.com/en/watches` ✓
- `https://example.com/newsroom` ✓

### Example 6: Combine all options

```bash
uv run sitemap_to_csv.py https://example.com/sitemap_index.xml \
  --recursive \
  --filter-rmc \
  --exclude-lang fr \
  --exclude-lang zh-hans \
  -o sitemap_csvs/filtered_urls.csv
```

Output: `sitemap_csvs/filtered_urls_2025-11-06.csv`

## Output Format

The script generates a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| `url` | The URL extracted from the sitemap |
| `changefreq` | How frequently the page is likely to change (optional) |
| `lastmod` | Last modification date (optional) |
| `priority` | Priority of this URL relative to other URLs (optional) |

Example CSV output:

```csv
url,changefreq,lastmod,priority
https://example.com/page1,weekly,2024-01-15,0.8
https://example.com/page2,monthly,2024-01-10,0.5
https://example.com/page3,,,
```

## Troubleshooting

### Error: "requests module not found"

If you see this error, make sure you're using `uv run`:

```bash
uv run sitemap_to_csv.py https://example.com/sitemap.xml
```

### Error: "Error fetching sitemap"

This can happen if:
- The URL is incorrect
- The website is down
- You don't have internet connectivity
- The sitemap requires authentication

### No URLs found

Check that:
- The sitemap URL is correct
- The sitemap is in valid XML format
- The sitemap follows the standard sitemap protocol

## Development

### Project Structure

```
sitemap-extractor/
├── sitemap_to_csv.py    # Main script
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Dependency lock file
├── .venv/              # Virtual environment (auto-created)
├── sitemap_csvs/       # Output folder for CSV files (auto-created)
└── README.md           # This file
```

### Adding Dependencies

```bash
uv add <package-name>
```

### Running in Development

```bash
# Sync dependencies
uv sync

# Run the script
uv run sitemap_to_csv.py --help
```

## License

This project is provided as-is for personal use.
