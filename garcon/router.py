import re


def route_with_rules(user_input: str) -> dict:
    text = user_input.strip()

    if not text:
        return {"action": "ask_clarification", "message": "무슨 작업을 할까요?"}

    if _match_any(text, ["종료", "끝", "그만", "exit", "quit", "bye"]):
        return {"action": "finish", "message": "garcon을 종료합니다."}

    if _match_any(text, ["안녕", "헬로", "hi", "hello", "시작"]):
        return {"action": "show_plan", "message": "garcon이 준비됐어요."}

    if _match_any(text, ["sudo", "관리자", "root", "포맷", "format"]):
        return {"action": "refuse", "message": "위험한 요청은 실행할 수 없습니다."}

    cmd = _route_command(text)
    if cmd:
        return cmd

    return {
        "action": "ask_clarification",
        "message": "어떤 작업을 할지 더 구체적으로 알려주세요.\n"
        "예: '파일 목록', 'test.txt 내용', 'error 찾아줘', 'py파일 찾아줘'",
    }


def _route_command(text: str) -> dict | None:
    result = _try_head_tail(text)
    if result:
        return result
    result = _try_wc(text)
    if result:
        return result
    result = _try_ls(text)
    if result:
        return result
    result = _try_cat(text)
    if result:
        return result
    result = _try_grep(text)
    if result:
        return result
    result = _try_find(text)
    if result:
        return result
    result = _try_rm(text)
    if result:
        return result
    result = _try_cp_mv(text)
    if result:
        return result
    result = _try_mkdir(text)
    if result:
        return result
    result = _try_tar(text)
    if result:
        return result
    result = _try_chmod(text)
    if result:
        return result
    result = _try_sort_uniq_diff(text)
    if result:
        return result
    result = _try_tree(text)
    if result:
        return result
    result = _try_cd(text)
    if result:
        return result
    return None


def _extract_path(text: str) -> str | None:
    path_hints = {
        "다운로드": "~/Downloads", "download": "~/Downloads",
        "홈": "~", "home": "~",
        "문서": "~/Documents", "documents": "~/Documents",
        "데스크탑": "~/Desktop", "바탕화면": "~/Desktop", "desktop": "~/Desktop",
    }
    tl = text.lower()
    for kw, p in path_hints.items():
        if kw in tl:
            return p

    m = re.search(r"(\S+)\s*폴더", text)
    if m:
        return m.group(1)

    m = re.search(r"[\"']([^\"']+)[\"']", text)
    if m and (".txt" in m.group(1) or ".py" in m.group(1) or ".log" in m.group(1) or "/" in m.group(1)):
        return m.group(1)

    return None


def _extract_filename(text: str) -> str | None:
    m = re.search(r"[\"']([^\"']+)[\"']", text)
    if m:
        return m.group(1)
    words = text.split()
    for w in words:
        c = w.strip(".,!?")
        if "." in c and not c.startswith(("-", "–", "—")):
            return c
    return None


def _try_ls(text: str) -> dict | None:
    if not _match_any(text, ["목록", "리스트", "파일", "뭐가", "list", "ls", "파일 보여줘", "파일 목록"]):
        return None
    path = _extract_path(text) or "."
    return {
        "action": "use_skill", "skill": "list_files",
        "args": {"path": path, "detail": False, "hidden": False},
        "risk": "low", "requires_confirmation": False,
        "message": f"{path}의 파일 목록을 표시합니다.",
    }


def _try_cat(text: str) -> dict | None:
    if not _match_any(text, ["읽어줘", "읽기", "내용", "열어줘", "열기", "read", "cat", "보기"]):
        return None
    f = _extract_filename(text)
    if not f:
        return {"action": "ask_clarification", "message": "어떤 파일을 읽을까요? 파일 이름을 알려주세요."}
    return {
        "action": "use_skill", "skill": "read_file",
        "args": {"path": f, "max_lines": 100},
        "risk": "low", "requires_confirmation": False,
        "message": f"{f}의 내용을 읽습니다.",
    }


def _try_grep(text: str) -> dict | None:
    if not _match_any(text, ["찾아줘", "검색", "찾기", "포함된", "포함하는", "search", "grep"]):
        return None
    query = _extract_query(text)
    if not query:
        return {"action": "ask_clarification", "message": "무슨 내용을 검색할까요? 검색어를 알려주세요."}
    path = _extract_path(text) or "."
    return {
        "action": "use_skill", "skill": "search_text",
        "args": {"path": path, "query": query},
        "risk": "low", "requires_confirmation": False,
        "message": f"'{query}'를 검색합니다.",
    }


