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
