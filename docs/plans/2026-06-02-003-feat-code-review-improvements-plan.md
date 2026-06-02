---
title: "feat: Address code review feedback — path safety, archive hardening, search, model, docs, CI"
status: active
created: 2026-06-02
---

# feat: Code review improvements

Execute all items from the comprehensive code review evaluation across three priority tiers. Each implementation unit lands as an independent commit.

## Problem

A structured code review of garcon identified gaps across four dimensions:

- **Safety maturity (5/10)**: `path_is_blocked()` only checks root path exact match, `/etc/passwd` and system paths are accessible. Extract archive uses `extractall()` without path traversal or symlink protection. Undo records overwritten files it should not restore.
- **Model integration (3.5/10)**: Model download has no checksum verification or partial-download cleanup.
- **Product readiness (5.5/10)**: No README, no CI, empty skill args return `use_skill` instead of `ask_clarification`, search text has no binary-file guardrails, compress format is ambiguous.
- **Code structure**: `model_router.py` / `router.py` at same package level with overlapping roles; no subpackage organization.

## Approach

Seven sequential implementation units, each independently committable:

1. **Path safety**: recursive blocked-root check, per-operation path policy, args path traversal in `validate_action()`
2. **Archive hardening**: path traversal prevention, symlink/hardlink rejection, overwrite prevention, accurate undo
3. **Empty args → clarification**: router returns `ask_clarification` when required args are missing
4. **Search + Model quality**: null-byte binary detection, size/scanned-file limits, sha256 checksum, partial-download cleanup
5. **Compress format clarification**: explicitly document zip-only and/or add format param
6. **README + docs**: README.md, SAFETY.md, MODEL.md, SKILLS.md
7. **CI pipeline**: GitHub Actions pytest workflow

---

## Key Technical Decisions

- **Path safety policy**: All skills get a `allowed_zone` classification. Read/list/search operate within home + cwd. Write/move/rename/extract/compress are confined to cwd by default. System paths (`/etc`, `/usr`, `/bin`, `/System`, `/private`, `/var`, `/Library`) are always blocked.
- **Archive hardening strategy**: `safe_join()` with `Path.resolve()` prevents traversal. Symlink/hardlink members are rejected. Pre-extraction scan compares each member path against existing files — existing files are skipped, not overwritten, and excluded from undo.
- **Search text binary detection**: `b"\x00"` in first 4096 bytes → binary. `MAX_FILE_SIZE = 10MB`. `MAX_SCANNED_FILES = 5000`.
- **Model checksum**: sha256 embedded in a `MODEL_MANIFEST` dict. Downloaded file is verified post-extraction; mismatch deletes `.part` and returns error. `download_model()` now cleans up partial downloads on failure.
- **Compress format**: v0 is zip-only. Router and skill consistently use zip. Docs state this clearly. Future tar support goes into a new unit.
- **No subpackage restructure in this round**: router naming and `router/` `model/` subpackages are deferred (code review 3순위) — current flat structure works and restructuring before the codebase settles is premature.

---

## Scope Boundaries

### In scope
- `safety.py` recursive blocked root check with `is_relative_to()`, per-operation path policy, `PATH_KEYS` + `iter_paths()` in `validate_action()`
- `extract_archive.py` path traversal prevention, symlink rejection, overwrite prevention, accurate undo
- `router.py` clarification return for empty compress/extract/rename args
- `search_text.py` null-byte detection, `MAX_FILE_SIZE`, `MAX_SCANNED_FILES`
- `model_manager.py` sha256 checksum in manifest, partial download cleanup
- `README.md` + `docs/SAFETY.md`, `docs/MODEL.md`, `docs/SKILLS.md`
- `.github/workflows/ci.yml`

### Deferred for follow-up work
- Subpackage restructure (`garcon/router/`, `garcon/model/`) — deferred until codebase stabilizes
- `ModelRouter` → `IntentClassifierRouter` rename — bundled with restructure
- tar format support in `compress_files` — new feature, not bug fix
- `--router` CLI flag (model/rule/auto) — nice-to-have after model is fine-tuned

### Outside scope
- Fine-tuning SmolLM2 (separate track)
- Performance benchmarking
- Remote model server support

---

## Implementation Units

### U1. Harden path safety

- **Goal**: Prevent garcon from reading, writing, or searching system paths. Replace root-path-only check with recursive blocked-root matching. Add per-operation path policy in `validate_action()`.