def _try_find(text: str) -> dict | None:
    if not _match_any(text, ["파일 찾아줘", "파일 찾기", "파일검색", ".py 파일", ".txt 파일", "확장자"]):
        return None
    path = _extract_path(text) or "."
    m = re.search(r"\.(\w+)\s*파일", text)
    ext = f"*.{m.group(1)}" if m else ""
    return {
        "action": "use_skill", "skill": "find_large_files",
        "args": {"path": path, "name": ext, "limit": 20},
        "risk": "low", "requires_confirmation": False,
        "message": f"{path}에서 {ext} 파일을 검색합니다. " if ext else f"{path}에서 파일을 검색합니다.",
    }


def _try_wc(text: str) -> dict | None:
    if not _match_any(text, ["몇 줄", "줄 수", "라인 수", "line", "줄이야"]):
        return None
    f = _extract_filename(text)
    if not f:
        return None
    return {
        "action": "use_skill", "skill": "wc_command",
        "args": {"path": f, "options": "-l"},
        "risk": "low", "requires_confirmation": False,
    }


def _try_head_tail(text: str) -> dict | None:
    is_tail = _match_any(text, ["마지막", "끝", "tail"])
    is_head = not is_tail and _match_any(text, ["처음", "앞", "head"])
    if not is_head and not is_tail:
        return None
    f = _extract_filename(text)
    if not f:
        return None
    m = re.search(r"(\d+)\s*줄", text)
    lines = int(m.group(1)) if m else 10
    skill = "tail_command" if is_tail else "head_command"
    return {
        "action": "use_skill", "skill": skill,
        "args": {"path": f, "lines": lines},
        "risk": "low", "requires_confirmation": False,
    }


def _try_rm(text: str) -> dict | None:
    if not _match_any(text, ["삭제", "지워", "제거", "del", "rm "]):
        return None
    f = _extract_filename(text)
    if not f:
        return None
    return {
        "action": "use_skill", "skill": "rm_command",
        "args": {"path": f},
        "risk": "high", "requires_confirmation": True,
    }


def _try_cp_mv(text: str) -> dict | None:
    is_cp = _match_any(text, ["복사", "copy", "cp "])
    is_mv = not is_cp and _match_any(text, ["이동", "옮겨", "mv ", "move", "이름 변경", "rename"])
    if not is_cp and not is_mv:
        return None

    words = text.split()
    filenames = [w.strip(".,!?") for w in words if "." in w and not w.startswith(("-", "–", "—"))]

    if is_cp:
        if len(filenames) >= 2:
            return {
                "action": "use_skill", "skill": "cp_command",
                "args": {"source": filenames[0], "destination": filenames[1]},
                "risk": "medium", "requires_confirmation": True,
            }
        if len(filenames) == 1:
            return {
                "action": "use_skill", "skill": "cp_command",
                "args": {"source": filenames[0], "destination": f"{filenames[0]}.backup"},
                "risk": "medium", "requires_confirmation": True,
            }
        return {"action": "ask_clarification", "message": "어떤 파일을 복사할까요?"}

    if is_mv:
        if len(filenames) >= 2:
            return {
                "action": "use_skill", "skill": "mv_command",
                "args": {"source": filenames[0], "destination": filenames[1]},
                "risk": "medium", "requires_confirmation": True,
            }
        if len(filenames) == 1:
            return {
                "action": "use_skill", "skill": "mv_command",
                "args": {"source": filenames[0]},
                "risk": "medium", "requires_confirmation": True,
            }
        return {"action": "ask_clarification", "message": "어떤 파일을 이동할까요?"}
    return None


def _try_mkdir(text: str) -> dict | None:
    if not _match_any(text, ["폴더 만들어", "디렉토리 만들어", "mkdir", "새 폴더", "만들어줘"]):
        return None
    path = _extract_path(text)
    if not path:
        return {"action": "ask_clarification", "message": "어떤 폴더를 만들까요?"}
    return {
        "action": "use_skill", "skill": "mkdir_command",
        "args": {"path": path},
        "risk": "low", "requires_confirmation": False,
    }


