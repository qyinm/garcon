import tempfile
import zipfile
from pathlib import Path

from garcon.skills.compress_files import CompressFilesSkill


class TestCompressFilesSkill:
    def test_no_paths(self):
        skill = CompressFilesSkill()
        result = skill.execute({"paths": [], "output": ""})
        assert result.ok is False

    def test_compress_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.txt").write_text("hello")
            Path(tmp, "b.txt").write_text("world")
            output = str(Path(tmp, "archive.zip"))
            skill = CompressFilesSkill()
            result = skill.execute({
                "paths": [str(Path(tmp, "a.txt")), str(Path(tmp, "b.txt"))],
                "output": output,
            })
            assert result.ok is True
            assert Path(output).exists()
            with zipfile.ZipFile(output) as zf:
                names = zf.namelist()
                assert "a.txt" in names
                assert "b.txt" in names

    def test_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.txt").write_text("hello")
            skill = CompressFilesSkill()
            result = skill.preview({
                "paths": [str(Path(tmp, "a.txt"))],
                "output": str(Path(tmp, "out.zip")),
            })
            assert result.ok is True

    def test_missing_file(self):
        skill = CompressFilesSkill()
        result = skill.execute({
            "paths": ["/nonexistent_xyz_file_for_zip"],
            "output": "/tmp/test_compress.zip",
        })
        assert result.ok is False

    def test_undo_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.txt").write_text("hello")
            output = Path(tmp, "archive.zip")
            skill = CompressFilesSkill()
            result = skill.execute({
                "paths": [str(Path(tmp, "a.txt"))],
                "output": str(output),
            })
            assert result.ok is True
            assert result.undo is not None
            assert result.undo["type"] == "delete_archive"
            assert result.undo["items"][0]["path"] == str(output.resolve())

    def test_auto_append_zip_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.txt").write_text("hello")
            output = Path(tmp, "archive")
            skill = CompressFilesSkill()
            result = skill.execute({
                "paths": [str(Path(tmp, "a.txt"))],
                "output": str(output),
            })
            assert result.ok is True
            assert Path(tmp, "archive.zip").exists()
            assert not output.exists()

    def test_preserve_explicit_zip_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.txt").write_text("hello")
            output = Path(tmp, "my.zip")
            skill = CompressFilesSkill()
            result = skill.execute({
                "paths": [str(Path(tmp, "a.txt"))],
                "output": str(output),
            })
            assert result.ok is True
            assert Path(tmp, "my.zip").exists()
