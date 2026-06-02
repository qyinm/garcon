import tempfile
from pathlib import Path

from garcon.skills.find_large_files import FindLargeFilesSkill


class TestFindLargeFilesSkill:
    def test_nonexistent_dir(self):
        skill = FindLargeFilesSkill()
        result = skill.execute({
            "path": "/nonexistent_xyz_large",
            "limit": 10, "min_size_mb": 1,
        })
        assert result.ok is False

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = FindLargeFilesSkill()
            result = skill.execute({
                "path": tmp, "limit": 10, "min_size_mb": 1,
            })
            assert result.ok is True
            assert result.data["files"] == []

    def test_find_large_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "small.txt").write_text("x" * 1024)
            large = Path(tmp, "large.dat")
            large.write_text("x" * (2 * 1024 * 1024))
            skill = FindLargeFilesSkill()
            result = skill.execute({
                "path": tmp, "limit": 10, "min_size_mb": 1,
            })
            assert result.ok is True
            names = [f["path"] for f in result.data["files"]]
            assert any("large.dat" in n for n in names)
            assert all("small.txt" not in n for n in names)

    def test_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = FindLargeFilesSkill()
            result = skill.preview({
                "path": tmp, "limit": 10, "min_size_mb": 1,
            })
            assert result.ok is True
