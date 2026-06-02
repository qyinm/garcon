import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

UNDO_DIR = Path("~/.garcon").expanduser()
TRASH_DIR = UNDO_DIR / "trash"
UNDO_FILE = UNDO_DIR / "undo_log.json"
MAX_LOG_ENTRIES = 100


def _ensure_dir():
    UNDO_DIR.mkdir(parents=True, exist_ok=True)


def _read_log() -> list[dict]:
    if not UNDO_FILE.exists():
        return []
    try:
        data = UNDO_FILE.read_text(encoding="utf-8").strip()
        if not data:
            return []
        return json.loads(data)
    except (json.JSONDecodeError, OSError):
        return []


def _write_log(entries: list[dict]):
    _ensure_dir()
    UNDO_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def record_undo(command: str, params: dict, undo_info: dict | None):
    if not undo_info:
        return

    entry = {
        "id": uuid.uuid4().hex[:12],
        "timestamp": datetime.now().isoformat(timespec="milliseconds"),
        "command": command,
        "params": params,
        "type": undo_info["type"],
        "items": undo_info.get("items", []),
    }

    log = _read_log()
    log.append(entry)

    if len(log) > MAX_LOG_ENTRIES:
        log = log[-MAX_LOG_ENTRIES:]

    _write_log(log)


def undo_last() -> bool:
    log = _read_log()
    if not log:
        return False

    entry = log.pop()
    _apply_undo(entry)
    _write_log(log)
    return True


def trash_list() -> list[dict]:
    if not TRASH_DIR.exists():
        return []

    items = []
    for trash_subdir in sorted(TRASH_DIR.iterdir()):
        if trash_subdir.is_dir():
            for f in trash_subdir.iterdir():
                if f.name == "_manifest.json":
                    continue
                items.append({
                    "id": trash_subdir.name,
                    "trash_path": str(f),
                    "original_name": f.name,
                })
    return items


def trash_restore(trash_id: str) -> bool:
    if not TRASH_DIR.exists():
        return False

    target = TRASH_DIR / trash_id
    if not target.exists() or not target.is_dir():
        return False

    manifest_file = target / "_manifest.json"
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        for item in manifest:
            src = Path(item["trash_path"])
            dst = Path(item["original_path"])
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
    else:
        for f in target.iterdir():
            original_path = Path.home() / f.name
            original_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(original_path))

    shutil.rmtree(str(target))
    return True


def _apply_undo(entry: dict):
    undo_type = entry.get("type", "")
    items = entry.get("items", [])

    if undo_type == "restore_trash":
        for item in items:
            trash_path = Path(item["trash_path"])
            original_path = Path(item["original_path"])
            if trash_path.exists():
                original_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(trash_path), str(original_path))

    elif undo_type == "reverse_mv":
        for item in items:
            src = Path(item["from"])
            dst = Path(item["to"])
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))

    elif undo_type == "restore_mode":
        for item in items:
            path = Path(item["path"])
            if path.exists():
                mode = int(item["original_mode"], 8)
                path.chmod(mode)

    elif undo_type == "restore_backup":
        for item in items:
            backup_dir = Path(item["backup_dir"])
            original_path = Path(item["original_path"])
            if backup_dir.exists():
                for f in backup_dir.iterdir():
                    shutil.copy2(str(f), str(original_path))
                shutil.rmtree(str(backup_dir))
