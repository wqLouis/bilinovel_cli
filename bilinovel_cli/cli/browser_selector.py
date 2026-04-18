"""Interactive browser selector with Rich Live."""

from typing import Optional, Callable

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.console import Group
from rich.text import Text

from bilinovel_cli.cli.config_manager import (
    BROWSER_TYPES,
    install_browser,
    get_installed_browsers,
)


class BrowserSelector:
    UP = "\x1b[A"
    DOWN = "\x1b[B"
    SPACE = " "
    ENTER_KEYS = {"\r", "\n"}
    I_KEY = "i"
    D_KEY = "d"
    QUIT_KEYS = {"q", "Q", "\x1b"}

    def __init__(self, console: Console):
        self._rich_console = console
        self._installed: list[str] = []
        self._cursor: int = 0
        self._selected: int = 0
        self._to_uninstall: list[str] = []
        self._install_progress: Optional[str] = None

    def run(self, current_browser: str) -> tuple[str, list[str]]:
        self._selected = (
            BROWSER_TYPES.index(current_browser)
            if current_browser in BROWSER_TYPES
            else 0
        )
        self._cursor = self._selected
        self._refresh_installed()

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
                elif key == self.SPACE or key in self.ENTER_KEYS:
                    result = self._get_selected_browser()
                    self._uninstall_pending()
                    return result, self._to_uninstall
                elif key == self.I_KEY:
                    self._start_install(live)
                elif key == self.D_KEY:
                    self._mark_uninstall()
                elif key in self.QUIT_KEYS:
                    self._uninstall_pending()
                    return None, []

                live.update(self._build_renderable())

    def _refresh_installed(self):
        self._installed = get_installed_browsers()

    def _move_up(self):
        if self._cursor > 0:
            self._cursor -= 1
            self._selected = self._cursor

    def _move_down(self):
        if self._cursor < len(BROWSER_TYPES) - 1:
            self._cursor += 1
            self._selected = self._cursor

    def _mark_uninstall(self):
        browser = BROWSER_TYPES[self._cursor]
        if browser in self._installed and browser not in self._to_uninstall:
            self._to_uninstall.append(browser)

    def _start_install(self, live):
        browser = BROWSER_TYPES[self._cursor]
        if browser in self._installed and browser not in self._to_uninstall:
            return

        self._install_progress = f"Installing {browser}..."
        live.update(self._build_renderable())

        def progress_callback(line: str):
            self._install_progress = line
            live.update(self._build_renderable())

        success = install_browser(browser, progress_callback)
        if success:
            self._installed = get_installed_browsers()
        self._install_progress = None

    def _get_selected_browser(self) -> str:
        return BROWSER_TYPES[self._selected]

    def _uninstall_pending(self):
        from bilinovel_cli.cli.config_manager import uninstall_browser

        for browser in self._to_uninstall:
            uninstall_browser(browser)

    def _build_renderable(self):
        table = Table(box=None, show_header=False, pad_edge=False)
        table.add_column("Browser", style="cyan")
        table.add_column("Status", style="magenta")

        for i, browser in enumerate(BROWSER_TYPES):
            if i == self._cursor:
                prefix = "[bold green]> [/bold green]"
            else:
                prefix = "  "

            if i == self._selected:
                prefix += "[bold green](*)[/bold green] "
            else:
                prefix += "    "

            installed = browser in self._installed and browser not in self._to_uninstall
            status = (
                "[green]Installed[/green]" if installed else "[red]Not Installed[/red]"
            )
            table.add_row(prefix + browser, status)

        selected_browser = self._get_selected_browser()
        status_text = f"[bold]Selected browser:[/bold] {selected_browser}"

        help_text = (
            "[bold yellow]↑/↓[/bold yellow] Move  "
            "[bold yellow]Space/Enter[/bold yellow] Confirm  "
            "[bold yellow]i[/bold yellow] Install  "
            "[bold yellow]d[/bold yellow] Uninstall  "
            "[bold yellow]q[/bold yellow] Quit"
        )

        lines = [
            table,
            "",
            Text.from_markup(status_text, justify="center"),
            "",
        ]

        if self._install_progress:
            lines.append(
                Text.from_markup(
                    f"[yellow]{self._install_progress}[/yellow]", justify="center"
                )
            )
            lines.append("")

        if self._to_uninstall:
            lines.append(
                Text.from_markup(
                    f"[red]To uninstall: {', '.join(self._to_uninstall)}[/red]",
                    justify="center",
                )
            )
            lines.append("")

        lines.append(Text.from_markup(help_text, justify="center"))

        return Group(*lines)
