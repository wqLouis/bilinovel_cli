# Design Document

## Overview

A Python CLI tool for scraping novels from bilinovel (哔哩轻小说).

## Tech Stack

- Python ≥ 3.13
- [playwright](https://playwright.dev/python/) - Dynamic page rendering
- [playwright-stealth](https://github.com/defaultnamehere/playwright-stealth) - Anti-detection
- [lxml](https://lxml.de/) - HTML parsing with XPath
- [rich](https://rich.readthedocs.io/) - Terminal UI
- [readchar](https://github.com/miso-belica/readchar) - Keyboard input

## Project Structure

```
bilinovel_cli/
├── bilinovel_cli/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── fetcher.py           # Page fetching (playwright + stealth)
│   │   ├── parser.py             # HTML parsing (lxml)
│   │   ├── storage.py            # Local storage (txt)
│   │   └── rubbish_map.json      # Anti-crawler character mapping
│   └── cli/
│       ├── __init__.py
│       ├── commands.py           # CLI commands
│       ├── console.py            # Rich console output
│       ├── formatters.py         # Output formatting
│       └── selector.py           # Interactive volume selection
├── docs/
│   └── DESIGN.md
├── main.py
└── pyproject.toml
```

## Data Structures

### NovelData

```python
@dataclass
class NovelData:
    title: str
    author: str
    description: str
    cover: str = ""
    tags: List[str] = field(default_factory=list)
    volumes: List[VolumeData] = field(default_factory=list)
```

### VolumeData

```python
@dataclass
class VolumeData:
    title: str
    chapters: List[ChapterData] = field(default_factory=list)
```

### ChapterData

```python
@dataclass
class ChapterData:
    title: str
    num: int
    url: str
    content: str = ""
```

## Core Modules

### bilinovel_cli.core

| Module | Class | Responsibility |
|--------|-------|---------------|
| `fetcher.py` | `Fetcher` | Page fetching via playwright-stealth, Cloudflare bypass, singleton pattern |
| `parser.py` | `Parser` | HTML parsing with lxml XPath, rubbish text replacement, content cleaning |
| `storage.py` | `Storage` | Save novels as per-chapter .txt files in volume folders |

### bilinovel_cli.cli

| Module | Class | Responsibility |
|--------|-------|---------------|
| `commands.py` | - | CLI argument parsing, command dispatch (info/catalog/download) |
| `console.py` | `ConsoleProgress` | Rich-based progress bars, status display |
| `formatters.py` | `NovelFormatter`, `ChapterFormatter` | Format output for terminal |
| `selector.py` | `VolumeSelector` | Interactive volume selection with arrow keys |

## Features

### 1. Cloudflare Anti-Bot Detection

**Detection**: Check if response contains `Access denied | www.bilinovelib.com used Cloudflare`.

**Bypass Strategy**: The key trick is to visit the novel's main page first, then reload it to trigger/clear the Cloudflare challenge, BEFORE visiting the chapter page.

**Code Location**: `bilinovel_cli/core/fetcher.py` - `_prepare_novel_page()`

**Behavior**:
```
1. goto main_page (/novel/{id}.html)
2. sleep 0.5s
3. reload main_page
4. sleep 0.5s
5. goto chapter page
```

### 2. Request Interval Control

**Purpose**: Avoid triggering anti-bot by reducing request frequency.

**Parameter**: `--interval` (seconds, default: 0)

**Code Location**: `bilinovel_cli/core/fetcher.py` - `Fetcher.interval`

### 3. Anti-Crawler Character Mapping

**Purpose**: Replace obfuscated Unicode characters back to Chinese characters.

**Mechanism**: Site uses Private Use Area characters (e.g., `\ue000` → `\u72fc` "狼") to bypass crawlers.

**Character Map**: `bilinovel_cli/core/rubbish_map.json`

**Code Location**: `bilinovel_cli/core/parser.py` - `replace_rubbish_text()`

### 4. Multi-Page Chapter Detection

**URL Pattern**: `{novel_id}/{chapter_id}_{page}.html`

**Detection Method**: Check if `_{page+1}.html` exists in current page HTML.

**Code Location**: `bilinovel_cli/core/fetcher.py` - `fetch_chapter_pages()`

### 5. Invalid URL Detection

**Purpose**: Skip chapters with broken URLs (e.g., `javascript:cid(0)`).

**Detection**: `Fetcher.check_url()` returns `True` if URL contains `javascript` or `cid`.

**Code Location**: `bilinovel_cli/core/fetcher.py` - `check_url()`

### 6. Content Cleaning

**Purpose**: Remove anti-crawler artifacts from chapter text.

**Cleaning Rules**:
1. Remove anti-crawler message (`【如需繼續閱讀請使用〔Chrome瀏覽器〕訪問 www.bilinovel.com】`)
2. Remove HTML comments
3. Remove `<pN>` tags
4. Replace `<br>` with newlines
5. Collapse multiple newlines

**Code Location**: `bilinovel_cli/core/parser.py` - `clean_content()`

### 7. File Name Sanitization

**Purpose**: Ensure saved file names are valid across different file systems.

**Illegal Characters**: `? * " < > | : / \`

**Replacement**: `□` (U+25A1)

**Code Location**: `bilinovel_cli/core/storage.py` - `check_chars()`

### 8. Resume Support

Skip existing files during download - if a chapter .txt already exists, it is skipped.

**Code Location**: `bilinovel_cli/cli/commands.py` - `_download_volumes()`

## CLI Interface

### Commands

#### `info <novel_id>`

Display novel information.

```
$ bilinovel info 1855

================================================================================
  约会大作战 DATE A LIVE
================================================================================
[作者] 橘公司

带给世界灾害的「精灵」...
解决方案只有消灭或……约会？...

共 386 章
================================================================================
```

#### `catalog <novel_id>`

Display novel catalog with volume and chapter counts.

```
$ bilinovel catalog 1855
```

#### `download <novel_id> [-v VOLUME] [-o OUTPUT] [-i INTERVAL]`

Download novel to txt files.

```
$ bilinovel download 1855 -v 0 1 2 -o ./novels -i 1.0
```

**Parameters**:
| Parameter | Description | Default |
|-----------|-------------|---------|
| `novel_id` | Novel ID from bilinovel | Required |
| `-v, --volumes` | Volume numbers to download (space-separated) | Interactive selection |
| `-o, --output` | Output directory | `.` |
| `-i, --interval` | Delay between requests in seconds | `0` |
| `--no-progress` | Disable progress bar | `False` |

### Output Format

```
novel_title/
├── volume_title_1/
│   ├── Chapter 1.txt
│   └── Chapter 2.txt
└── volume_title_2/
    └── Chapter 1.txt
```

Each .txt file contains:
```
# Chapter Title

Chapter content here...
```

## API

### Core Module

```python
from bilinovel_cli.core import Fetcher, Parser, Storage

# Fetcher (singleton)
fetcher = Fetcher.get_instance(interval=0)
html = fetcher.fetch_novel(novel_id)
html = fetcher.fetch_catalog(novel_id)
html = fetcher.fetch_chapter(novel_id, chapter_id)
pages = fetcher.fetch_chapter_pages(url)
fetcher.close()

# Parser
parser = Parser()
novel = parser.parse_novel(novel_html, catalog_html)
volumes = parser.parse_catalog(catalog_html)
content = parser.parse_chapter_content(chapter_html)
clean_content = parser.clean_content(content)
replaced_content = parser.replace_rubbish_text(content)
full_content = parser.parse_chapter_pages(list_of_html)

# Storage
storage = Storage(output_dir="./novels")
path = storage.prepare_novel(novel)
path = storage.prepare_volume(volume, novel_path)
path = storage.save_chapter(chapter, volume_path)
path = storage.save_volume(volume, novel_path)
path = storage.save_novel(novel)
```

### CLI Module

```python
from bilinovel_cli.cli import run, create_parser

# Run with custom args
exit_code = run(["download", "1855", "-v", "0", "1", "2"])

# Create parser for testing
parser = create_parser()
```

## Delay Constants

| Constant | Value | Location |
|----------|-------|----------|
| `CLOUDCARE_WAIT` | 5s | `fetcher.py` - Extra wait on Cloudflare detection |
| `RETRY_WAIT` | 2s | `fetcher.py` - Wait between fetch retries |
| `_prepare_novel_page()` sleep | 0.5s × 2 | `fetcher.py` - After goto and reload |
| `fetch()` sleep | 0.5s | `fetcher.py` - Before chapter fetch |
| `--interval` CLI param | 0s (default) | `commands.py` - Extra delay between requests |
