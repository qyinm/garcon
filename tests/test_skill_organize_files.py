import tempfile
from pathlib import Path

from garcon.skills.organize_files import OrganizeFilesSkill


class TestOrganizeFilesSkill:
    def test_nonexistent_dir(self):
        skill = OrganizeFilesSkill()
        result = skill.execute({
            "source_dir": "/nonexistent_xyz_org",
            "rules": [],
        })
        assert result.ok is False

    def test_organize_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "doc.pdf").write_text("pdf")
            Path(tmp, "pic.png").write_text("png")
            Path(tmp, "readme.txt").write_text("text")
            skill = OrganizeFilesSkill()
            result = skill.execute({
                "source_dir": tmp,
                "rules": [
                    {
                        "extensions": ["pdf"],
                        "target_dir": str(Path(tmp, "PDFs")),
                    },
                    {
                        "extensions": ["png"],
                        "target_dir": str(Path(tmp, "Images")),
                    },
                ],
            })
            assert result.ok is True
            assert len(result.data["moved"]) == 2
            assert Path(tmp, "PDFs", "doc.pdf").exists()
            assert Path(tmp, "Images", "pic.png").exists()
            assert Path(tmp, "readme.txt").exists()

    def test_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "doc.pdf").write_text("pdf")
            skill = OrganizeFilesSkill()
            result = skill.preview({
                "source_dir": tmp,
                "rules": [
                    {
                        "extensions": ["pdf"],
                        "target_dir": str(Path(tmp, "PDFs")),
                    },
                ],
            })
            assert result.ok is True
            assert len(result.data["plan"]) == 1

    def test_undo_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "doc.pdf").write_text("pdf")
            skill = OrganizeFilesSkill()
            result = skill.execute({
                "source_dir": tmp,
                "rules": [
                    {
                        "extensions": ["pdf"],
                        "target_dir": str(Path(tmp, "PDFs")),
                    },
                ],
            })
            assert result.ok is True
            assert result.undo is not None
            assert result.undo["type"] == "move_files_back"
            assert len(result.undo["items"]) == 1
            assert result.undo["items"][0]["to"] == str(Path(tmp, "doc.pdf").resolve())
