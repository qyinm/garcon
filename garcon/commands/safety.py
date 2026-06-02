from dataclasses import dataclass
from pathlib import Path

from garcon.commands import get_safety

KNOWN_DANGER: dict[str, str] = {
    "rm_command": "high",
    "chmod_command": "high",
    "mv_command": "medium",
    "cp_command": "medium",
    "mkdir_command": "low",
    "tar_command": "medium",
}

BLOCKED_ROOTS = [
    "/",
    "/bin",
    "/sbin",
    "/usr",
    "/etc",
    "/System",
    "/Library",
    "/private",
    "/var",
]

BLOCKED_COMMANDS: set[str] = {"sudo", "su", "passwd", "kill", "pkill", "reboot", "shutdown", "init", "systemctl"}

DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "chmod 777 /",
    "chmod -R 777 /",
    "mkfs",
    "dd if=",
    "curl | sh",
    "wget | sh",
    ":(){ :|:& };:",
    "> /dev/",
    "> /dev/sda",
    "| sh",
    "| bash",
]

PATH_KEYS = {"path", "paths", "source", "destination", "archive", "files", "name"}


@dataclass
class SafetyVerdict:
    allowed: bool
    reason: str | None = None
    requires_confirm: bool = False
    undo_info: dict | None = None


def is_blocked_command(command_name: str) -> bool:
    base = command_name.replace("_command", "")
    return base in BLOCKED_COMMANDS


def _iter_param_values(params: dict) -> list[str]:
    values: list[str] = []
    for k, v in params.items():
        if isinstance(v, str):
            values.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    values.append(item)
    return values


def has_dangerous_pattern(params: dict) -> str | None:
    param_str = str(params)
    for pattern in DANGEROUS_PATTERNS:
        if pattern in param_str:
            return pattern
    return None


def is_blocked_path(path_value: str) -> bool:
    try:
        path = Path(path_value).expanduser().resolve()
    except Exception:
        return True

    resolved = path
    for root in BLOCKED_ROOTS:
        root_path = Path(root).resolve()
        if resolved == root_path:
            return True
        if root_path == Path("/").resolve():
            continue
        try:
            if resolved.is_relative_to(root_path):
                return True
        except ValueError:
            pass
    return False


def _find_blocked_paths(params: dict) -> list[str]:
    blocked: list[str] = []
    for k, v in params.items():
        if k in PATH_KEYS and isinstance(v, str) and is_blocked_path(v):
            blocked.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str) and k in PATH_KEYS and is_blocked_path(item):
                    blocked.append(item)
    return blocked


def validate_command(name: str, params: dict) -> SafetyVerdict:
    if is_blocked_command(name):
        return SafetyVerdict(allowed=False, reason=f"차단된 명령어입니다: {name}")

    pattern = has_dangerous_pattern(params)
    if pattern:
        return SafetyVerdict(allowed=False, reason=f"위험한 패턴이 포함되어 있습니다: {pattern}")

    blocked_paths = _find_blocked_paths(params)
    if blocked_paths:
        return SafetyVerdict(
            allowed=False,
            reason=f"차단된 시스템 경로입니다: {blocked_paths[0]}",
        )

    danger = KNOWN_DANGER.get(name, get_safety(name).get("danger", "low"))
    requires_confirm = danger in ("high", "medium")

    return SafetyVerdict(
        allowed=True,
        requires_confirm=requires_confirm,
    )
