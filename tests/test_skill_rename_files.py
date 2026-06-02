import tempfile
from pathlib import Path

from garcon.skills.rename_files import RenameFilesSkill


class TestRenameFilesSkill:
    def test_nonexistent_dir(self):
        skill = RenameFilesSkill()
        result = skill.execute({
            "source_dir": "/nonexistent_xyz_rename",
            "pattern": "_old", "replacement": "_new",
        })
        assert result.ok is False

    def test_rename_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "report_old.txt").write_text("a")
            Path(tmp, "keep.txt").write_text("b")
            skill = RenameFilesSkill()
            result = skill.execute({
                "source_dir": tmp,
                "pattern": "_old", "replacement": "_new",
            })
            assert result.ok is True
            assert len(result.data["renamed"]) == 1
            assert Path(tmp, "report_new.txt").exists()
            assert not Path(tmp, "report_old.txt").exists()

    def test_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a_old.txt").write_text("a")
            skill = RenameFilesSkill()
            result = skill.preview({
                "source_dir": tmp,
                "pattern": "_old", "replacement": "_new",
            })
            assert result.ok is True
            assert len(result.data["plan"]) == 1

    def test_empty_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = RenameFilesSkill()
            result = skill.preview({
                "source_dir": tmp,
                "pattern": "", "replacement": "_new",
            })
            assert result.ok is False

    def test_undo_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a_old.txt").write_text("a")
            skill = RenameFilesSkill()
            result = skill.execute({
                "source_dir": tmp,
                "pattern": "_old", "replacement": "_new",
            })
            assert result.ok is True
            assert result.undo is not None
            assert result.undo["type"] == "move_files_back"
            expected_from = str(Path(tmp, "a_new.txt").resolve())
            expected_to = str(Path(tmp, "a_old.txt").resolve())
            assert result.undo["items"][0]["from"] == expected_from
            assert result.undo["items"][0]["to"] == expected_to
