from garcon.safety import path_is_blocked, validate_action
from garcon.schema import GarconAction


def test_path_is_blocked_root():
    assert path_is_blocked("/") is True


def test_path_is_blocked_system():
    assert path_is_blocked("/etc") is True
    assert path_is_blocked("/usr") is True


def test_path_is_blocked_home_is_safe():
    assert path_is_blocked("~") is False


def test_path_is_blocked_downloads_is_safe():
    assert path_is_blocked("~/Downloads") is False


def test_validate_action_empty_skill():
    action = GarconAction(action="use_skill")
    ok, reason = validate_action(action)
    assert ok is False
    assert "skill이 비어 있습니다" in reason


def test_validate_action_high_risk_sets_confirmation():
    action = GarconAction(action="use_skill", skill="organize_files", args={"source_dir": "~"})
    ok, reason = validate_action(action)
    assert ok is True
    assert action.requires_confirmation is True


def test_validate_action_safe():
    action = GarconAction(
        action="use_skill",
        skill="list_files",
        args={"path": "."},
        risk="low",
    )
    ok, reason = validate_action(action)
    assert ok is True
    assert reason is None


def test_validate_action_dangerous_token():
    action = GarconAction(
        action="use_skill",
        skill="list_files",
        args={"command": "rm -rf /"},
    )
    ok, reason = validate_action(action)
    assert ok is False
    assert "위험한 표현" in reason


def test_validate_action_sudo_detected():
    action = GarconAction(
        action="use_skill",
        skill="list_files",
        args={"command": "sudo rm"},
    )
    ok, reason = validate_action(action)
    assert ok is False
