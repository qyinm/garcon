# garcon

**garcon** is a tiny local terminal coworker. Korean natural language goes in, Linux commands come out — with safety first.

Instead of generating raw shell commands, garcon classifies intent and runs deterministic, sandboxed actions with **preview → confirm → undo** safety.

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

When the model is available, requests are routed through SLM intent classification. Without the model, garcon shows an error — the model is required for operation.

### Session log

```bash
garcon log
garcon log --limit 5
```

## Supported commands

| Command | Description | Risk | Confirmation |
|---------|-------------|------|-------------|
| `list_files` (`ls`) | 파일 목록 보기 | low | no |
| `read_file` (`cat`) | 파일 내용 읽기 | low | no |
| `search_text` (`grep`) | 텍스트 검색 | low | no |
| `find_large_files` (`find`) | 큰 파일 찾기 | low | no |
| `organize_files` (`mv`) | 확장자별 정리 | medium | yes |
| `rename_files` (`mv`) | 파일 이름 변경 | medium | yes |
| `compress_files` (`tar`) | tar 압축 | medium | yes |
| `extract_archive` (`tar`) | 압축 해제 | medium | yes |

## Safety model

1. **Preview** — high-risk commands show a plan before executing
2. **Confirm** — user types `y`/`네` to proceed
3. **Undo** — `garcon undo` reverses the most recent operation

### Path policy

- Blocked paths: `/`, `/etc`, `/usr`, `/bin`, `/System`, `/private`, `/var`, `/Library` (including nested)
- Read operations: home directory and current working directory allowed
- Write/move operations: home directory and current working directory allowed

### Archive extraction safety

- Path traversal via `../../` or absolute paths is rejected
- Symlinks and hardlinks inside archives are rejected
- Existing files are never overwritten

## Intent classification

garcon uses a small language model (SmolLM2-135M-Instruct) for intent classification. The model picks one of 11 intent words (`list`, `read`, `search`, `organize`, `rename`, `compress`, `extract`, `refuse`, `finish`, `greeting`, `other`). Parameter extraction and action construction are deterministic.

### Model details

| | Value |
|---|---|
| Model | `HuggingFaceTB/SmolLM2-135M-Instruct` |
| Format | Q4_K_M GGUF |
| Size | ~105 MB |
| Backend | llama.cpp via `llama-cpp-python` |

The model router is **intent classification only**. All execution is handled by deterministic command handlers.

### Accuracy

Before fine-tuning, the 135M model's intent classification accuracy is approximately 14%. Most inputs are classified as `list` due to the model's limited capacity and the lack of Korean fine-tuning. Fine-tuning is planned.

## Current limitations

- Model accuracy is low (~14%) before fine-tuning — garcon currently misclassifies many requests
- Only tar format is supported for compression
- No remote git operations

## License

MIT
