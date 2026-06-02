import shlex

from garcon.commands.base import CommandResult
from garcon.commands.file_ops import _run


def execute_cat(path: str) -> CommandResult:
    quoted = shlex.quote(path)
    return _run(f"cat {quoted}")


def execute_head(path: str, lines: int = 10) -> CommandResult:
    quoted = shlex.quote(path)
    return _run(f"head -n {lines} {quoted}")


def execute_tail(path: str, lines: int = 10) -> CommandResult:
    quoted = shlex.quote(path)
    return _run(f"tail -n {lines} {quoted}")


def execute_wc(path: str, options: str = "-l") -> CommandResult:
    quoted = shlex.quote(path)
    return _run(f"wc {options} {quoted}")


def execute_diff(path1: str, path2: str) -> CommandResult:
    q1 = shlex.quote(path1)
    q2 = shlex.quote(path2)
    return _run(f"diff {q1} {q2}")
