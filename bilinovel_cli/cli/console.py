"""Rich console output."""

from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.progress import TaskProgressColumn


class ConsoleProgress:
    def __init__(self):
        self.console = Console()
        self.progress: Optional[Progress] = None
        self.task_id: Optional[int] = None

    def start(self, total: int, description: str = "Downloading..."):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        )
        self.progress.start()
        self.task_id = self.progress.add_task(description, total=total)

    def update(self, current: int, description: str = ""):
        if self.progress and self.task_id is not None:
            self.progress.update(
                self.task_id, completed=current, description=description
            )

    def start_chapter_download(self, total: int):
        self.stop()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        )
        self.progress.start()
        self.task_id = self.progress.add_task("Starting download...", total=total)

    def update_chapter(self, current: int, chapter_name: str):
        if self.progress and self.task_id is not None:
            self.progress.update(
                self.task_id,
                completed=current,
                description=f"Downloading: {chapter_name}",
            )

    def stop(self):
        if self.progress:
            self.progress.stop()
            self.progress = None
            self.task_id = None

    def print(self, message: str, style: str = ""):
        if style:
            self.console.print(f"[{style}]{message}[/{style}]")
        else:
            self.console.print(message)

    def print_info(self, message: str):
        self.print(message, style="blue")

    def print_success(self, message: str):
        self.print(message, style="green")

    def print_error(self, message: str):
        self.print(message, style="red bold")

    def print_warning(self, message: str):
        self.print(message, style="yellow")