- **Dependencies**: None

- **Files**:
  - `garcon/safety.py` — modify
  - `garcon/cli.py` — modify (wire safety into relevant spots)
  - `tests/test_safety.py` — extend

- **Approach**:
  - `is_under_blocked_root(path: Path) -> bool`: resolves path, checks `is_relative_to()` against each `BLOCKED_ROOTS` entry. Catches `/etc/passwd`, `/usr/bin/foo`, `/System/Library/...` etc.
  - `PATH_KEYS = {"path", "source_dir", "target_dir", "archive", "output", "source"}`
  - `iter_paths(value)` recursively walks dict/list and yields string values whose parent key is in `PATH_KEYS`
  - `validate_action()` classifies skill into `allowed_zone`:
    - `"read"`: `list_files`, `read_file`, `search_text`, `find_large_files` — home + cwd allowed, blocked roots denied
    - `"write"`: `organize_files`, `rename_files`, `compress_files`, `extract_archive` — only cwd allowed, blocked roots denied
  - `path_is_blocked()` updated to use `is_under_blocked_root()`
  - `validate_action()` iterates over `iter_paths(action.args)` and calls `path_is_blocked()` on each

- **Patterns to follow**: Existing `BLOCKED_ROOTS` list and `path_is_blocked()` function signature

- **Test scenarios**:
  - `test_is_under_blocked_root_exact_match`: `/etc/passwd` under `/etc` → True
  - `test_is_under_blocked_root_nested`: `/usr/bin/python3` under `/usr` → True
  - `test_is_under_blocked_root_safe_path`: `/Users/user/file.txt` not under any blocked root → False
  - `test_is_under_blocked_root_cwd`: `Path(".").resolve()` not blocked → False
  - `test_iter_paths_extracts_path_values`: dict with nested keys, verify all path values extracted
  - `test_validate_action_read_blocked_path`: `read_file` with `/etc/passwd` → blocked
  - `test_validate_action_write_outside_cwd`: `organize_files` with `source_dir` outside cwd → blocked
  - `test_validate_action_read_home_dir_allowed`: `read_file` with `~/file.txt` → allowed
  - `test_path_is_blocked_returns_true_for_root`: `/` alone → True (existing behavior preserved)

- **Verification**: `pytest tests/test_safety.py` passes; manual `garcon run "/etc/passwd 읽어줘"` shows 차단 메시지

---

### U2. Harden archive extraction

- **Goal**: Prevent path traversal, symlink/hardlink extraction, and accidental overwrite of existing files in `extract_archive`. Produce accurate undo data (only newly-created files).

- **Dependencies**: U1 (path safety for archive path args)

- **Files**:
  - `garcon/skills/extract_archive.py` — modify
  - `tests/test_skill_extract_archive.py` — extend

- **Approach**:
  - `safe_join(base: Path, member_name: str) -> Path`: resolves `base / member_name`, verifies result is under `base.resolve()`. Raises `ValueError` if traversal detected.
  - **ZIP**: iterate `zf.infolist()`, call `safe_join()` on each `info.filename`. Before extracting, check if destination exists — if so, skip and exclude from undo.
  - **TAR**: same member scan. Additionally reject `member.issym()` and `member.islnk()` with `ValueError`.
  - Extract each file individually (not `extractall()`).
  - Undo `"type": "delete_files"` only includes paths that did not exist before extraction.

- **Patterns to follow**: Existing `MAX_EXTRACT_SIZE` constant, `SkillResult` undo format

- **Test scenarios**:
  - `test_safe_join_normal`: `safe_join("/tmp/out", "file.txt")` → `/tmp/out/file.txt`
  - `test_safe_join_traversal`: `safe_join("/tmp/out", "../../etc/passwd")` → raises `ValueError`
  - `test_safe_join_absolute_member`: `safe_join("/tmp/out", "/etc/passwd")` → raises `ValueError`
  - `test_extract_zip_path_traversal`: create zip with traversal member → extraction fails with message
  - `test_extract_tar_symlink`: create tar with symlink member → extraction fails
  - `test_extract_zip_existing_file_not_overwritten`: target file exists → skipped, undo does not include it
  - `test_extract_zip_undo_only_new_files`: extract to dir with 1 existing + 1 new file → undo only lists the new file
  - `test_extract_zip_normal_extract_still_works`: valid zip extracts successfully

