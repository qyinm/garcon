import shlex

from garcon.commands.base import CommandResult
from garcon.commands.file_ops import _run


def execute_sort(path: str) -> CommandResult:
    quoted = shlex.quote(path)
    return _run(f"sort {quoted}")


def execute_uniq(path: str) -> CommandResult:
    quoted = shlex.quote(path)
    return _run(f"uniq {quoted}")
