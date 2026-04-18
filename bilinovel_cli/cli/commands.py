"""CLI commands for bilinovel scraping."""

import argparse
import signal
import sys
from typing import Optional

from bilinovel_cli.cli.console import ConsoleProgress
from bilinovel_cli.cli.formatters import NovelFormatter

_fetcher_instance = None


def _get_fetcher(interval: float = 0):
    global _fetcher_instance
    if _fetcher_instance is None:
        from bilinovel_cli.core.fetcher import Fetcher

        _fetcher_instance = Fetcher.get_instance(interval)
    return _fetcher_instance


def _close_fetcher():
    global _fetcher_instance
    if _fetcher_instance is not None:
        _fetcher_instance.close()
        _fetcher_instance = None


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bilinovel",
        description="A CLI tool for scraping novels from bilinovel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    download_parser = subparsers.add_parser("download", help="Download a novel")
    download_parser.add_argument("novel_id", type=int, help="Novel ID from bilinovel")
    download_parser.add_argument("-o", "--output", default=".", help="Output directory")
    download_parser.add_argument(
        "-v", "--volumes", nargs="+", type=int, help="Volume numbers to download"
    )
    download_parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar"
    )
    download_parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=0,
        help="Interval between requests in seconds",
    )

    info_parser = subparsers.add_parser("info", help="Show novel information")
    info_parser.add_argument("novel_id", type=int, help="Novel ID from bilinovel")

    catalog_parser = subparsers.add_parser("catalog", help="Show novel catalog")
    catalog_parser.add_argument("novel_id", type=int, help="Novel ID from bilinovel")

    subparsers.add_parser("config", help="Configure browser and settings")

    return parser


def run(args: Optional[list] = None) -> int:
    parser = create_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 0

    console = ConsoleProgress()

    def signal_handler(sig, frame):
        _close_fetcher()
        console.stop()
        sys.exit(130)

    original_sigint = signal.signal(signal.SIGINT, signal_handler)

    try:
        if parsed.command == "download":
            return _run_download(console, parsed)
        elif parsed.command == "info":
            return _run_info(console, parsed)
        elif parsed.command == "catalog":
            return _run_catalog(console, parsed)
        elif parsed.command == "config":
            return _run_config(console)
        else:
            console.print_error(f"Unknown command: {parsed.command}")
            return 1
    except KeyboardInterrupt:
        console.print_warning("\nOperation cancelled by user")
        return 130
    except Exception as e:
        console.print_error(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        signal.signal(signal.SIGINT, original_sigint)
        _close_fetcher()
        console.stop()


def _run_download(console: ConsoleProgress, args: argparse.Namespace) -> int:
    from bilinovel_cli.core import Parser, Storage
    from bilinovel_cli.cli.selector import VolumeSelector

    fetcher = _get_fetcher(interval=args.interval)
    parser = Parser()
    storage = Storage(output_dir=args.output)

    novel = _fetch_novel_info(console, fetcher, parser, args.novel_id)
    selected_indices = _select_volumes(console, args, novel.volumes)
    if not selected_indices:
        return 0

    _download_volumes(console, fetcher, parser, storage, novel, selected_indices)
    return 0


def _fetch_novel_info(console, fetcher, parser, novel_id):
    console.print_info(f"Fetching novel ID: {novel_id}")
    novel_html = fetcher.fetch_novel(novel_id)
    catalog_html = fetcher.fetch_catalog(novel_id)
    novel = parser.parse_novel(novel_html, catalog_html)
    console.print_success(f"Novel: {novel.title}")
    console.print_info(f"Author: {novel.author}")
    return novel


def _select_volumes(console, args, volumes):
    if args.volumes:
        return args.volumes
    from bilinovel_cli.cli.selector import VolumeSelector

    selector = VolumeSelector(console, volumes)
    selected = selector.run()
    if not selected:
        console.print_warning("No volumes selected, exiting")
    return selected


def _download_volumes(console, fetcher, parser, storage, novel, selected_indices):
    total = sum(len(novel.volumes[i].chapters) for i in selected_indices)
    console.start_chapter_download(total)

    downloaded = 0
    novel_path = storage.prepare_novel(novel)

    for vol_idx in selected_indices:
        if vol_idx >= len(novel.volumes):
            console.print_warning(f"Volume {vol_idx} not found, skipping")
            continue
        vol = novel.volumes[vol_idx]
        console.print_info(f"Downloading: {vol.title}")
        vol_path = storage.prepare_volume(vol, novel_path)

        for ch in vol.chapters:
            if fetcher.check_url(ch.url):
                console.print_warning(f"Skipping invalid URL: {ch.url}")
                continue
            ch_path = vol_path / f"{ch.title}.txt"
            if ch_path.exists():
                console.print_info(f"Skipping existing: {ch.title}")
                continue
            ch.content = parser.parse_chapter_pages(fetcher.fetch_chapter_pages(ch.url))
            storage.save_chapter(ch, vol_path)
            downloaded += 1
            console.update_chapter(downloaded, ch.title)

    console.stop()
    console.print_success(f"Saved to: {novel_path}")


def _run_info(console: ConsoleProgress, args: argparse.Namespace) -> int:
    from bilinovel_cli.core import Parser

    console.print_info(f"Fetching novel ID: {args.novel_id}")

    fetcher = _get_fetcher()
    parser = Parser()

    novel_html = fetcher.fetch_novel(args.novel_id)
    catalog_html = fetcher.fetch_catalog(args.novel_id)
    novel = parser.parse_novel(novel_html, catalog_html)

    formatter = NovelFormatter()
    console.print(formatter.format_novel_info(novel))
    return 0


def _run_catalog(console: ConsoleProgress, args: argparse.Namespace) -> int:
    from bilinovel_cli.core import Parser

    console.print_info(f"Fetching catalog for novel ID: {args.novel_id}")

    fetcher = _get_fetcher()
    parser = Parser()

    catalog_html = fetcher.fetch_catalog(args.novel_id)
    volumes = parser.parse_catalog(catalog_html)

    formatter = NovelFormatter()
    console.print(formatter.format_catalog(volumes))
    return 0


def _run_config(console: ConsoleProgress) -> int:
    from bilinovel_cli.cli.browser_selector import BrowserSelector
    from bilinovel_cli.cli.config_manager import load_config, save_config

    config = load_config()
    selector = BrowserSelector(console.console)
    selected_browser, to_uninstall = selector.run(config.browser.type)

    if selected_browser is None:
        console.print_info("Configuration unchanged")
        return 0

    config.browser.type = selected_browser
    save_config(config)
    return 0