- **Verification**: `pytest tests/test_skill_extract_archive.py` passes; manual extract of traversal zip shows "안전하지 않은 경로" error

---

### U3. Return ask_clarification when required args are empty

- **Goal**: Instead of returning `use_skill` with empty args (which either errors or does nothing), return `ask_clarification` that tells the user what information is missing.

- **Dependencies**: None

- **Files**:
  - `garcon/router.py` — modify
  - `tests/test_router.py` — extend

- **Approach**:
  - In `route_with_rules()`, before returning compress/extract/rename `use_skill`, check whether required args are populated:
    - `compress_files`: if `paths` is empty, return `ask_clarification` with "어떤 파일을 압축할까요? 파일 이름을 알려주세요."
    - `extract_archive`: if `archive` is empty, return `ask_clarification` with "어떤 파일의 압축을 풀까요? 압축 파일 이름을 알려주세요."
    - `rename_files`: if `pattern` is empty, return `ask_clarification` with "어떤 패턴으로 변경할까요? (예: '.txt → .md')"
  - These clarifications carry `action: "ask_clarification"` which executor already handles (shows message in cyan).

- **Patterns to follow**: Existing `ask_clarification` returns in `router.py` (e.g., read without filename)

- **Test scenarios**:
  - `test_compress_empty_paths_returns_clarification`: input has "압축해" but no file names → `action == "ask_clarification"`
  - `test_extract_empty_archive_returns_clarification`: input has "압축 풀어" but no archive → `action == "ask_clarification"`
  - `test_rename_empty_pattern_returns_clarification`: input has "이름 변경" but no pattern → `action == "ask_clarification"`
  - `test_compress_with_paths_still_works`: input has "압축해 test.txt" → `action == "use_skill"` with paths filled
  - `test_extract_with_archive_still_works`: input has "압축 풀어 archive.zip" → `action == "use_skill"` with archive filled

- **Verification**: `pytest tests/test_router.py` passes; manual `garcon run "압축해"` shows clarification message instead of plan

---

### U4. Improve search text quality and model manager reliability

- **Goal**: Prevent search from scanning binary files or huge files. Add integrity verification for model downloads.

- **Dependencies**: U1 (path safety for search path)

- **Files**:
  - `garcon/skills/search_text.py` — modify
  - `garcon/model_manager.py` — modify
  - `garcon/cli.py` — modify (model status shows checksum)
  - `tests/test_skill_search_text.py` — extend
  - `tests/test_model_manager.py` — extend

- **Approach**:
  - **Search**:
    - `MAX_FILE_SIZE = 10 * 1024 * 1024` (10 MB)
    - `MAX_SCANNED_FILES = 5000` (stop after scanning this many files)
    - `_is_text_file()`: add `b"\x00"` null byte check in first 4096 bytes → return False
    - `execute()`: skip files larger than `MAX_FILE_SIZE` before reading
    - `execute()`: increment counter, stop scanning after `MAX_SCANNED_FILES`
  - **Model manager**:
    - `MODEL_MANIFEST = {"id": "smollm2-135m-instruct-q4-k-m", "repo": "QuantFactory/SmolLM2-135M-Instruct-GGUF", "filename": "SmolLM2-135M-Instruct.Q4_K_M.gguf", "sha256": "<hash>", "size_bytes": 105000000, "backend": "llama.cpp"}`
    - `_verify_checksum(path) -> bool`: reads file, computes sha256, compares against manifest
    - `download_model()`: after `shutil.move()`, run checksum. On mismatch, delete file and raise. `.part` file also cleaned up on any exception.
    - `model_size()` returns actual file size; `model_status()` displays checksum status (verified/unknown/mismatch)

- **Patterns to follow**: Existing `_is_text_file()` function shape, `SkillResult` return pattern

- **Test scenarios**:
  - **Search**:
    - `test_is_text_file_null_byte_detection`: file with `\x00` in content → `_is_text_file` returns False
    - `test_is_text_file_allowed_binary_ext`: `.pyc` file → False (not in TEXT_EXTS, has null bytes)
    - `test_search_skips_large_file`: file > 10MB → skipped with counter increased
    - `test_search_max_scanned_files`: dir with 5001+ files → stops at 5000
  - **Model manager**:
    - `test_download_model_checksum_valid`: mock filesystem, checksum matches → success
    - `test_download_model_checksum_mismatch`: mock checksum mismatch → error, file deleted
    - `test_download_model_partial_cleanup`: `urlretrieve` raises → `.part` file removed
    - `test_model_status_shows_checksum`: after download, status includes "SHA256: verified"
    - `test_model_manifest_contents`: `MODEL_MANIFEST` has all required keys

