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
        self._will_uninstall_all: bool = False
        self._install_progress: Optional[str] = None

    def run(
        self, current_browser: str, current_source: str
    ) -> tuple[str, str, str, bool]:
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
        self._will_uninstall_all = True

    def _cancel_uninstall(self):
        self._will_uninstall_all = False

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
            return (None, "playwright", None, self._will_uninstall_all)

        if self._selected_source == "playwright":
            return (self._selected_name, "playwright", None, self._will_uninstall_all)

        for i, (name, path, found) in enumerate(self._system_browsers):
            if name == self._selected_name:
                return (name, "system", path, self._will_uninstall_all)

        return (None, "playwright", None, self._will_uninstall_all)

    def _uninstall_pending(self):
        if self._will_uninstall_all:
            uninstall_browsers()

    def _build_renderable(self) -> Group:
        lines = [
            self._build_table(),
            "",
            self._build_status_text(),
            "",
        ]
        if self._install_progress:
            lines.append(self._build_install_progress())
        if self._will_uninstall_all:
            lines.append(self._build_uninstall_warning())
        lines.append(self._build_help_text())
        return Group(*lines)

    def _build_table(self) -> Table:
        table = Table(box=None, show_header=False, pad_edge=False)
        table.add_column("Browser", style="cyan")
        table.add_column("Status", style="magenta")

        table.add_row("[bold]Playwright[/bold]", "")
        for i, browser in enumerate(PLAYWRIGHT_BROWSERS):
            row_idx = i + 1
            is_sel = (
                browser == self._selected_name and self._selected_source == "playwright"
            )
            prefix = self._get_prefix(row_idx, is_sel)
            installed = browser in self._playwright_installed
            status = (
                "[green]Installed[/green]" if installed else "[red]Not Installed[/red]"
            )
            table.add_row(prefix + browser, status)

        table.add_row("[bold]System[/bold]", "")
        system_start = len(PLAYWRIGHT_BROWSERS) + 2
        for i, (name, path, found) in enumerate(self._system_browsers):
            row_idx = system_start + i
            is_sel = name == self._selected_name and self._selected_source == "system"
            prefix = self._get_prefix(row_idx, is_sel)
            status = "[green]" + path + "[/green]" if found else "[red]Not Found[/red]"
            table.add_row(prefix + name, status)
        return table

    def _build_status_text(self) -> Text:
        browser, source, path, _ = self._get_selection()
        if browser:
            if source == "system":
                display = f"system:{browser} ({path})"
            else:
                display = f"playwright:{browser}"
        else:
            display = "none"
        return Text.from_markup(f"[bold]Selected:[/bold] {display}", justify="center")

    def _build_install_progress(self) -> Text:
        return Text.from_markup(
            f"[yellow]{self._install_progress}[/yellow]", justify="center"
        )

    def _build_uninstall_warning(self) -> Text:
        return Text.from_markup(
            "[red]Will uninstall all browsers on quit[/red]", justify="center"
        )

    def _build_help_text(self) -> Text:
        return Text.from_markup(
            "[bold yellow]↑/↓[/bold yellow] Move  "
            "[bold yellow]Space[/bold yellow] Toggle  "
            "[bold yellow]i[/bold yellow] Install  "
            "[bold yellow]d[/bold yellow] Uninstall All  "
            "[bold yellow]c[/bold yellow] Cancel  "
            "[bold yellow]q[/bold yellow] Quit",
            justify="center",
        )

    def _get_prefix(self, idx: int, is_selected: bool) -> str:
        cursor = "[bold green]>[/bold green] " if idx == self._cursor else "  "
        mark = "[bold green](*)[/bold green] " if is_selected else "    "
        return cursor + mark
