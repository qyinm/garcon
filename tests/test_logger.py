import json
from pathlib import Path

import pytest

from garcon.logger import (
    SESSION_FILE,
    clear,
    get_recent,
    log_entry,
    _read_all,
)


@pytest.fixture(autouse=True)
def _clean_log():
    clear()
    yield
    clear()


def test_log_entry_writes_jsonl():
    log_entry(user_input="파일 목록", router="slm", classification="list", action="use_skill", skill="list_files", result_type="ok")
    entries = _read_all()
    assert len(entries) == 1
    assert entries[0]["input"] == "파일 목록"
    assert entries[0]["router"] == "slm"
    assert entries[0]["classification"] == "list"
    assert entries[0]["action"] == "use_skill"
    assert entries[0]["skill"] == "list_files"
    assert entries[0]["result"] == "ok"
    assert "ts" in entries[0]


def test_log_entry_minimal():
    log_entry(user_input="안녕", router="rule")
    entries = _read_all()
    assert len(entries) == 1
    assert entries[0]["input"] == "안녕"
    assert entries[0]["router"] == "rule"
    assert "classification" not in entries[0]


def test_log_entry_appends():
    log_entry(user_input="a", router="rule")
    log_entry(user_input="b", router="slm")
    entries = _read_all()
    assert len(entries) == 2
    assert entries[0]["input"] == "a"
    assert entries[1]["input"] == "b"


def test_get_recent():
    for i in range(5):
        log_entry(user_input=str(i), router="rule")
    recent = get_recent(3)
    assert len(recent) == 3
    assert [e["input"] for e in recent] == ["2", "3", "4"]


def test_get_recent_empty():
    assert get_recent() == []


def test_max_entries():
    for i in range(1002):
        log_entry(user_input=str(i), router="rule")
    entries = _read_all()
    assert len(entries) == 1000
    assert entries[0]["input"] == "2"
    assert entries[-1]["input"] == "1001"


def test_clear():
    log_entry(user_input="x", router="rule")
    assert SESSION_FILE.exists()
    clear()
    assert not SESSION_FILE.exists()


def test_log_entry_risk_and_args():
    log_entry(user_input="정리", router="slm", classification="organize", action="use_skill", skill="organize_files", args={"target_dir": "~"}, risk="medium", result_type="needs_confirmation", message="5개 파일 정리 예정")
    entries = _read_all()
    assert entries[0]["risk"] == "medium"
    assert entries[0]["args"] == {"target_dir": "~"}
    assert entries[0]["message"] == "5개 파일 정리 예정"


def test_log_entry_invalid_json_handled():
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text("not json\n", encoding="utf-8")
    assert _read_all() == []
    log_entry(user_input="new", router="rule")
    entries = _read_all()
    assert len(entries) == 1
    assert entries[0]["input"] == "new"


def test_results_column_names():
    log_entry(user_input="파일", router="slm", classification="list", action="use_skill", skill="list_files", result_type="ok")
    entries = _read_all()
    expected = {"ts", "input", "router", "classification", "action", "skill", "result"}
    assert set(entries[0].keys()) == expected
