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


def path_is_blocked(path_value: str) -> bool:
    try:
        path = Path(path_value).expanduser().resolve()
    except Exception:
        return True

    for root in BLOCKED_ROOTS:
        root_path = Path(root).resolve()
        if path == root_path:
            return True

    return False


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

    return True, None
