from garcon.parser import normalize_path, normalize_args, parse_action


def test_normalize_path():
    assert normalize_path("다운로드") == "~/Downloads"
    assert normalize_path("바탕화면") == "~/Desktop"
    assert normalize_path("현재 폴더") == "."
    assert normalize_path("여기") == "."
    assert normalize_path("/custom/path") == "/custom/path"


def test_normalize_args():
    args = {"source_dir": "다운로드", "path": "여기"}
    result = normalize_args(args)
    assert result["source_dir"] == "~/Downloads"
    assert result["path"] == "."


def test_normalize_args_with_rules():
    args = {
        "source_dir": "다운로드",
        "rules": [{"extensions": ["pdf"], "target_dir": "문서"}],
    }
    result = normalize_args(args)
    assert result["rules"][0]["target_dir"] == "~/Documents"


def test_parse_action_valid_dict():
    raw = {
        "action": "use_skill",
        "skill": "list_files",
        "args": {"path": "."},
        "risk": "low",
    }
    action, err = parse_action(raw)
    assert err is None
    assert action is not None
    assert action.skill == "list_files"


def test_parse_action_valid_json():
    raw = '{"action": "use_skill", "skill": "list_files", "args": {"path": "."}, "risk": "low"}'
    action, err = parse_action(raw)
    assert err is None
    assert action is not None


def test_parse_action_invalid_json():
    action, err = parse_action("not json at all")
    assert err is not None
    assert "JSON 파싱 실패" in err


def test_parse_action_missing_field():
    # Pydantic allows optional str=None, so parse_action succeeds
    # skill=None is caught later by validate_action
    action, err = parse_action({"action": "use_skill"})
    assert err is None
    assert action is not None
    assert action.skill is None


def test_parse_action_normalizes_paths():
    raw = {"action": "use_skill", "skill": "list_files", "args": {"path": "여기"}}
    action, err = parse_action(raw)
    assert err is None
    assert action.args["path"] == "."


def test_parse_action_not_a_dict():
    action, err = parse_action([1, 2, 3])
    assert err is not None
    assert "JSON 객체" in err
