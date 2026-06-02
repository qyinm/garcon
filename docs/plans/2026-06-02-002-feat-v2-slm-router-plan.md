---
title: "feat: v2 SLM router — SmolLM2 replaces rule-based router"
status: active
created: 2026-06-02
---

# feat: v2 SLM router

Replace the rule-based Korean NL router with a 0.1B SLM (SmolLM2-135M-Instruct) running locally via llama.cpp. The rule-based router becomes a fallback when the model is unavailable.

## Problem

The current `route_with_rules()` in `garcon/router.py` uses keyword matching (e.g., `"정리" in text`) to dispatch skills. This approach:
- Cannot handle variations in user phrasing
- Requires manual pattern additions for every new skill
- Fails on ambiguous or compound requests
- Does not scale past ~10 skills

## Approach

Run SmolLM2-135M-Instruct GGUF (Q4_K_M, ~105 MB) via `llama-cpp-python` with Metal GPU acceleration. The model receives a system prompt listing all available skills with their JSON schemas, plus the user's Korean NL request, and outputs a structured JSON action. If the model is absent or inference fails, fall back to the existing `route_with_rules()`.

## Key Technical Decisions

- **Runtime**: `llama-cpp-python` (not raw llama.cpp subprocess, not transformers) — best Python DX, built-in Metal support, no torch dependency
- **Model format**: Q4_K_M GGUF (~105 MB) from `QuantFactory/SmolLM2-135M-Instruct-GGUF`
- **Model caching**: `~/.cache/garcon/` (project-specific, not HF global cache — simpler for users who don't use HF)
- **Fallback**: rule-based router is always the fallback; model is an enhancement, not a hard dependency
- **Output format**: Model outputs raw JSON (no markdown fences) — validated against GarconAction schema. If JSON parse fails, fallback to rule router.

---

## Scope Boundaries

### In scope
- Model download/management (CLI commands)
- Model inference wrapper (prompt building, JSON parsing, retry logic)
- Integration into existing CLI (optional, off by default, enabled via `--use-model` or `GARCON_USE_MODEL=1`)
- Fallback to rule-based router on failure

### Deferred for later
- Online model download during `garcon chat` first run (user must run `garcon model download` manually)
- GGUF auto-download on first use (requires `huggingface-hub` at runtime)
- Multi-model support (e.g., user chooses different GGUF path)
- Streaming inference or partial JSON parsing
- Benchmarking against rule router accuracy

### Outside scope
- Training/fine-tuning the model
- GPU fallback to CPU-only (llama.cpp handles this automatically)
- Support for non-GGUF model formats
- Remote model server (ollama, OpenAI API)

---

## Implementation Units

### U1. Model download and management

- **Goal**: Download SmolLM2-135M-Instruct GGUF from HuggingFace and cache it at `~/.cache/garcon/`. Provide CLI commands to manage the model.

- **Files**:
  - `garcon/model_manager.py` — new
  - `garcon/cli.py` — modify (add `model` command group)
  - `tests/test_model_manager.py` — new

- **Approach**:
  - `model_manager.py` has `ensure_model()` which checks for `~/.cache/garcon/SmolLM2-135M-Instruct.Q4_K_M.gguf`, downloads via `huggingface-cli` or `requests` if absent
  - `model_path()` returns the path or None
  - `download_model()` streams the GGUF file with progress bar
  - `remove_model()` deletes the cached file
  - CLI: `garcon model download`, `garcon model status`, `garcon model remove`

- **Test scenarios**:
  - `test_model_not_found_returns_none`: when no GGUF in cache, `model_path()` returns None
  - `test_download_model_creates_file`: mock HTTP download, verify file created at correct path
  - `test_remove_model_deletes_file`: download then remove, verify absent
  - `test_model_status_reports_correctly`: with and without model file, status output differs

- **Verification**: `garcon model status` shows model path and "사용 가능" or "다운로드 필요"

### U2. Model inference wrapper

- **Goal**: Load the GGUF model via `llama-cpp-python`, build the ChatML prompt with system prompt listing all skills, call inference, parse and validate the JSON output.

- **Files**:
  - `garcon/model_router.py` — new
  - `tests/test_model_router.py` — new

- **Approach**:
  - `ModelRouter` class with `load()` (lazy) and `route(user_input: str) -> dict`
  - `load()` instantiates `llama_cpp.Llama(model_path, n_gpu_layers=-1, verbose=False)`. On failure, sets `_available = False`
  - System prompt enumerates all skills from `garcon/executor.SKILLS` keys, with their JSON argument schemas and the output JSON schema
  - Prompt format:
    ```
    <|im_start|>system
    {system_prompt}<|im_end|>
    <|im_start|>user
    {user_input}<|im_end|>
    <|im_start|>assistant
    ```
  - Inference: `temperature=0.1, max_tokens=256, stop=["<|im_end|>"]`
  - Response parsing: strip whitespace, `json.loads()`, validate against GarconAction-like dict shape. On failure, try extracting JSON from between `{` and `}`. If all fail, `_available = False` and return None (caller falls back)
  - Temperature 0.1 for deterministic structured output
  - Include 2-shot examples in system prompt (list_files + organize_files) to guide output format

- **Patterns to follow**: `garcon/schema.py` for the GarconAction model fields

- **Test scenarios**:
  - `test_load_model_success`: mock `llama_cpp.Llama`, verify `_available` is True
  - `test_load_model_failure`: mock import failure or constructor error, verify graceful `_available = False`
  - `test_route_valid_json`: mock `create_chat_completion` to return valid JSON, verify parsed dict matches expected shape
  - `test_route_invalid_json`: mock returns garbage text, verify returns None (trigger fallback)
  - `test_route_empty_input`: empty string input, verify graceful handling
  - `test_route_with_korean`: "다운로드 폴더 정리해줘" → mock returns organize_files JSON, verify skill and args match

- **Verification**: `ModelRouter().route("파일 목록 보여줘")` returns dict with `action: "use_skill", skill: "list_files"`

### U3. CLI integration

- **Goal**: Wire the model router into the existing CLI execution flow, controlled by environment variable or flag. Rule-based router always runs as fallback.

- **Files**:
  - `garcon/cli.py` — modify (add `--use-model` flag, model initialization)
  - `garcon/executor.py` — modify (accept optional router function)
  - `tests/test_cli.py` or `tests/test_router.py` — extend

- **Approach**:
  - Add `--use-model` flag to `garcon chat` and `garcon run`
  - Environment variable `GARCON_USE_MODEL=1` also enables it
  - New `_get_router()` function: if model enabled and available, return `model_router.route`; else `route_with_rules`
  - `handle()` in cli.py uses the chosen router function instead of calling `route_with_rules()` directly
  - Lazy model loading: only download/load on first chat turn or run, not at CLI startup
  - Import `llama_cpp` is optional — if not installed, `GARCON_USE_MODEL=1` is silently ignored (or prints a warning)

- **Patterns to follow**: existing `handle()` function in `garcon/cli.py` — same flow, different router source

- **Test scenarios**:
  - `test_router_uses_model_when_enabled`: `GARCON_USE_MODEL=1`, mock successful model_router, verify model_router.route called
  - `test_router_falls_back_on_model_failure`: `GARCON_USE_MODEL=1`, mock model_router returns None, verify rule router called
  - `test_router_uses_rules_by_default`: no env var, verify rule router called, model never loaded
  - `test_model_not_imported_gracefully`: mock `llama_cpp` import error, verify no crash, rule router used

- **Verification**: `GARCON_USE_MODEL=1 garcon run "안녕"` works end-to-end with model

### U4. Dependency management

- **Goal**: Add `llama-cpp-python` as an optional dependency. Graceful degradation when not installed.

- **Files**:
  - `pyproject.toml` — modify

- **Approach**:
  - Add optional dependency group: `[project.optional-dependencies] model = ["llama-cpp-python>=0.3"]`
  - Documentation note: install with `uv sync --group model` or `pip install "garcon[model]"` (once published)
  - All model-related imports use try/except ImportError with `_MODEL_AVAILABLE` flag

- **Test scenarios**:
  - `test_import_without_llama_cpp`: mock module absent, verify model_router import doesn't crash, `_MODEL_AVAILABLE` is False

- **Verification**: `uv sync` without group works; `uv sync --group model` installs llama-cpp-python

---

## Dependencies

- `llama-cpp-python>=0.3` (optional, `model` dependency group)
- `huggingface-hub` or `requests` for model download (stdlib `urllib` may suffice for direct download from HF)

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| llama-cpp-python fails to install (no Rust, missing cmake) | Medium | Document install steps; recommend `CMAKE_ARGS="-DGGML_METAL=on" pip install`; fallback to rule router always works |
| Model outputs invalid JSON | High (small models struggle with structured output) | Temperature 0.1, 2-shot examples, JSON extraction fallback, final fallback to rule router |
| Model download is slow (~105 MB) | Low | Show progress bar; one-time cost; small file |
| Model hallucinates skill names | Medium | Validate output skill against SKILLS keys; reject unknown skills; fallback to rule router |
| Korean NL quality is poor with 135M | Medium | Test before merging; if quality is insufficient, document limitation and consider larger model path |
