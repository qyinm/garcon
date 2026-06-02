import json
from datetime import datetime
from pathlib import Path

UNDO_DIR = Path("~/.garcon").expanduser()
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


def record_undo(skill: str, undo_data: dict | None):
    if not undo_data:
        return

    entry = {
        "operation_id": datetime.now().strftime("%Y%m%dT%H%M%S"),
        "skill": skill,
        "undo": undo_data,
    }

    log = _read_log()
    log.append(entry)

    if len(log) > MAX_LOG_ENTRIES:
        log = log[-MAX_LOG_ENTRIES:]

    _write_log(log)


def get_latest() -> dict | None:
    log = _read_log()
    if not log:
        return None
    return log[-1]


def pop_latest() -> dict | None:
    log = _read_log()
    if not log:
        return None
    entry = log.pop()
    _write_log(log)
    return entry
