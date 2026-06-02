import tempfile
from pathlib import Path

from garcon.skills.list_files import ListFilesSkill
from garcon.skills.read_file import ReadFileSkill
from garcon.skills.search_text import SearchTextSkill


class TestListFiles:
    def test_list_nonexistent(self):
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
            assert "파일 목록" in result.message or "표시" in result.message


class TestReadFile:
    def test_read_nonexistent(self):
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


class TestSearchText:
    def test_search_nonexistent(self):
        skill = SearchTextSkill()
        result = skill.execute({"path": "/nonexistent_xyz", "query": "test"})
        assert result.ok is False

    def test_search_empty_query(self):
        skill = SearchTextSkill()
        result = skill.execute({"path": ".", "query": ""})
        assert result.ok is False

    def test_search_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test.txt").write_text("hello world\nfoo bar\n")
            skill = SearchTextSkill()
            result = skill.execute({"path": tmp, "query": "hello"})
            assert result.ok is True
            assert result.data["total"] == 1

    def test_search_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test.txt").write_text("hello world\n")
            skill = SearchTextSkill()
            result = skill.execute({"path": tmp, "query": "zzznotfound"})
            assert result.ok is True
            assert result.data["total"] == 0

    def test_search_with_extension_filter(self):
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
