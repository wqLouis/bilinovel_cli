"""Interactive volume selector with arrow key navigation."""

from typing import List

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from bilinovel_cli.core.parser import VolumeData


class VolumeSelector:
    UP = "\x1b[A"
    DOWN = "\x1b[B"
    SPACE = " "
    ENTER_KEYS = {"\r", "\n"}
    A_KEY = "a"
    N_KEY = "n"

    def __init__(self, console: Console, volumes: List[VolumeData]):
        self._rich_console = console.console
        self.volumes = volumes
        self.selected: List[bool] = [False] * len(volumes)
        self.cursor: int = 0

    def run(self) -> List[int]:
        import readchar

        with Live(
            self._build_renderable(),
            console=self._rich_console,
            refresh_per_second=30,
            screen=True,
        ) as live:
            while True:
                key = readchar.readkey()
                if key == self.UP:
                    self._move_up()
                elif key == self.DOWN:
                    self._move_down()
                elif key == self.SPACE:
                    self._toggle_selected()
                elif key in self.ENTER_KEYS:
                    return self._get_selected_indices()
                elif key == self.A_KEY:
                    self._select_all()
                elif key == self.N_KEY:
                    self._deselect_all()
                live.update(self._build_renderable())

    def _build_renderable(self):
        from rich.console import Group
        from rich.text import Text

        table = Table(box=None, show_header=False, pad_edge=False)
        table.add_column("Volume", style="cyan", no_wrap=False)
        table.add_column("Chapters", justify="right", style="magenta")

        for i, vol in enumerate(self.volumes):
            ch_count = str(len(vol.chapters))
            if i == self.cursor:
                prefix = "[bold green]> [/bold green]"
            else:
                prefix = "  "
            if self.selected[i]:
                prefix += "[bold green]x[/bold green] "
            else:
                prefix += "  "
            table.add_row(prefix + vol.title, ch_count)

        selected_count = sum(self.selected)
        status = (
            f"[bold green]Selected: {selected_count} volume(s)[/bold green]"
            if selected_count
            else "[dim]No volume selected[/dim]"
        )

        help_text = (
            "[bold yellow][↑/↓][/bold yellow] Move  "
            "[bold yellow][Space][/bold yellow] Toggle  "
            "[bold yellow][Enter][/bold yellow] Confirm  "
            "[bold yellow][a][/bold yellow] All  "
            "[bold yellow][n][/bold yellow] None"
        )

        return Group(
            table,
            "",
            Text.from_markup(status, justify="center"),
            "",
            Text.from_markup(help_text, justify="center"),
        )

    def _move_up(self):
        if self.cursor > 0:
            self.cursor -= 1

    def _move_down(self):
        if self.cursor < len(self.volumes) - 1:
            self.cursor += 1

    def _toggle_selected(self):
        self.selected[self.cursor] = not self.selected[self.cursor]

    def _select_all(self):
        self.selected = [True] * len(self.volumes)

    def _deselect_all(self):
        self.selected = [False] * len(self.volumes)

    def _get_selected_indices(self) -> List[int]:
        return [i for i, selected in enumerate(self.selected) if selected]
