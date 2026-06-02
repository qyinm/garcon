import shlex

from garcon.commands.base import CommandResult
from garcon.commands.file_ops import _run


def execute_grep(pattern: str, path: str = ".") -> CommandResult:
    quoted_path = shlex.quote(path)
    quoted_pattern = shlex.quote(pattern)
    return _run(f"grep -n {quoted_pattern} {quoted_path}")


def execute_find(path: str = ".", name: str = "") -> CommandResult:
    quoted_path = shlex.quote(path)
    if name:
        quoted_name = shlex.quote(name)
        return _run(f"find {quoted_path} -name {quoted_name}")
    return _run(f"find {quoted_path}")
