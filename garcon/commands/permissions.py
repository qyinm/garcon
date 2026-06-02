import os
import shlex
import stat
from pathlib import Path

from garcon.commands.base import CommandResult


def execute_chmod(mode: str, path: str) -> CommandResult:
    try:
        p = Path(path).expanduser().resolve()
        original_mode = p.stat().st_mode

        quoted_path = shlex.quote(str(p))
        result = os.system(f"chmod {mode} {quoted_path}")
        if result != 0:
            return CommandResult(stdout="", stderr=f"chmod failed with exit code {result}", success=False)

        return CommandResult(
            stdout=f"Mode changed to {mode}",
            stderr="",
            success=True,
            undo_info={
                "type": "restore_mode",
                "items": [{"path": str(p), "original_mode": oct(stat.S_IMODE(original_mode))}],
            },
        )
    except Exception as e:
        return CommandResult(stdout="", stderr=str(e), success=False)
