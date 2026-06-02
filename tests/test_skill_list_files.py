import tempfile
from pathlib import Path

from garcon.skills.list_files import ListFilesSkill


class TestListFilesSkill:
    def test_nonexistent(self):
        skill = ListFilesSkill()
        result = skill.execute({"path": "/nonexistent_path_xyz"})
        assert result.ok is False

    def test_list_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = ListFilesSkill()
            result = skill.execute({"path": tmp})
            assert result.ok is True
            assert "entries" in result.data

    def test_list_with_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.txt").write_text("hello")
            Path(tmp, "b.py").write_text("print(1)")
            skill = ListFilesSkill()
            result = skill.execute({"path": tmp})
            assert result.ok is True
            names = {e["name"] for e in result.data["entries"]}
            assert "a.txt" in names
            assert "b.py" in names

    def test_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = ListFilesSkill()
            result = skill.preview({"path": tmp})
            assert result.ok is True
