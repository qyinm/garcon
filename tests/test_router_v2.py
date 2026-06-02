from garcon.router import route_with_rules


def test_ls_folder():
    result = route_with_rules("tests 폴더 ls 해줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "list_files"
    assert "tests" in str(result["args"])


def test_cat_file():
    result = route_with_rules("test.txt 내용 읽어줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "read_file"


def test_grep():
    result = route_with_rules("error 찾아줘")
    assert result["skill"] == "search_text"


def test_wc():
    result = route_with_rules("test.py 몇 줄이야")
    assert result["skill"] == "wc_command"


def test_tail():
    result = route_with_rules("test.log 마지막 5줄 보여줘")
    assert result["skill"] == "tail_command"


def test_head():
    result = route_with_rules("test.txt 처음 3줄 보여줘")
    assert result["skill"] == "head_command"


def test_cp_copy():
    result = route_with_rules("test.txt 복사해줘")
    assert result["skill"] == "cp_command"


def test_rm():
    result = route_with_rules("임시파일 삭제해줘")
    # should either be rm or ask clarification
    assert result["action"] in ("use_skill", "ask_clarification")


def test_tar_extract():
    result = route_with_rules("backup.tar.gz 압축 풀어줘")
    assert result["action"] == "use_skill"
    assert result["skill"] == "tar_command"
    assert result["args"].get("operation") == "extract"


def test_sort():
    result = route_with_rules("정렬해줘")
    assert result["action"] in ("use_skill", "ask_clarification")


def test_chmod():
    result = route_with_rules("chmod 755 script.sh")
    assert result["action"] == "use_skill"
    assert result["skill"] == "chmod_command"


def test_finish():
    result = route_with_rules("종료")
    assert result["action"] == "finish"


def test_empty_input():
    result = route_with_rules("")
    assert result["action"] == "ask_clarification"


def test_refuse_dangerous():
    result = route_with_rules("sudo rm -rf")
    assert result["action"] == "refuse"
