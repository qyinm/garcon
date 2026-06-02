
def route_with_rules(user_input: str) -> dict:
    text = user_input.strip().lower()

    if not text:
        return {
            "action": "ask_clarification",
            "message": "무슨 작업을 할까요?",
        }

    if _match(text, ["안녕", "헬로", "hi", "hello", "시작"]):
        return {
            "action": "show_plan",
            "message": (
                "garcon이 준비됐어요. 파일 목록, 읽기, 검색, 정리를"
                " 도와드릴 수 있어요."
            ),
        }

    if _match(text, ["종료", "끝", "그만", "꺼줘", "exit", "quit", "bye"]):
        return {
            "action": "finish",
            "message": "garcon을 종료합니다.",
        }

    if _match_any(text, [
        "삭제", "지워", "제거", "rm", "del",
        "sudo", "관리자", "root",
        "포맷", "format",
    ]):
        return {
            "action": "refuse",
            "message": "위험한 요청은 실행할 수 없습니다.",
        }

    if _match_any(text, [
        "용량", "큰 파일", "큰파일",
        "크기", "disk", "disk usage",
        "공간", "space",
    ]):
        path = _extract_path(text) or "."
        return {
            "action": "use_skill",
            "skill": "find_large_files",
            "args": {"path": path, "limit": 20, "min_size_mb": 100},
            "risk": "low",
            "requires_confirmation": False,
            "message": "큰 파일을 검색합니다.",
        }

    if _match_any(text, ["정리", "분류", "종류별"]):
        source = _extract_path(text) or "."
        return {
            "action": "use_skill",
            "skill": "organize_files",
            "args": {
                "source_dir": source,
                "rules": [
                    {
                        "extensions": ["pdf"],
                        "target_dir": _join_path(source, "PDFs"),
                    },
                    {
                        "extensions": ["png", "jpg", "jpeg", "webp"],
                        "target_dir": _join_path(source, "Images"),
                    },
                    {
                        "extensions": ["zip", "tar", "gz", "bz2"],
                        "target_dir": _join_path(source, "Archives"),
                    },
                ],
            },
            "risk": "medium",
            "requires_confirmation": True,
            "message": f"{source}를 확장자별로 정리합니다.",
        }

    if _match_any(text, [
        "이름 변경", "이름 바꿔", "rename",
        "파일명 변경", "파일명 바꿔",
    ]):
        source = _extract_path(text) or "."
        return {
            "action": "use_skill",
            "skill": "rename_files",
            "args": {
                "source_dir": source,
                "pattern": "",
                "replacement": "",
            },
            "risk": "medium",
            "requires_confirmation": True,
            "message": "파일 이름 변경을 시작합니다.",
        }

    if _match_any(text, ["zip", "tar", "압축해", "압축 하"]):
        return {
            "action": "use_skill",
            "skill": "compress_files",
            "args": {"paths": [], "output": ""},
            "risk": "medium",
            "requires_confirmation": True,
            "message": "파일 압축을 시작합니다.",
        }

    if _match_any(text, ["압축 풀어", "압축 해제", "압축풀기", "extract", "unzip"]):
        return {
            "action": "use_skill",
            "skill": "extract_archive",
            "args": {"archive": "", "target_dir": "."},
            "risk": "medium",
            "requires_confirmation": True,
            "message": "압축 해제를 시작합니다.",
        }

    list_patterns = [
        "목록", "리스트", "파일", "뭐가", "보여줘", "보여 주",
        "파일들", "list", "ls",
        "파일 보여줘", "파일 목록",
        "뭐 있어", "뭐가 있어",
    ]
    if _match_any(text, list_patterns):
        args: dict = {"path": ".", "hidden": False, "detail": False}

        if _match_any(text, ["자세히", "상세", "디테일", "모두", "전부"]):
            args["detail"] = True

        if _match_any(text, ["숨김", "숨긴", "숨겨진", "dot", "hidden", "모든"]):
            args["hidden"] = True

        path = _extract_path(text)
        if path:
            args["path"] = path

        return {
            "action": "use_skill",
            "skill": "list_files",
            "args": args,
            "risk": "low",
            "requires_confirmation": False,
            "message": "파일 목록을 표시합니다." if not path
            else f"{path}의 파일 목록을 표시합니다.",
        }

    read_patterns = [
        "읽어줘", "읽기", "내용", "보여줘",
        "파일 내용", "열어줘", "열기",
        "read", "cat", "보기",
    ]
    if _match_any(text, read_patterns):
        file_path = _extract_path_or_filename(text)
        if not file_path:
            return {
                "action": "ask_clarification",
                "message": "어떤 파일을 읽을까요? 파일 이름을 알려주세요.",
            }

        return {
            "action": "use_skill",
            "skill": "read_file",
            "args": {"path": file_path, "max_lines": 100},
            "risk": "low",
            "requires_confirmation": False,
            "message": f"{file_path}의 내용을 읽습니다.",
        }

    search_patterns = [
        "찾아줘", "검색", "찾기", "포함된", "포함하는",
        "search", "find", "grep",
        "있는 줄", "들어간", "들어있는",
    ]
    if _match_any(text, search_patterns):
        query = _extract_query(text)
        if not query:
            return {
                "action": "ask_clarification",
                "message": "무슨 내용을 검색할까요? 검색어를 알려주세요.",
            }

        search_path = _extract_path(text) or "."
        exts = _extract_extensions(text)

        return {
            "action": "use_skill",
            "skill": "search_text",
            "args": {
                "path": search_path,
                "query": query,
                "include_extensions": exts,
            },
            "risk": "low",
            "requires_confirmation": False,
            "message": f"'{query}'를 검색합니다.",
        }

    return {
        "action": "ask_clarification",
        "message": "어떤 작업을 할지 조금 더 구체적으로 알려주세요.\n\n"
        "예: '파일 목록 보여줘', '파일 읽어줘', 'log에서 error 찾아줘', "
        "'다운로드 폴더 정리해줘'",
    }


