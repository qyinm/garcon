from garcon.router import route_with_rules


def test_list_files():
    result = route_with_rules("파일 목록 보여줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "list_files"


def test_list_files_with_detail():
    result = route_with_rules("자세히 보여줘")
    assert result["skill"] == "list_files"
    assert result["args"]["detail"] is True


def test_read_file():
    result = route_with_rules("pyproject.toml 내용 읽어줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "read_file"


def test_search_text():
    result = route_with_rules("error 찾아줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "search_text"


def test_refuse_delete():
    result = route_with_rules("파일 삭제해줘")
    assert result["action"] == "refuse"


def test_refuse_sudo():
    result = route_with_rules("sudo 실행")
    assert result["action"] == "refuse"


def test_finish():
    result = route_with_rules("종료")
    assert result["action"] == "finish"


def test_hello():
    result = route_with_rules("안녕")
    assert result["action"] == "show_plan"


def test_clarification():
    result = route_with_rules("아무말 대잔치")
    assert result["action"] == "ask_clarification"


def test_empty_input():
    result = route_with_rules("")
    assert result["action"] == "ask_clarification"


def test_find_large_files():
    result = route_with_rules("큰 파일 찾아줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "find_large_files"


def test_find_large_files_disk():
    result = route_with_rules("용량 확인")
    assert result["skill"] == "find_large_files"


def test_organize_files():
    result = route_with_rules("다운로드 폴더 정리해줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "organize_files"
    assert result["args"]["source_dir"] == "~/Downloads"
    assert result["requires_confirmation"] is True


def test_rename_files():
    result = route_with_rules("파일 이름 변경해줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "rename_files"


def test_compress_files():
    result = route_with_rules("파일 압축해줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "compress_files"


def test_extract_archive():
    result = route_with_rules("압축 풀어줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "extract_archive"


def test_search_with_extension():
    result = route_with_rules("python에서 error 찾아줘")
    assert result["skill"] == "search_text"
    assert result["args"]["include_extensions"] == ["py"]


def test_search_log_extension():
    result = route_with_rules("log에서 error 찾아줘")
    assert result["skill"] == "search_text"
    assert result["args"]["include_extensions"] == ["log"]