def _try_tar(text: str) -> dict | None:
    is_extract = _match_any(text, ["압축 풀어", "압축 해제", "압축풀기", "extract", "unzip"])
    is_compress = not is_extract and _match_any(text, ["압축해", "압축 하", "zip", "tar", "compress"])
    if not is_extract and not is_compress:
        return None
    f = _extract_filename(text)
    if not f:
        return {"action": "ask_clarification", "message": "어떤 파일을 압축/해제할까요?"}
    if is_extract:
        return {
            "action": "use_skill", "skill": "tar_command",
            "args": {"operation": "extract", "archive": f},
            "risk": "medium", "requires_confirmation": True,
        }
    return {
        "action": "use_skill", "skill": "tar_command",
        "args": {"operation": "compress", "archive": f"{f}.tar.gz", "files": f},
        "risk": "medium", "requires_confirmation": True,
    }


def _try_chmod(text: str) -> dict | None:
    m = re.search(r"chmod\s+(\d+)\s+(\S+)", text)
    if not m:
        return None
    return {
        "action": "use_skill", "skill": "chmod_command",
        "args": {"mode": m.group(1), "path": m.group(2)},
        "risk": "high", "requires_confirmation": True,
    }


def _try_sort_uniq_diff(text: str) -> dict | None:
    if _match_any(text, ["정렬", "sort"]):
        f = _extract_filename(text)
        if not f:
            return None
        return {"action": "use_skill", "skill": "sort_command", "args": {"path": f}, "risk": "low", "requires_confirmation": False}
    if _match_any(text, ["중복 제거", "중복 제거해", "uniq"]):
        f = _extract_filename(text)
        if not f:
            return None
        return {"action": "use_skill", "skill": "uniq_command", "args": {"path": f}, "risk": "low", "requires_confirmation": False}
    if _match_any(text, ["비교", "diff", "차이"]):
        f = _extract_filename(text)
        if not f:
            return None
        return {"action": "use_skill", "skill": "diff_command", "args": {"path1": f, "path2": ""}, "risk": "low", "requires_confirmation": False}
    return None


def _try_tree(text: str) -> dict | None:
    if not _match_any(text, ["트리", "tree", "구조"]):
        return None
    path = _extract_path(text) or "."
    return {
        "action": "use_skill", "skill": "tree_command",
        "args": {"path": path},
        "risk": "low", "requires_confirmation": False,
    }


def _try_cd(text: str) -> dict | None:
    if not _match_any(text, ["이동", "cd ", "들어가", "폴더 이동"]):
        return None
    path = _extract_path(text)
    if not path:
        return None
    return {
        "action": "use_skill", "skill": "cd_command",
        "args": {"path": path},
        "risk": "low", "requires_confirmation": False,
    }


def _match_any(text: str, keywords: list[str]) -> bool:
    tl = text.lower()
    for kw in keywords:
        if kw.lower() in tl:
            return True
    return False


def _extract_query(text: str) -> str | None:
    m = re.search(r"[\"']([^\"']+)[\"']", text)
    if m:
        return m.group(1)
    m = re.search(r"`([^`]+)`", text)
    if m:
        return m.group(1)
    stop = {"줄", "것", "파일", "파일을", "파일이", "파일의", "내용", "거", "목록", "리스트"}
    m = re.search(r"(\S+)\s*(?:포함된|포함하는|들어간|들어있는)", text)
    if m and m.group(1) not in stop:
        return m.group(1)
    m = re.search(r"(\S+)\s*(?:찾아줘|찾기|검색|찾아)", text)
    if m and m.group(1) not in stop:
        return m.group(1)
    m = re.search(r"(?:찾아줘|찾기|검색|찾아)\s*(\S+)", text)
    if m and m.group(1) not in stop:
        return m.group(1)
    m = re.search(r"(?:포함된|포함하는|들어간|들어있는)\s*(\S+)", text)
    if m and m.group(1) not in stop:
        return m.group(1)
    return None


def _extract_extensions(text: str) -> list[str] | None:
    m = re.search(r"(\w+)(?:에서|에)", text)
    if not m:
        return None
    ext_text = m.group(1).lower()
    ext_map = {
        "파이썬": ["py"], "python": ["py"],
        "로그": ["log", "txt"], "log": ["log"],
        "텍스트": ["txt"], "text": ["txt"],
        "자바스크립트": ["js", "ts"], "javascript": ["js", "ts"],
        "타입스크립트": ["ts"], "typescript": ["ts"],
    }
    return ext_map.get(ext_text)