- **Verification**: `pytest tests/test_skill_search_text.py tests/test_model_manager.py` passes

---

### U5. Clarify compress format as zip-only

- **Goal**: Make it explicit that v0 compress only supports zip. Align router output format with skill capability.

- **Dependencies**: U3 (route returns clarification for missing args)

- **Files**:
  - `garcon/skills/compress_files.py` — modify (add docstring, explicit zip check)
  - `garcon/router.py` — modify (output mentions zip)
  - `tests/test_skill_compress_files.py` — extend
  - `tests/test_router.py` — extend

- **Approach**:
  - `compress_files.py` docstring: "zip-only in v0. Future: tar.gz support."
  - `preview()` and `execute()`: if `output` doesn't end with `.zip`, append `.zip` automatically
  - Router message: "파일을 zip으로 압축합니다." instead of generic "파일 압축을 시작합니다."
  - Router output `args["format"]` = `"zip"` for future use

- **Test scenarios**:
  - `test_compress_appends_zip_extension`: output="archive" → saved as "archive.zip"
  - `test_compress_preserves_explicit_zip`: output="out.zip" → stays "out.zip"
  - `test_compress_router_message_mentions_zip`: router output message includes "zip"

- **Verification**: `pytest tests/test_skill_compress_files.py` passes

---

### U6. Write README and documentation

- **Goal**: Make the project understandable and approachable for new users. Document safety model and architecture decisions.

- **Dependencies**: U1-U5 complete (docs reflect current behavior)

- **Files**:
  - `README.md` — new
  - `docs/SAFETY.md` — new
  - `docs/MODEL.md` — new
  - `docs/SKILLS.md` — new

- **Approach**:
  - **README.md**:
    - What is garcon, why it exists
    - Quick start: `git clone && uv sync && uv run garcon`
    - Usage examples: file list, read, search, organize
    - Supported skills table
    - Model download: `garcon model download`
    - Rule-based vs model router
    - Safety model: preview/confirm/undo
    - Current limitations
  - **SAFETY.md**:
    - Path policy (blocked roots, per-operation zones)
    - Preview/confirm/undo flow
    - Archive extraction safety
    - Threat model (local file access, no network)
  - **MODEL.md**:
    - Intent classification architecture (grammar-constrained one-word → deterministic action build)
    - Model: SmolLM2-135M-Instruct, QuantFactory GGUF, llama.cpp backend
    - Accuracy before fine-tuning (~14%)
    - Fine-tuning path (future)
  - **SKILLS.md**:
    - Per-skill reference: args, behavior, risk level, example input
    - Table format

- **Verification**: `README.md` renders correctly on GitHub; all doc files exist

---

### U7. Add CI pipeline

- **Goal**: Run tests automatically on push/PR to main. Ensure regressions are caught before merge.

- **Dependencies**: All prior units complete

- **Files**:
  - `.github/workflows/ci.yml` — new

- **Approach**:
  - Trigger: `push` and `pull_request` on `main`
  - Job: `test` on `ubuntu-latest`, `macos-latest`
  - Steps:
    - Checkout repo
    - Install `uv`
    - `uv sync`
    - `uv run pytest -v`
  - No model download in CI (tests that require model use `xfail` or mocking)

- **Test scenarios**: N/A — CI is the verification mechanism

- **Verification**: CI passes on opening a PR

---

## Dependencies

- Python >=3.12, `pytest`, `uv` (dev)
- No new runtime dependencies from this work

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Path safety blocks legitimate user workflows | Medium | Test with common home/cwd paths; error message tells user which path was blocked |
| Archive extraction hardening breaks existing archives | Low | Normal zip/tar with relative paths still works; only traversal/symlink rejected |
| Clarification change breaks existing CLI integration | Low | `ask_clarification` is already handled by executor — same code path as existing clarifications |
| CI fails on macOS without Metal | Low | Tests don't load model; `xfail` markers for model-dependent tests |
| Docs go out of sync with code | Medium | Docs written last; U1-U5 are the reference |