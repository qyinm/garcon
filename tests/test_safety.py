from pathlib import Path

from garcon.safety import (
    PATH_KEYS,
    is_under_blocked_root,
    iter_paths,
    path_is_blocked,
    validate_action,
)
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


def test_path_is_blocked_nested_system():
    assert path_is_blocked("/etc/passwd") is True
    assert path_is_blocked("/usr/bin/python3") is True
    assert path_is_blocked("/System/Library/CoreServices") is True
    assert path_is_blocked("/private/etc/ssh/sshd_config") is True


def test_path_is_blocked_cwd():
    assert path_is_blocked(".") is False
    assert path_is_blocked("./pyproject.toml") is False


def test_is_under_blocked_root_exact_match():
    assert is_under_blocked_root(Path("/etc")) is True


def test_is_under_blocked_root_nested():
    assert is_under_blocked_root(Path("/etc/passwd")) is True
    assert is_under_blocked_root(Path("/usr/bin/python3")) is True


def test_is_under_blocked_root_safe():
    assert is_under_blocked_root(Path.home()) is False
    assert is_under_blocked_root(Path.cwd()) is False
    assert is_under_blocked_root(Path("~/Downloads").expanduser()) is False


def test_iter_paths_extracts_path_values():
    args = {
        "path": "/some/file",
        "source_dir": "~/Downloads",
        "other": "not_a_path",
        "nested": {"target_dir": "/target/path", "archive": "a.zip"},
        "items": [{"source": "/item/path"}],
    }
    result = list(iter_paths(args))
    assert "/some/file" in result
    assert "~/Downloads" in result
    assert "/target/path" in result
    assert "a.zip" in result
    assert "/item/path" in result
    assert "not_a_path" not in result


def test_iter_paths_handles_empty():
    assert list(iter_paths({})) == []
    assert list(iter_paths([])) == []


def test_iter_paths_list_values():
    args = {"paths": ["/etc/passwd", "/etc/hosts"]}
    result = list(iter_paths(args))
    assert "/etc/passwd" in result
    assert "/etc/hosts" in result


def test_iter_paths_non_path_list_not_yielded():
    args = {"items": ["/etc/passwd", "/etc/hosts"]}
    result = list(iter_paths(args))
    assert result == []


def test_validate_action_empty_skill():
    action = GarconAction(action="use_skill")
    ok, reason = validate_action(action)
    assert ok is False
    assert "skill이 비어 있습니다" in reason


def test_validate_action_high_risk_sets_confirmation():
    action = GarconAction(
        action="use_skill", skill="organize_files", args={"source_dir": "~"}
    )
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


def test_validate_action_read_blocked_system_path():
    action = GarconAction(
        action="use_skill",
        skill="read_file",
        args={"path": "/etc/passwd"},
    )
    ok, reason = validate_action(action)
    assert ok is False
    assert "차단된" in reason


def test_validate_action_read_nested_system_path():
    action = GarconAction(
        action="use_skill",
        skill="read_file",
        args={"path": "/usr/share/doc/README"},
    )
    ok, reason = validate_action(action)
    assert ok is False


def test_validate_action_read_home_allowed():
    action = GarconAction(
        action="use_skill",
        skill="read_file",
        args={"path": "~/Documents/notes.txt"},
    )
    ok, reason = validate_action(action)
    assert ok is True


def test_validate_action_write_outside_home_blocked():
    action = GarconAction(
        action="use_skill",
        skill="organize_files",
        args={"source_dir": "/opt/test"},
    )
    ok, reason = validate_action(action)
    assert ok is False


def test_validate_action_write_blocked_system_path():
    action = GarconAction(
        action="use_skill",
        skill="compress_files",
        args={"paths": ["/etc/passwd"], "output": "out.zip"},
    )
    ok, reason = validate_action(action)
    assert ok is False
    assert "차단된" in reason


def test_validate_action_write_home_allowed():
    action = GarconAction(
        action="use_skill",
        skill="organize_files",
        args={"source_dir": "~/Downloads"},
    )
    ok, reason = validate_action(action)
    assert ok is True


def test_validate_action_search_system_path_blocked():
    action = GarconAction(
        action="use_skill",
        skill="search_text",
        args={"path": "/usr/bin", "query": "test"},
    )
    ok, reason = validate_action(action)
    assert ok is False


def test_validate_action_extract_blocked_path():
    action = GarconAction(
        action="use_skill",
        skill="extract_archive",
        args={"archive": "/etc/hosts.zip", "target_dir": "."},
    )
    ok, reason = validate_action(action)
    assert ok is False


def test_validate_action_non_path_keys_not_checked():
    action = GarconAction(
        action="use_skill",
        skill="list_files",
        args={"query": "/etc/passwd"},
    )
    ok, reason = validate_action(action)
    assert ok is True


def test_path_is_blocked_bin():
    assert path_is_blocked("/bin") is True
    assert path_is_blocked("/sbin/sh") is True


def test_path_is_blocked_var():
    assert path_is_blocked("/var/log/system.log") is True


def test_path_is_blocked_library():
    assert path_is_blocked("/Library/Preferences") is True
