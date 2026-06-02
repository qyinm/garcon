import logging
from typing import Any

from garcon.router import (
    _extract_extensions,
    _extract_path,
    _extract_path_or_filename,
    _extract_query,
    _match_any,
)

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """Korean intent classification.
Answer with exactly one word.

list = 파일 목록, 보여줘, 보기, 찾기
read = 파일 내용 보기, 읽기
search = 검색
organize = 정리, 분류
rename = 이름 바꾸기, 이름 변경
compress = 압축하기
extract = 압축 풀기, 해제, 추출
refuse = 삭제, 지우기
finish = 종료, 그만
greeting = 인사, 안녕
other = 도움말, 설정, 기타

Input: {inp}
Answer (one word):"""

CLASS_GRAMMAR_STRING = (
    'root ::= "list" | "read" | "search" | "organize" | "rename"'
    ' | "compress" | "extract" | "refuse" | "finish" | "greeting" | "other"'
)

_LOW = {"risk": "low", "requires_confirmation": False}
_MED = {"risk": "medium", "requires_confirmation": True}

CLASS_TO_SKILL: dict[str, dict[str, Any]] = {
    "list": {"action": "use_skill", "skill": "list_files", **_LOW},
    "read": {"action": "use_skill", "skill": "read_file", **_LOW},
    "search": {"action": "use_skill", "skill": "search_text", **_LOW},
    "organize": {"action": "use_skill", "skill": "organize_files", **_MED},
    "rename": {"action": "use_skill", "skill": "rename_files", **_MED},
    "compress": {"action": "use_skill", "skill": "compress_files", **_MED},
    "extract": {"action": "use_skill", "skill": "extract_archive", **_MED},
    "refuse": {"action": "refuse", "message": "위험한 요청은 실행할 수 없습니다."},
    "finish": {"action": "finish", "message": "garcon을 종료합니다."},
    "greeting": {
        "action": "show_plan",
        "message": "garcon이 준비됐어요. 파일 목록, 읽기, 검색, 정리를 도와드릴 수 있어요.",
    },
    "other": {"action": "ask_clarification", "message": "어떤 작업을 할지 알려주세요."},
}


CLASS_KEYWORDS = {
    "list": ["목록", "리스트", "파일", "ls", "보여줘", "보기", "찾기", "뭐", "알려줘", "파일들"],
    "read": ["읽", "내용", "열", "cat", "보기"],
    "search": ["찾", "검색", "포함", "grep", "search", "log"],
    "organize": ["정리", "분류", "종류"],
    "rename": ["이름", "rename", "변경", "바꿔"],
    "compress": ["압축", "zip", "tar", "compress"],
    "extract": ["압축 풀", "압축해제", "해제", "unzip", "extract", "추출", "풀어"],
    "refuse": ["삭제", "지우", "제거", "rm", "del", "sudo", "포맷", "format"],
    "finish": ["종료", "그만", "끝", "exit", "quit", "bye", "꺼줘"],
    "greeting": ["안녕", "헬로", "hi", "hello", "시작", "인사"],
    "other": ["도움", "설정", "help", "설명"],
}


def _validate_classification(text: str, classified: str) -> str | None:
    text_lower = text.strip().lower()
    if classified not in CLASS_KEYWORDS:
        return None
    for kw in CLASS_KEYWORDS[classified]:
        if kw in text_lower:
            return classified
    return None


def _post_process_classification(text: str, classified: str) -> str | None:
    if classified == "read":
        if _match_any(text, ["목록", "리스트"]):
            return "list"
    validated = _validate_classification(text, classified)
    if validated is None:
        return None
    return validated


