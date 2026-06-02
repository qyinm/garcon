import tempfile
import zipfile
from pathlib import Path

from garcon.skills.extract_archive import ExtractArchiveSkill


class TestExtractArchiveSkill:
    def test_nonexistent_archive(self):
        skill = ExtractArchiveSkill()
        result = skill.execute({
            "archive": "/nonexistent_xyz_archive.zip",
            "target_dir": ".",
        })
        assert result.ok is False

    def test_extract_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp, "test.zip")
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("file1.txt", "content1")
                zf.writestr("sub/file2.txt", "content2")
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is True
            assert Path(target, "file1.txt").exists()
            assert Path(target, "sub", "file2.txt").exists()

    def test_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp, "test.zip")
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("file.txt", "content")
            skill = ExtractArchiveSkill()
            result = skill.preview({
                "archive": str(archive),
                "target_dir": str(Path(tmp, "out")),
            })
            assert result.ok is True

    def test_unsupported_format(self):
        skill = ExtractArchiveSkill()
        result = skill.execute({
            "archive": "/tmp/test.xyz",
            "target_dir": ".",
        })
        assert result.ok is False

    def test_undo_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp, "test.zip")
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("file.txt", "content")
            target = Path(tmp, "out")
            skill = ExtractArchiveSkill()
            result = skill.execute({
                "archive": str(archive),
                "target_dir": str(target),
            })
            assert result.ok is True
            assert result.undo is not None
            assert result.undo["type"] == "delete_files"
            assert any("file.txt" in item["path"] for item in result.undo["items"])