def _match(text: str, keywords: list[str]) -> bool:
    return text.strip() in keywords


def _match_any(text: str, keywords: list[str]) -> bool:
    for kw in keywords:
        if kw in text:
            return True
    return False


def _join_path(base: str, sub: str) -> str:
    if base in (".", "~"):
        return f"{base}/{sub}"
    return f"{base}/{sub}"


def _extract_path(text: str) -> str | None:
    path_hints = {
        "다운로드": "~/Downloads",
        "download": "~/Downloads",
        "홈": "~",
        "home": "~",
        "문서": "~/Documents",
        "documents": "~/Documents",
        "데스크탑": "~/Desktop",
        "바탕화면": "~/Desktop",
        "desktop": "~/Desktop",
    }

    text_lower = text.lower()
    for keyword, path in path_hints.items():
        if keyword in text_lower:
            return path

    return None


def _extract_path_or_filename(text: str) -> str | None:
    import re

    patterns = [
        r"[\"']([^\"']+)[\"']",
        r"`([^`]+)`",
        r"(?:파일\s*:?\s*)(\S+)",
        r"(?:읽[을아]줘\s*)(\S+)",
        r"(?:열[어아]줘\s*)(\S+)",
    ]

    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)

    words = text.split()
    for w in words:
        if "." in w and not w.startswith("-"):
            return w

    return None


def _extract_query(text: str) -> str | None:
    import re

    m = re.search(r"[\"']([^\"']+)[\"']", text)
    if m:
        return m.group(1)

    m = re.search(r"`([^`]+)`", text)
    if m:
        return m.group(1)

    stop_words = {
        "줄", "것", "파일", "파일을", "파일이", "파일의",
        "내용", "거", "목록", "리스트",
    }

    m = re.search(r"(\S+)\s*(?:포함된|포함하는|들어간|들어있는)", text)
    if m and m.group(1) not in stop_words:
        return m.group(1)

    m = re.search(r"(\S+)\s*(?:찾아줘|찾기|검색|찾아|서치)", text)
    if m and m.group(1) not in stop_words:
        return m.group(1)

    m = re.search(r"(?:찾아줘|찾기|검색|찾아|서치)\s*(\S+)", text)
    if m and m.group(1) not in stop_words:
        return m.group(1)

    m = re.search(r"(?:포함된|포함하는|들어간|들어있는)\s*(\S+)", text)
    if m and m.group(1) not in stop_words:
        return m.group(1)

    return None


def _extract_extensions(text: str) -> list[str] | None:
    import re

    m = re.search(r"(\w+)(?:에서|에)", text)
    if m:
        ext_text = m.group(1).lower()
        ext_map = {
            "파이썬": ["py"],
            "python": ["py"],
            "로그": ["log", "txt"],
            "log": ["log"],
            "텍스트": ["txt"],
            "text": ["txt"],
            "자바스크립트": ["js", "ts"],
            "javascript": ["js", "ts"],
            "타입스크립트": ["ts"],
            "typescript": ["ts"],
        }
        if ext_text in ext_map:
            return ext_map[ext_text]

    return None
