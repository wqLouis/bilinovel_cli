"""Interactive browser selector with Rich Live."""

from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.console import Group
from rich.text import Text

from bilinovel_cli.cli.config_manager import (
    PLAYWRIGHT_BROWSERS,
    SYSTEM_BROWSERS,
    install_browser,
    get_installed_browsers,
    get_system_browsers,
    uninstall_browsers,
)


class BrowserSelector:
    UP = "\x1b[A"
    DOWN = "\x1b[B"
    SPACE = " "
    I_KEY = "i"
    D_KEY = "d"
    C_KEY = "c"
    QUIT_KEYS = {"q", "Q", "\x1b"}

    def __init__(self, console: Console):
        self._rich_console = console
        self._playwright_installed: list[str] = []
        self._system_browsers: list[tuple] = []
        self._cursor: int = 0
        self._selected_name: Optional[str] = None
        self._selected_source: str = "playwright"
        self._to_uninstall: list[str] = []
        self._install_progress: Optional[str] = None

    def run(
        self, current_browser: str, current_source: str
    ) -> tuple[str, str, str, list[str]]:
        self._parse_current(current_browser, current_source)
        self._refresh_status()

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
                    self._toggle_selection()
                elif key == self.I_KEY:
                    self._start_install(live)
                elif key == self.D_KEY:
                    self._mark_uninstall()
                elif key == self.C_KEY:
                    self._cancel_uninstall()
                elif key in self.QUIT_KEYS:
                    self._uninstall_pending()
                    return self._get_selection()

                live.update(self._build_renderable())

    def _parse_current(self, browser_type: str, source: str):
        self._selected_name = browser_type
        self._selected_source = source
        self._cursor = 0

    def _refresh_status(self):
        self._playwright_installed = get_installed_browsers()
        self._system_browsers = get_system_browsers()

    def _move_up(self):
        if self._cursor > 0:
            self._cursor -= 1

    def _move_down(self):
        total = 2 + len(PLAYWRIGHT_BROWSERS) + len(SYSTEM_BROWSERS)
        if self._cursor < total - 1:
            self._cursor += 1

    def _toggle_selection(self):
        name, source, path = self._get_item_at_cursor()
        if name:
            self._selected_name = name
            self._selected_source = source

    def _get_item_at_cursor(self) -> tuple:
        if self._cursor == 0:
            return ("playwright", "header", None)
        elif self._cursor <= len(PLAYWRIGHT_BROWSERS):
            idx = self._cursor - 1
            return (PLAYWRIGHT_BROWSERS[idx], "playwright", None)
        elif self._cursor == len(PLAYWRIGHT_BROWSERS) + 1:
            return ("system", "header", None)
        else:
            idx = self._cursor - len(PLAYWRIGHT_BROWSERS) - 2
            if idx < len(SYSTEM_BROWSERS):
                name, path, _ = self._system_browsers[idx]
                return (name, "system", path)
            return (None, "playwright", None)

    def _mark_uninstall(self):
        if not self._is_playwright_section(self._cursor):
            return
        idx = self._get_playwright_index(self._cursor)
        browser = PLAYWRIGHT_BROWSERS[idx]
        if browser in self._playwright_installed and browser not in self._to_uninstall:
            self._to_uninstall.append(browser)

    def _cancel_uninstall(self):
        self._to_uninstall = []

    def _start_install(self, live):
        name, source, _ = self._get_item_at_cursor()
        if source != "playwright":
            return
        if name in self._playwright_installed:
            return

        self._install_progress = f"Installing {name}..."
        live.update(self._build_renderable())

        def progress_callback(line: str):
            self._install_progress = line
            live.update(self._build_renderable())

        success = install_browser(name, progress_callback)
        if success:
            self._playwright_installed = get_installed_browsers()
        self._install_progress = None

    def _get_selection(self) -> tuple:
        if not self._selected_name:
            return (None, "playwright", None, self._to_uninstall)

        if self._selected_source == "playwright":
            return (self._selected_name, "playwright", None, self._to_uninstall)

        for i, (name, path, found) in enumerate(self._system_browsers):
            if name == self._selected_name:
                return (name, "system", path, self._to_uninstall)

        return (None, "playwright", None, self._to_uninstall)

    def _uninstall_pending(self):
        if self._to_uninstall:
            uninstall_browsers()

    def _build_renderable(self):
        table = Table(box=None, show_header=False, pad_edge=False)
        table.add_column("Browser", style="cyan")
        table.add_column("Status", style="magenta")

        table.add_row("[bold]Playwright[/bold]", "")
        for i, browser in enumerate(PLAYWRIGHT_BROWSERS):
            row_idx = i + 1
            is_selected = (
                browser == self._selected_name and self._selected_source == "playwright"
            )
            prefix = self._get_prefix(row_idx, is_selected)
            installed = browser in self._playwright_installed
            status = (
                "[green]Installed[/green]" if installed else "[red]Not Installed[/red]"
            )
            table.add_row(prefix + browser, status)

        table.add_row("[bold]System[/bold]", "")
        system_start = len(PLAYWRIGHT_BROWSERS) + 2
        for i, (name, path, found) in enumerate(self._system_browsers):
            row_idx = system_start + i
            is_selected = (
                name == self._selected_name and self._selected_source == "system"
            )
            prefix = self._get_prefix(row_idx, is_selected)
            status = "[green]" + path + "[/green]" if found else "[red]Not Found[/red]"
            table.add_row(prefix + name, status)

        browser, source, path, _ = self._get_selection()
        if browser:
            if source == "system":
                display = f"system:{browser} ({path})"
            else:
                display = f"playwright:{browser}"
        else:
            display = "none"

        status_text = f"[bold]Selected:[/bold] {display}"

        help_text = (
            "[bold yellow]↑/↓[/bold yellow] Move  "
            "[bold yellow]Space[/bold yellow] Toggle  "
            "[bold yellow]i[/bold yellow] Install  "
            "[bold yellow]d[/bold yellow] Uninstall All  "
            "[bold yellow]c[/bold yellow] Cancel  "
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

    def _get_prefix(self, idx: int, is_selected: bool) -> str:
        cursor = "[bold green]>[/bold green] " if idx == self._cursor else "  "
        mark = "[bold green](*)[/bold green] " if is_selected else "    "
        return cursor + mark
