import tempfile
from pathlib import Path

from garcon.skills.search_text import SearchTextSkill


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
