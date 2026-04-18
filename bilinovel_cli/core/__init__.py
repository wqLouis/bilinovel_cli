"""Core module for bilinovel scraping."""

from bilinovel_cli.core.fetcher import Fetcher
from bilinovel_cli.core.parser import Parser, NovelData, VolumeData, ChapterData
from bilinovel_cli.core.storage import Storage

__all__ = ["Fetcher", "Parser", "Storage", "NovelData", "VolumeData", "ChapterData"]
