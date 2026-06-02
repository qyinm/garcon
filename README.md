# garcon

**garcon** is a tiny local terminal coworker that routes Korean natural language to safe file skills.

Instead of generating shell commands, garcon classifies intent (list, read, search, organize, rename, compress, extract) and runs deterministic, sandboxed actions with **preview → confirm → undo** safety.

## Quick start

```bash
# Install
uv sync

# Run in chat mode
uv run garcon chat
> 파일 목록 보여줘
> log에서 error 찾아줘
> 다운로드 폴더 정리해줘
```

## Usage

### Chat mode

```bash
garcon chat
```

Interactive session. Type `exit`, `quit`, or `종료` to end.

### One-shot mode

```bash
garcon run "파일 목록 보여줘"
garcon run "log에서 error 찾아줘"
garcon run "다운로드 폴더 정리해줘"
```

### Model (optional)

Download the 105 MB SmolLM2 GGUF model for SLM-based intent classification:

```bash
garcon model download
garcon model status
garcon model remove
```

When the model is available, requests are routed through the SLM first, falling back to rule-based matching. Without the model, all requests use the rule-based router.

### Session log

```bash
garcon log
garcon log --limit 5
```

## Supported skills

| Skill | Description | Risk | Confirmation |
|-------|-------------|------|-------------|
| `list_files` | 파일 목록 보기 | low | no |
| `read_file` | 파일 내용 읽기 | low | no |
| `search_text` | 텍스트 검색 | low | no |
| `find_large_files` | 큰 파일 찾기 | low | no |
| `organize_files` | 확장자별 정리 | medium | yes |
| `rename_files` | 파일 이름 변경 | medium | yes |
| `compress_files` | zip 압축 (zip only) | medium | yes |
| `extract_archive` | 압축 해제 | medium | yes |

## Safety model

1. **Preview** — high-risk skills show a plan before executing
2. **Confirm** — user types `y`/`네` to proceed
3. **Undo** — `garcon undo` reverses the most recent operation

### Path policy

- Blocked paths: `/`, `/etc`, `/usr`, `/bin`, `/System`, `/private`, `/var`, `/Library` (including nested)
- Read operations: home directory and current directory allowed
- Write/move operations: home directory and current directory allowed

### Archive extraction safety

- Path traversal via `../../` or absolute paths is rejected
- Symlinks and hardlinks inside archives are rejected
- Existing files are never overwritten

## Rule-based vs model router

| | Rule router | Model router |
|---|---|---|
| Method | Korean keyword matching | SmolLM2-135M-Instruct via llama.cpp |
| Accuracy | ~100% (deterministic) | ~14% before fine-tuning |
| Speed | Instant | ~1-2s |
| Dependency | None | `llama-cpp-python` |
| Fallback | — | Yes (model → rule) |

The model router is **intent classification only**: the model picks one of 11 intent words (`list`, `read`, `search`, `organize`, `rename`, `compress`, `extract`, `refuse`, `finish`, `greeting`, `other`). Parameter extraction and action construction are deterministic and rule-based.

## Current limitations

- Model accuracy is low (~14%) before fine-tuning
- Fine-tuning `HuggingFaceTB/SmolLM2-135M-Instruct` for Korean intent classification is planned
- Only zip format is supported for compression
- No remote git operations

## License

MIT
