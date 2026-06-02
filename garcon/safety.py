from pathlib import Path

from garcon.schema import GarconAction

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

HIGH_RISK_SKILLS: set[str] = {
    "delete_files",
    "organize_files",
    "rename_files",
    "extract_archive",
    "compress_files",
}

DANGEROUS_TOKENS = [
    "rm -rf",
    "sudo",
    "chmod -R 777",
    "mkfs",
    "dd if=",
    "curl | sh",
    "wget | sh",
    "> /dev/",
    ":(){ :|:& };:",
]

PATH_KEYS = {"path", "paths", "source_dir", "target_dir", "archive", "output", "source"}

READ_SKILLS = {"list_files", "read_file", "search_text", "find_large_files"}
WRITE_SKILLS = {"organize_files", "rename_files", "compress_files", "extract_archive"}

WRITE_ZONE_WARNING = "작업 영역을 벗어난 경로입니다. 홈 디렉토리 내에서만 사용 가능합니다."
BLOCKED_ROOT_WARNING = "차단된 시스템 경로입니다: {path}"


def is_under_blocked_root(path: Path) -> bool:
    resolved = path.expanduser().resolve()
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


def path_is_blocked(path_value: str) -> bool:
    try:
        path = Path(path_value).expanduser().resolve()
    except Exception:
        return True

    return is_under_blocked_root(path)


def _is_within_cwd(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    cwd = Path.cwd().resolve()
    try:
        return resolved == cwd or resolved.is_relative_to(cwd)
    except ValueError:
        return False


def _is_within_home(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    home = Path.home().resolve()
    try:
        return resolved == home or resolved.is_relative_to(home)
    except ValueError:
        return False


def iter_paths(value, parent_key: str | None = None):
    if isinstance(value, dict):
        for k, v in value.items():
            if k in PATH_KEYS and isinstance(v, str):
                yield v
            yield from iter_paths(v, parent_key=k)
    elif isinstance(value, list):
        for item in value:
            if parent_key in PATH_KEYS and isinstance(item, str):
                yield item
            yield from iter_paths(item, parent_key=parent_key)


def validate_action(action: GarconAction) -> tuple[bool, str | None]:
    if action.action == "use_skill" and not action.skill:
        return False, "skill이 비어 있습니다."

    if action.skill in HIGH_RISK_SKILLS:
        action.requires_confirmation = True

    if action.action == "use_skill" and action.args:
        args_text = str(action.args)

        for token in DANGEROUS_TOKENS:
            if token in args_text:
                return False, f"위험한 표현이 포함되어 있습니다: {token}"

        for path_val in iter_paths(action.args):
            try:
                p = Path(path_val).expanduser().resolve()
            except Exception:
                continue

            if is_under_blocked_root(p):
                return False, BLOCKED_ROOT_WARNING.format(path=path_val)

            if action.skill in WRITE_SKILLS and not (_is_within_cwd(p) or _is_within_home(p)):
                return False, WRITE_ZONE_WARNING

            if action.skill in READ_SKILLS and not (_is_within_home(p) or _is_within_cwd(p)):
                return False, BLOCKED_ROOT_WARNING.format(path=path_val)

    return True, None
