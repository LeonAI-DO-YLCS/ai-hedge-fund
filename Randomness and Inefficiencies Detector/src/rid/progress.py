from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


@dataclass
class DetectorProgress:
    total: int
    description: str = "Starting"

    def __post_init__(self) -> None:
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
        )
        self.task_id: TaskID | None = None

    def __enter__(self) -> "DetectorProgress":
        self.progress.start()
        self.task_id = self.progress.add_task(self.description, total=self.total)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.progress.stop()

    def add_total(self, increment: int) -> None:
        if self.task_id is not None:
            task = self.progress.tasks[0]
            self.progress.update(self.task_id, total=(task.total or 0) + increment)

    def advance(self, description: str, step: int = 1) -> None:
        if self.task_id is not None:
            self.progress.update(self.task_id, description=description, advance=step)

    def note(self, description: str) -> None:
        if self.task_id is not None:
            self.progress.update(self.task_id, description=description)
