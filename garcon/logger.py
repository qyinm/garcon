import json
from datetime import datetime
from pathlib import Path

SESSION_DIR = Path("~/.garcon").expanduser()
SESSION_FILE = SESSION_DIR / "session_log.jsonl"

MAX_ENTRIES = 1000


def _ensure_dir():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)


def log_entry(
    user_input: str,
    router: str,
    classification: str | None = None,
    action: str | None = None,
    skill: str | None = None,
    args: dict | None = None,
    risk: str | None = None,
    result_type: str | None = None,
    message: str | None = None,
):
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "input": user_input,
        "router": router,
    }
    if classification is not None:
        entry["classification"] = classification
    if action is not None:
        entry["action"] = action
    if skill is not None:
        entry["skill"] = skill
    if args:
        entry["args"] = args
    if risk is not None:
        entry["risk"] = risk
    if result_type is not None:
        entry["result"] = result_type
    if message is not None:
        entry["message"] = message

    _ensure_dir()
    entries = _read_all()
    entries.append(entry)
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    _write_all(entries)


def _read_all() -> list[dict]:
    if not SESSION_FILE.exists():
        return []
    try:
        lines = SESSION_FILE.read_text(encoding="utf-8").strip().split("\n")
        return [json.loads(line) for line in lines if line.strip()]
    except (json.JSONDecodeError, OSError):
        return []


def _write_all(entries: list[dict]):
    _ensure_dir()
    SESSION_FILE.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in entries),
        encoding="utf-8",
    )


def get_recent(limit: int = 20) -> list[dict]:
    entries = _read_all()
    return entries[-limit:]


def clear():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
