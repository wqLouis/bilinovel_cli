"""Output formatting."""

from typing import List

from rich.table import Table


class NovelFormatter:
    def __init__(self, width: int = 80):
        self.width = width

    def format_novel_info(self, novel) -> str:
        total_chapters = sum(len(v.chapters) for v in novel.volumes)
        separator = "=" * self.width
        lines = [
            "",
            separator,
            f"  {novel.title}",
            separator,
            f"[作者] {novel.author}",
            "",
            f"{novel.description}",
            "",
            f"共 {total_chapters} 章",
            separator,
            "",
        ]
        return "\n".join(lines)

    def format_catalog(self, volumes: List) -> Table:
        table = Table(title="Novel Catalog")
        table.add_column("Volume", style="cyan")
        table.add_column("Chapters", justify="right", style="magenta")
        for vol in volumes:
            ch_count = len(vol.chapters)
            table.add_row(vol.title, str(ch_count))
        return table


class ChapterFormatter:
    def __init__(self, width: int = 80):
        self.width = width

    def format_chapter(self, chapter, show_title: bool = True) -> str:
        lines = []
        if show_title:
            separator = "=" * self.width
            lines.extend(["", separator, f"  {chapter.title}", separator, ""])

        for line in chapter.content.split("\n"):
            line = line.strip()
            if not line:
                lines.append("")
            elif len(line) <= self.width:
                lines.append(line)
            else:
                lines.extend(self._wrap_text(line))
        return "\n".join(lines)

    def _wrap_text(self, text: str) -> List[str]:
        words = text.split()
        lines = []
        current_line = []
        current_len = 0

        for word in words:
            word_len = len(word)
            if current_len + word_len + 1 <= self.width:
                current_line.append(word)
                current_len += word_len + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_len = word_len

        if current_line:
            lines.append(" ".join(current_line))

        return lines
