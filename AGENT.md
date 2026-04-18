# bilinovel-cli

A Python CLI tool for scraping novels from bilinovel (哔哩轻小说).

## Project Structure

```
bilinovel_cli/
├── AGENT.md                       # Agent instructions
├── README.md                      # User-facing README
├── main.py                        # Entry point
├── pyproject.toml                 # Dependencies
├── docs/
│   └── DESIGN.md                  # Design document
└── bilinovel_cli/
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── fetcher.py             # Page fetching (playwright + stealth)
    │   ├── parser.py              # HTML parsing (lxml)
    │   ├── storage.py             # Local storage (txt)
    │   └── rubbish_map.json       # Anti-crawler character mapping
    └── cli/
        ├── __init__.py
        ├── commands.py            # CLI commands
        ├── console.py             # Rich console output
        ├── formatters.py          # Output formatting
        └── selector.py            # Interactive volume selection
```

## Tech Stack

- Python ≥ 3.13
- [playwright](https://playwright.dev/python/) - Dynamic page rendering
- [playwright-stealth](https://github.com/defaultnamehere/playwright-stealth) - Anti-detection
- [lxml](https://lxml.de/) - HTML parsing with XPath
- [rich](https://rich.readthedocs.io/) - Terminal UI
- [readchar](https://github.com/miso-belica/readchar) - Keyboard input

## Code Style

- **Naming**: snake_case (PEP 8)
- **KISS**: Simple logic, avoid deep nesting (≤ 3 levels)
- **Functions**: ≤ 50 lines each
- **Modules**: Low coupling, high cohesion

## Delay Constants (fetcher.py)

| Constant | Value | Purpose |
|----------|-------|---------|
| `CLOUDCARE_WAIT` | 5s | Extra wait on Cloudflare challenge detection |
| `RETRY_WAIT` | 2s | Wait between fetch retries |
| `_prepare_novel_page()` sleep | 0.5s | After goto and after reload |
| `fetch()` sleep | 0.5s | Before fetching chapter |
| `--interval` CLI param | 0s (default) | Extra delay between requests |

## Workflow

```
novel_id → fetcher (playwright+stealth) → parser (lxml) → storage (txt)
```

1. **Fetch**: playwright-stealth renders JS-heavy pages, bypasses Cloudflare
2. **Parse**: lxml XPath extracts title, chapters, content, replace rubbish text
3. **Store**: Write per-chapter .txt files in volume folders
4. **Display**: rich progress bars and status updates

## CLI Commands

```bash
# Show novel info
bilinovel info <novel_id>

# Show catalog
bilinovel catalog <novel_id>

# Download novel (interactive volume selection)
bilinovel download <novel_id>

# Download specific volumes
bilinovel download <novel_id> -v 0 1 2

# Download with interval delay
bilinovel download <novel_id> -i 1.0

# Download to custom output dir
bilinovel download <novel_id> -o ./novels
```

## Key Implementation Details

### Cloudflare Bypass

1. Visit novel main page first (`/novel/{id}.html`)
2. Reload the page
3. THEN visit chapter page

This triggers/clears the Cloudflare challenge before accessing content.

### Anti-Crawler Character Mapping

Site uses Private Use Area Unicode chars (e.g., `\ue000` → `\u72fc` "狼") to bypass crawlers.

`rubbish_map.json` contains `rubbish_secret_map` mapping these characters back to Chinese.

### Multi-Page Chapters

URL pattern: `/novel/{id}/{chapter_id}_{page}.html`

Detection: Check if `_{page+1}.html` exists in current page HTML.

### Invalid URL Detection

`Fetcher.check_url()` returns `True` if URL contains `javascript` or `cid` - these are skipped during download.

## Dependencies

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "playwright>=1.40.0",
    "playwright-stealth>=2.0.0",
    "lxml>=5.0.0",
    "rich>=13.0.0",
    "readchar>=4.0.0",
]
```

## Installation

```bash
# Install browsers
playwright install chromium

# Run without installing
uv run python main.py <command>
```

## Testing

```bash
# Run a quick test
uv run python -c "
from bilinovel_cli.core import Fetcher, Parser
f = Fetcher()
html = f.fetch_novel(1855)
print(len(html))
f.close()
"
```
