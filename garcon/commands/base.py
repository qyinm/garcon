from dataclasses import dataclass


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    success: bool
    undo_info: dict | None = None
