# bilinovel-cli

A CLI tool for scraping novels from bilinovel (哔哩轻小说).

[中文](./README.md)

## Install

```bash
# Install playwright browsers
playwright install chromium
```

## Usage

```bash
# Show novel info
bilinovel info <novel_id>

# Show catalog
bilinovel catalog <novel_id>

# Download novel (interactive volume selection)
bilinovel download <novel_id>

# Download specific volumes
bilinovel download <novel_id> -v 0 1 2

# Download with interval delay (seconds)
bilinovel download <novel_id> -i 1.0

# Download to custom output dir
bilinovel download <novel_id> -o ./novels
```

## Run Without Installing

```bash
uv run python main.py <command>
```

## Output

Novels are saved as per-chapter .txt files organized in volume folders.

```
novel_title/
├── volume_title_1/
│   ├── Chapter 1.txt
│   └── Chapter 2.txt
└── volume_title_2/
    └── Chapter 1.txt
```

## Acknowledgments

- [bilinovel-download](https://github.com/ShqWW/bilinovel-download/tree/master) - for the rubbish_secret_map character mapping data
