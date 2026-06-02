import pytest

from garcon.model_manager import model_path
from garcon.model_router import (
    CLASS_TO_SKILL,
    CLASSIFICATION_PROMPT,
    ModelRouter,
    _build_action,
    _post_process_classification,
)


def test_classification_prompt_format():
    prompt = CLASSIFICATION_PROMPT.format(inp="안녕")
    assert "안녕" in prompt
    assert "Answer (one word):" in prompt
    assert prompt.startswith("Korean intent classification.")


def test_class_to_skill_has_all_classes():
    expected = {
        "list", "read", "search", "organize", "rename",
        "compress", "extract", "refuse", "finish",
        "greeting", "other",
    }
    assert set(CLASS_TO_SKILL.keys()) == expected


class TestPostProcessClassification:
    def test_read_with_list_keyword_becomes_list(self):
        assert _post_process_classification("파일 목록 보여줘", "read") == "list"

    def test_read_without_list_keyword_stays_read(self):
        assert _post_process_classification("파일 읽어줘", "read") == "read"

    def test_other_classifications_unchanged(self):
        assert _post_process_classification("안녕", "greeting") == "greeting"
        assert _post_process_classification("검색해줘", "search") == "search"


class TestBuildAction:
    def test_greeting(self):
        result = _build_action("안녕", "greeting")
        assert result is not None
        assert result["action"] == "show_plan"

    def test_refuse(self):
        result = _build_action("파일 삭제해줘", "refuse")
        assert result is not None
        assert result["action"] == "refuse"

    def test_finish(self):
        result = _build_action("종료", "finish")
        assert result is not None
        assert result["action"] == "finish"

    def test_other(self):
        result = _build_action("도움말", "other")
        assert result is not None
        assert result["action"] == "ask_clarification"

    def test_list_files(self):
        result = _build_action("파일 목록 보여줘", "list")
        assert result is not None
        assert result["action"] == "use_skill"
        assert result["skill"] == "list_files"
        assert "args" in result
        assert result["args"]["path"] == "."

    def test_list_files_with_download_path(self):
        result = _build_action("다운로드 파일 목록", "list")
        assert result is not None
        assert result["args"]["path"] == "~/Downloads"

    def test_read_file(self):
        result = _build_action("test.py 읽어줘", "read")
        assert result is not None
        assert result["skill"] == "read_file"
        assert result["args"]["path"] == "test.py"

    def test_read_file_without_name_extracts_filename(self):
        result = _build_action("파일 읽어줘", "read")
        assert result is not None
        assert result["action"] == "use_skill"
        assert result["skill"] == "read_file"

    def test_search(self):
        result = _build_action("log에서 error 찾아줘", "search")
        assert result is not None
        assert result["skill"] == "search_text"
        assert result["args"]["query"] == "error"
        assert result["args"]["include_extensions"] == ["log"]

    def test_search_without_query_false_positive(self):
        result = _build_action("검색해줘", "search")
        assert result is not None
        assert result["action"] == "use_skill"
        assert result["skill"] == "search_text"

    def test_organize(self):
        result = _build_action("다운로드 폴더 정리해줘", "organize")
        assert result is not None
        assert result["skill"] == "organize_files"
        assert result["args"]["source_dir"] == "~/Downloads"

    def test_rename(self):
        result = _build_action("파일 이름 바꿔줘", "rename")
        assert result is not None
        assert result["skill"] == "rename_files"

    def test_compress(self):
        result = _build_action("파일 압축해줘", "compress")
        assert result is not None
        assert result["skill"] == "compress_files"

    def test_extract(self):
        result = _build_action("압축 풀어줘", "extract")
        assert result is not None
        assert result["skill"] == "extract_archive"

    def test_unknown_class_returns_none(self):
        assert _build_action("test", "unknown") is None


class TestModelRouter:
    def test_not_loaded_by_default(self):
        router = ModelRouter()
        assert router.available is False
        assert router.route("안녕") is None

    def test_load_success(self):
        mp = model_path()
        if not mp:
            pytest.skip("Model not downloaded")
        router = ModelRouter()
        router.load(mp)
        assert router.available is True

    @pytest.mark.xfail(reason="SmolLM2 135M accuracy <50% before fine-tuning")
    def test_route_korean_greeting(self):
        mp = model_path()
        if not mp:
            pytest.skip("Model not downloaded")
        router = ModelRouter()
        router.load(mp)
        result = router.route("안녕")
        assert result is not None and result.get("action") == "show_plan"

    @pytest.mark.xfail(reason="SmolLM2 135M accuracy <50% before fine-tuning")
    def test_route_korean_refuse_delete(self):
        mp = model_path()
        if not mp:
            pytest.skip("Model not downloaded")
        router = ModelRouter()
        router.load(mp)
        result = router.route("파일 삭제해줘")
        assert result is not None and result.get("action") == "refuse"

    @pytest.mark.xfail(reason="SmolLM2 135M accuracy <50% before fine-tuning")
    def test_route_korean_search(self):
        mp = model_path()
        if not mp:
            pytest.skip("Model not downloaded")
        router = ModelRouter()
        router.load(mp)
        result = router.route("log에서 error 찾아줘")
        assert result is not None and result.get("skill") == "search_text"

    @pytest.mark.xfail(reason="SmolLM2 135M accuracy <50% before fine-tuning")
    def test_route_korean_organize(self):
        mp = model_path()
        if not mp:
            pytest.skip("Model not downloaded")
        router = ModelRouter()
        router.load(mp)
        result = router.route("다운로드 폴더 정리해줘")
        assert result is not None and result.get("skill") == "organize_files"

    @pytest.mark.xfail(reason="SmolLM2 135M accuracy <50% before fine-tuning")
    def test_route_korean_list_files(self):
        mp = model_path()
        if not mp:
            pytest.skip("Model not downloaded")
        router = ModelRouter()
        router.load(mp)
        result = router.route("파일 목록 보여줘")
        assert result is not None and result.get("skill") == "list_files"

    @pytest.mark.xfail(reason="SmolLM2 135M accuracy <50% before fine-tuning")
    def test_route_korean_extract(self):
        mp = model_path()
        if not mp:
            pytest.skip("Model not downloaded")
        router = ModelRouter()
        router.load(mp)
        result = router.route("압축 풀어줘")
        assert result is not None and result.get("skill") == "extract_archive"

    @pytest.mark.xfail(reason="SmolLM2 135M accuracy <50% before fine-tuning")
    def test_route_korean_compress(self):
        mp = model_path()
        if not mp:
            pytest.skip("Model not downloaded")
        router = ModelRouter()
        router.load(mp)
        result = router.route("파일 압축해줘")
        assert result is not None and result.get("skill") == "compress_files"
