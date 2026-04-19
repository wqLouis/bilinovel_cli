"""Local storage as .txt file with per-chapter structure."""

import os
from pathlib import Path

from bilinovel_cli.core.parser import ChapterData, NovelData, VolumeData


_ILLEGAL_CHARS = '?*"<>|:/'
_CHAR_TRANSLATION = str.maketrans({c: "\u25a0" for c in _ILLEGAL_CHARS})


def check_chars(name: str) -> str:
    return name.translate(_CHAR_TRANSLATION)


class Storage:
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)

    def prepare_novel(self, novel: NovelData) -> Path:
        safe_title = check_chars(novel.title)
        novel_path = self.output_dir / safe_title
        novel_path.mkdir(parents=True, exist_ok=True)
        return novel_path

    def prepare_volume(self, volume: VolumeData, novel_path: Path) -> Path:
        safe_vol_title = check_chars(volume.title)
        vol_path = novel_path / safe_vol_title
        vol_path.mkdir(parents=True, exist_ok=True)
        return vol_path

    def save_chapter(self, chapter: ChapterData, volume_path: Path) -> Path:
        filepath = volume_path / f"{chapter.title}.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {chapter.title}\n\n")
            f.write(chapter.content)
            f.write("\n")
        return filepath

    def save_volume(self, volume: VolumeData, novel_path: Path) -> Path:
        vol_path = self.prepare_volume(volume, novel_path)
        for ch in volume.chapters:
            if ch.content:
                self.save_chapter(ch, vol_path)
        return vol_path

    def save_novel(self, novel: NovelData) -> Path:
        novel_path = self.prepare_novel(novel)
        for vol in novel.volumes:
            if vol.chapters and vol.chapters[0].content:
                self.save_volume(vol, novel_path)
        return novel_path
