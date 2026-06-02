import shlex
import subprocess

from garcon.commands.base import CommandResult


def _run(cmd: str) -> CommandResult:
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
        )
        return CommandResult(
            stdout=result.stdout.rstrip("\n"),
            stderr=result.stderr.rstrip("\n"),
            success=result.returncode == 0,
        )
    except Exception as e:
        return CommandResult(stdout="", stderr=str(e), success=False)


def execute_ls(path: str = ".", options: str = "-la") -> CommandResult:
    quoted = shlex.quote(path)
    return _run(f"ls {options} {quoted}")


def execute_tree(path: str = ".") -> CommandResult:
    quoted = shlex.quote(path)
    return _run(f"ls -R {quoted}")


def execute_mkdir(path: str) -> CommandResult:
    quoted = shlex.quote(path)
    return _run(f"mkdir -p {quoted}")


def execute_cp(source: str, destination: str) -> CommandResult:
    import shutil
    import tempfile
    from pathlib import Path

    src_path = Path(source).expanduser().resolve()
    if not src_path.exists():
        return CommandResult(stdout="", stderr=f"Source does not exist: {source}", success=False)

    dest_path = Path(destination).expanduser().resolve()
    overwriting = dest_path.exists()

    undo_info = None
    if overwriting:
        backup_dir = Path(tempfile.mkdtemp(prefix="garcon_cp_backup_"))
        shutil.copy2(str(dest_path), str(backup_dir / dest_path.name))
        undo_info = {
            "type": "restore_backup",
            "items": [{"backup_dir": str(backup_dir), "original_path": str(dest_path)}],
        }

    qs = shlex.quote(source)
    qd = shlex.quote(destination)
    result = _run(f"cp {qs} {qd}")
    return CommandResult(
        stdout=f"Copied {source} → {destination}",
        stderr=result.stderr,
        success=result.success,
        undo_info=undo_info,
    )


def execute_mv(source: str, destination: str) -> CommandResult:
    try:
        from pathlib import Path

        src_path = Path(source).expanduser().resolve()
        dst_path = Path(destination).expanduser().resolve()

        if not src_path.exists():
            return CommandResult(stdout="", stderr=f"Source does not exist: {source}", success=False)

        undo_info = {
            "type": "reverse_mv",
            "items": [{"from": str(dst_path), "to": str(src_path)}],
        }

        qs = shlex.quote(source)
        qd = shlex.quote(destination)
        result = _run(f"mv {qs} {qd}")
        return CommandResult(
            stdout=result.stdout,
            stderr=result.stderr,
            success=result.success,
            undo_info=undo_info,
        )
    except Exception as e:
        return CommandResult(stdout="", stderr=str(e), success=False)


def execute_rm(path: str, recursive: bool = False) -> CommandResult:
    import shutil
    import uuid
    from datetime import datetime
    from pathlib import Path

    src = Path(path).expanduser().resolve()
    if not src.exists():
        return CommandResult(stdout="", stderr=f"Path does not exist: {path}", success=False)

    trash_name = f"{datetime.now().strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
    trash_dir = Path.home() / ".garcon" / "trash" / trash_name
    trash_dir.mkdir(parents=True, exist_ok=True)

    dest_in_trash = trash_dir / src.name
    shutil.move(str(src), str(dest_in_trash))

    manifest = trash_dir / "_manifest.json"
    manifest.write_text(
        __import__("json").dumps([{"original_path": str(src), "trash_path": str(dest_in_trash)}])
    )

    return CommandResult(
        stdout=f"Moved {path} to trash",
        stderr="",
        success=True,
        undo_info={
            "type": "restore_trash",
            "items": [{"trash_path": str(dest_in_trash), "original_path": str(src)}],
        },
    )
