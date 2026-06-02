import shlex
from pathlib import Path

from garcon.commands.base import CommandResult
from garcon.commands.file_ops import _run


def execute_tar(operation: str, archive: str, files: str = "") -> CommandResult:
    quoted_archive = shlex.quote(archive)

    if operation in ("compress", "create", "czf"):
        if not files:
            return CommandResult(stdout="", stderr="files required for compress", success=False)
        quoted_files = shlex.quote(files)
        return _run(f"tar -czf {quoted_archive} {quoted_files}")

    elif operation in ("extract", "xzf"):
        dest = Path(archive).expanduser().resolve().parent
        dest_quoted = shlex.quote(str(dest))
        return _run(f"tar -xzf {quoted_archive} -C {dest_quoted}")

    elif operation == "list":
        return _run(f"tar -tzf {quoted_archive}")

    return CommandResult(stdout="", stderr=f"Unknown tar operation: {operation}", success=False)
