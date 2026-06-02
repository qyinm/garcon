import tempfile
from pathlib import Path

from garcon.skills.read_file import ReadFileSkill


class TestReadFileSkill:
    def test_nonexistent(self):
        skill = ReadFileSkill()
        result = skill.execute({"path": "/nonexistent_xyz_file"})
        assert result.ok is False

    def test_read_text_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp, "test.txt")
            f.write_text("line1\nline2\nline3\n")
            skill = ReadFileSkill()
            result = skill.execute({"path": str(f)})
            assert result.ok is True
            assert result.data["lines"] == ["line1", "line2", "line3"]

    def test_read_with_max_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp, "test.txt")
            f.write_text("\n".join(f"line{i}" for i in range(100)))
            skill = ReadFileSkill()
            result = skill.execute({"path": str(f), "max_lines": 10})
            assert result.ok is True
            assert len(result.data["lines"]) == 10
            assert result.data["truncated"] is True

    def test_read_binary_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp, "test.png")
            f.write_bytes(b"\x89PNG\r\n\x1a\n")
            skill = ReadFileSkill()
            result = skill.execute({"path": str(f)})
            assert result.ok is False
            assert "바이너리" in result.message

    def test_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp, "test.txt")
            f.write_text("hello")
            skill = ReadFileSkill()
            result = skill.preview({"path": str(f)})
            assert result.ok is True