def _build_action(text: str, classified: str) -> dict | None:
    entry = CLASS_TO_SKILL.get(classified)
    if not entry:
        return None

    if entry.get("action") != "use_skill":
        return entry

    text_lower = text.strip().lower()
    skill = entry["skill"]
    args: dict = {}
    message = ""

    if skill == "list_files":
        path = _extract_path(text) or "."
        detail = _match_any(text_lower, ["자세히", "상세", "디테일", "모두", "전부"])
        hidden = _match_any(
            text_lower, ["숨김", "숨긴", "숨겨진", "dot", "hidden", "모든"]
        )
        args = {"path": path, "hidden": hidden, "detail": detail}
        message = (
            "파일 목록을 표시합니다."
            if path == "."
            else f"{path}의 파일 목록을 표시합니다."
        )

    elif skill == "read_file":
        file_path = _extract_path_or_filename(text)
        if not file_path:
            return {
                "action": "ask_clarification",
                "message": "어떤 파일을 읽을까요? 파일 이름을 알려주세요.",
            }
        args = {"path": file_path, "max_lines": 100}
        message = f"{file_path}의 내용을 읽습니다."

    elif skill == "search_text":
        query = _extract_query(text)
        if not query:
            return {
                "action": "ask_clarification",
                "message": "무슨 내용을 검색할까요? 검색어를 알려주세요.",
            }
        search_path = _extract_path(text) or "."
        exts = _extract_extensions(text)
        args = {"path": search_path, "query": query, "include_extensions": exts}
        message = f"'{query}'를 검색합니다."

    elif skill == "organize_files":
        source = _extract_path(text) or "."
        args = {
            "source_dir": source,
            "rules": [
                {"extensions": ["pdf"], "target_dir": f"{source}/PDFs"},
                {
                    "extensions": ["png", "jpg", "jpeg", "webp"],
                    "target_dir": f"{source}/Images",
                },
                {
                    "extensions": ["zip", "tar", "gz", "bz2"],
                    "target_dir": f"{source}/Archives",
                },
            ],
        }
        message = f"{source}를 확장자별로 정리합니다."

    elif skill == "rename_files":
        source = _extract_path(text) or "."
        args = {"source_dir": source, "pattern": "", "replacement": ""}
        message = "파일 이름 변경을 시작합니다."

    elif skill == "compress_files":
        args = {"paths": [], "output": ""}
        message = "파일 압축을 시작합니다."

    elif skill == "extract_archive":
        args = {"archive": "", "target_dir": "."}
        message = "압축 해제를 시작합니다."

    else:
        return None

    return {
        "action": "use_skill",
        "skill": skill,
        "args": args,
        "risk": entry.get("risk", "low"),
        "requires_confirmation": entry.get("requires_confirmation", False),
        "message": message,
    }


class ModelRouter:
    def __init__(self):
        self._llm = None
        self._grammar = None
        self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def load(self, model_path: str):
        try:
            from llama_cpp import Llama, LlamaGrammar

            self._llm = Llama(
                model_path=model_path,
                n_ctx=8192,
                n_gpu_layers=-1,
                verbose=False,
            )
            self._grammar = LlamaGrammar.from_string(CLASS_GRAMMAR_STRING)
            self._available = True
        except Exception as e:
            logger.warning("Failed to load model: %s", e)
            self._available = False

    def route(self, user_input: str) -> dict | None:
        if not self._available or self._llm is None or self._grammar is None:
            return None

        prompt = CLASSIFICATION_PROMPT.format(inp=user_input)

        try:
            response = self._llm.create_completion(
                prompt,
                max_tokens=10,
                temperature=0.0,
                grammar=self._grammar,
                stop=["\n"],
            )
        except Exception as e:
            logger.warning("Model inference failed: %s", e)
            return None

        raw = response["choices"][0]["text"].strip()
        if not raw:
            return None

        classified = _post_process_classification(user_input, raw)
        if classified is None:
            return None
        result = _build_action(user_input, classified)
        if result is not None:
            result["_classification"] = classified
        return result


_model_router_instance: ModelRouter | None = None


def router(user_input: str, model_path: str | None = None) -> dict | None:
    global _model_router_instance
    if _model_router_instance is None:
        instance = ModelRouter()
        if model_path:
            instance.load(model_path)
        _model_router_instance = instance
    return _model_router_instance.route(user_input)
