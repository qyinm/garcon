import json

from pydantic import ValidationError

from garcon.schema import GarconAction

PATH_ALIASES = {
    "다운로드": "~/Downloads",
    "다운로드 폴더": "~/Downloads",
    "downloads": "~/Downloads",
    "바탕화면": "~/Desktop",
    "데스크탑": "~/Desktop",
    "desktop": "~/Desktop",
    "문서": "~/Documents",
    "documents": "~/Documents",
    "현재 폴더": ".",
    "여기": ".",
    "현재 디렉토리": ".",
    "현재 디렉터리": ".",
    "홈": "~",
    "홈 폴더": "~",
    "home": "~",
}


def normalize_path(value: str) -> str:
    stripped = value.strip()
    if stripped in PATH_ALIASES:
        return PATH_ALIASES[stripped]
    return stripped


def normalize_args(args: dict) -> dict:
    path_keys = {"path", "source_dir", "target_dir", "archive", "source"}

    for key in list(args.keys()):
        val = args[key]
        if key in path_keys and isinstance(val, str):
            args[key] = normalize_path(val)

    rules = args.get("rules", [])
    if isinstance(rules, list):
        for rule in rules:
            if isinstance(rule, dict):
                td = rule.get("target_dir")
                if isinstance(td, str):
                    rule["target_dir"] = normalize_path(td)

    return args


def parse_action(raw: str | dict) -> tuple[GarconAction | None, str | None]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as e:
            return None, f"JSON 파싱 실패: {e}"

    if not isinstance(raw, dict):
        return None, "출력이 JSON 객체가 아닙니다."

    raw["args"] = normalize_args(raw.get("args", {}))

    try:
        action = GarconAction.model_validate(raw)
    except ValidationError as e:
        return None, f"스키마 검증 실패: {e}"

    return action, None
