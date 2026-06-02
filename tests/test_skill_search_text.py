import tempfile
from pathlib import Path

from garcon.skills.search_text import (
    MAX_FILE_SIZE,
    SearchTextSkill,
    _is_text_file,
)


def test_is_text_file_null_byte():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp, "binary.bin")
        p.write_bytes(b"hello\x00world")
        assert _is_text_file(p) is False


def test_is_text_file_known_ext():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp, "test.py")
        p.write_text("print('hello')")
        assert _is_text_file(p) is True


def test_is_text_file_unknown_no_null():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp, "readme")
        p.write_bytes(b"hello world\n")
        assert _is_text_file(p) is True


def test_is_text_file_unknown_with_null():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp, "data.bin")
        p.write_bytes(b"PNG\x00\x00\x00\x0dIHDR")
        assert _is_text_file(p) is False


def test_search_skips_large_file():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp, "big.txt")
        p.write_bytes(b"x" * (MAX_FILE_SIZE + 1))
        skill = SearchTextSkill()
        result = skill.execute({"path": tmp, "query": "x"})
        assert result.ok is True
        assert result.data["total"] == 0


class TestSearchTextSkill:
    def test_nonexistent(self):
        skill = SearchTextSkill()
        result = skill.execute({"path": "/nonexistent_xyz", "query": "test"})
        assert result.ok is False

    def test_empty_query(self):
        skill = SearchTextSkill()
        result = skill.execute({"path": ".", "query": ""})
        assert result.ok is False

    def test_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test.txt").write_text("hello world\nfoo bar\n")
            skill = SearchTextSkill()
            result = skill.execute({"path": tmp, "query": "hello"})
            assert result.ok is True
            assert result.data["total"] == 1

    def test_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test.txt").write_text("hello world\n")
            skill = SearchTextSkill()
            result = skill.execute({"path": tmp, "query": "zzznotfound"})
            assert result.ok is True
            assert result.data["total"] == 0

    def test_extension_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.py").write_text("import os\n")
            Path(tmp, "a.txt").write_text("hello\n")
            skill = SearchTextSkill()
            result = skill.execute({
                "path": tmp,
                "query": "import",
                "include_extensions": ["py"],
            })
            assert result.ok is True
            assert result.data["total"] == 1
