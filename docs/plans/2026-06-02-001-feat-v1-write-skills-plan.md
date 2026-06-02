# garcon v1: Write Skills + Undo System

- **Created:** 2026-06-02
- **Status:** active
- **Type:** feat
- **Plan ID:** 001

## Problem

garcon v0 has read-only skills (list_files, read_file, search_text). Users
cannot organize, rename, compress, or extract files. The rule-based router
also lacks a `find_large_files` skill which was planned but stubbed.

## Scope

Add write-mode skills with preview/confirm/undo safety, plus a persistence
layer for undo operations.

## Implementation Units

### U1. `find_large_files` skill

**Goal:** Find files above a configurable size threshold in a given path.

**Files:**
- `garcon/skills/find_large_files.py` — create
- `tests/test_skills.py` — add test class

**Approach:**
- Walk the directory tree, skip hidden dirs (same pattern as search_text)
- Collect files >= `min_size_mb`, sort by size descending, return top N
- Low risk, no confirmation needed, no undo

**Test scenarios:**
- Happy path: directory with files > 100MB returns them sorted by size
- Edge case: directory with no large files returns empty result
- Edge case: nonexistent path returns ok=False
- Edge case: file path (not directory) returns correct size for that file

**Dependencies:** none

### U2. `organize_files` skill

**Goal:** Move files by extension rules to target directories (preview + confirm + undo).

**Files:**
- `garcon/skills/organize_files.py` — create
- `garcon/executor.py` — register OrganizeFilesSkill
- `garcon/router.py` — add "정리" patterns
- `tests/test_skills.py` — add test class

**Approach:**
- Accept `source_dir` and `rules` (list of `{extensions, target_dir}`)
- `preview()` builds a plan without moving; `execute()` runs the plan
- Use `shutil.move()` — safe, no raw shell
- Set `risk=medium`, auto-confirmation via HIGH_RISK_SKILLS in safety.py
- Return undo data in SkillResult

**Test scenarios:**
- Happy path: moves matching files to target dir
- Edge case: source_dir doesn't exist
- Edge case: target file already exists (FileExistsError)
- Edge case: no matching files (empty plan)
- Preview returns correct count without moving files

**Dependencies:** U5 (undo log)

### U3. `rename_files` skill

**Goal:** Batch rename files using a pattern (preview + confirm + undo).

**Files:**
- `garcon/skills/rename_files.py` — create
- `garcon/executor.py` — register RenameFilesSkill
- `garcon/router.py` — add "이름 변경" patterns
- `tests/test_skills.py` — add test class

**Approach:**
- Accept `source_dir`, `pattern`, `replace_with` (simple string replace in filename)
- Alternative approach: accept a `rename_map` of `{from_name: to_name}` dict
- `preview()` shows the before/after; `execute()` renames
- Return undo data in SkillResult

**Test scenarios:**
- Happy path: replaces matching pattern in filenames
- Edge case: no files match the pattern
- Edge case: target name already exists
- Preview shows correct rename mapping without actually renaming

**Dependencies:** U5 (undo log)

### U4. `compress_files` and `extract_archive` skills

**Goal:** Create and extract zip/tar archives (preview + confirm + undo).

**Files:**
- `garcon/skills/compress_files.py` — create
- `garcon/skills/extract_archive.py` — create
- `garcon/executor.py` — register both
- `garcon/router.py` — add "압축" patterns
- `tests/test_skills.py` — add test classes

**Approach:**
- Use Python's `zipfile` and `tarfile` modules (no system tar/zip)
- compress: accept `paths` (list of file/dir paths) and `output` path
- extract: accept `archive` path and optional `target_dir`
- Both set `risk=medium`, require confirmation
- extract_archive validates archive extension before extracting
- Undo for compress: store list of compressed files; undo deletes archive
- Undo for extract: store list of extracted files; undo deletes them

**Test scenarios (compress):**
- Happy path: creates zip with listed files
- Edge case: nonexistent source files
- Edge case: output already exists

**Test scenarios (extract):**
- Happy path: extracts zip to target dir
- Edge case: nonexistent archive
- Edge case: unsupported archive format

**Dependencies:** U5 (undo log)

### U5. Undo log system

**Goal:** Persist undo data to `~/.garcon/undo_log.json` so users can revert
write operations.

**Files:**
- `garcon/undo.py` — create
- `garcon/cli.py` — add `undo` command
- `garcon/executor.py` — persist undo after successful execute

**Approach:**
- Store undo log at `~/.garcon/undo_log.json` (append-only array)
- Each entry: `operation_id`, `skill`, `undo_type`, `items` (list of from/to pairs)
- `garcon undo` reads the most recent entry, displays the operations, asks
  confirmation, then reverses them
- After successful undo, remove the entry from the log
- `operation_id` uses ISO 8601 timestamp

**Test scenarios:**
- Happy path: writes and reads undo log
- Happy path: undo reverses a file move
- Edge case: empty undo log
- Edge case: undo log file doesn't exist

**Dependencies:** none (all write skills depend on this)

## Router Patterns to Add

| Korean pattern | Skill | Notes |
|---|---|---|
| "큰 파일", "용량", "큰 용량" | find_large_files | — |
| "정리", "분류", "종류별" | organize_files | Auto-detect "다운로드" path |
| "이름 변경", "이름 바꿔", "rename" | rename_files | — |
| "압축", "zip", "tar" | compress_files | — |
| "압축 풀어", "압축 해제", "extract" | extract_archive | — |

## Undo CLI UX

```
$ garcon undo
최근 실행 취소 가능한 작업:
1. organize_files (2026-06-02T12:30:15) — 3개 파일 이동
되돌릴까요? [y/N]
```

## Dependencies

```
U5 (undo log) ──┬── U2 (organize_files)
                 ├── U3 (rename_files)
                 └── U4 (compress/extract)

U1 (find_large_files) — no dependencies
```

## Risks

- `shutil.move` across filesystems (same volume): fast. Different volumes:
  copy+delete. Should still work correctly, just slower.
- Zip bomb protection: `extract_archive` should check total extracted size
  before extracting.
- Undo log uncapped: Could grow unbounded. v1 starts with append-only;
  consider size cap or TTL in v2.

## Deferred to Implementation

- `delete_files` skill — intentionally excluded, high risk
- Undo log size management (rotation/cap)
- `garcon undo --list` to show all undoable operations

## Verification

- `uv run pytest` — all tests pass
- Manual e2e: create temp dir, run organize/rename via CLI, verify undo
