---
type: plan
status: active
created: 2026-06-02
---

# feat: v2 Architecture — Linux Commands + Agent Loop

> **Problem**: 8 high-level skills are too coarse. Dynamic composition is impossible — the model only outputs a single intent word, parameters are rule-extracted, and skills can't chain.
>
> **Approach**: Replace 8 high-level skills with 25+ Linux command-level primitives. Model generates Thought/Action/Action Input in an iterative agent loop (one step at a time, with result feedback). SmolLM2-135M fine-tuned on Korean → command sequence data.

## Scope Boundaries

### In Scope
- Replace `garcon/skills/` directory with `garcon/commands/` (25+ command functions)
- Agent loop executor: model → execute → feedback → loop → Finish
- Thought/Action/Action Input output format
- `cd` command with `cwd` state maintained across agent loop steps
- Interactive CLI with step-by-step preview + confirm
- Undo system (backup-based for destructive commands)
- SmolLM2-135M fine-tuning data generation (5K+ samples)
- Rule-based fallback for all 25 commands (when model unavailable)
- Safety layer: command filter, path validation, preview/confirm

### Deferred to Follow-Up Work
- Network commands (`ping`, `curl`) — low priority, require network safety policy
- System commands (`ps`, `df`, `du`, `top`) — low priority, display-only
- Full fine-tuning of SmolLM2-135M (GPU-dependent, separate work item)

### Outside Scope
- Multi-user or remote execution
- Docker or container integration
- Web UI
- Plugin system
- Non-Korean language support

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Command execution | `subprocess.run(cmd, shell=True)` | Simple, fast, matches Linux semantics. Safety via validation layer. |
| Undo mechanism | File backup to `~/.garcon/trash/` before mutation | Works for rm, mv, chmod, cp-overwrite. Restore on `garcon undo`. |
| Agent loop | Synchronous, one step at a time | Each step shows preview, gets confirmation. Iterative = model sees intermediate results. |
| Model format | Thought/Action/Action Input | Grammar-constrained single intent phrase with structured params. GBNF grammar constrains output. |
| Safety model | 3 layers: filter → path validate → preview/confirm | Before command runs. Prevents damage proactively. |
| Session state | In-memory context (no persistence) | Agent loop builds context as it runs. No cross-session state needed. |

## Implementation Units

### U1. Create command framework and registry

**Goal**: Define `CommandResult`, command interface, and registry pattern. All commands follow the same contract.

**Files**:
- `garcon/commands/__init__.py` — registry, `register()`, `execute_command()`
- `garcon/commands/base.py` — `CommandResult` dataclass, safety status

**Approach**:
- `@dataclass CommandResult(stdout: str, stderr: str, success: bool, undo_info: dict | None)`
- Registry is a dict: `COMMANDS: dict[str, Callable]`
- `execute_command(name, params) → CommandResult`
- Safety metadata per command: `SAFETY_RULES[name] = {"danger": "high"|"medium"|"low", "creates_files": bool, "modifies_files": bool}`

**Test scenarios**:
- Registering a command makes it discoverable via `get_command()`
- `execute_command` with unknown name returns error result
- `execute_command` passes params correctly to the command function
- `CommandResult` stores stdout, stderr, success, undo_info correctly

**Test files**: `tests/test_commands/__init__.py`, `tests/test_commands/test_registry.py`

**Verification**: `uv run pytest tests/test_commands/test_registry.py -v` passes

### U2. Implement read-only commands (ls, cat, head, tail, wc, grep, find, sort, uniq, diff, tree)

**Goal**: Implement 11 read-only commands that don't modify files. These are safe to run without confirm.

**Files**:
- `garcon/commands/file_ops.py` — `execute_ls()`, `execute_tree()`
- `garcon/commands/content.py` — `execute_cat()`, `execute_head()`, `execute_tail()`, `execute_wc()`, `execute_diff()`
- `garcon/commands/search.py` — `execute_grep()`, `execute_find()`
- `garcon/commands/text.py` — `execute_sort()`, `execute_uniq()`
- `garcon/commands/safety_rules.py` — register safety metadata

**Approach**:
- Each function is a thin wrapper: sanitize params → build shell command → `subprocess.run(cmd, shell=True, capture_output=True, text=True)` → return `CommandResult`
- Param sanitization: `shlex.quote()` for path values, validate options against allowed list
- Safety: all read-only → `SAFETY_RULES["ls"] = {"danger": "low", ...}`

**Test scenarios**:
- `ls` lists directory contents correctly
- `ls` with non-existent path returns error
- `cat` reads file content
- `cat` on non-existent file returns error
- `head` respects `lines` param
- `tail` respects `lines` param
- `wc -l` counts lines correctly
- `grep` finds matching lines
- `grep` with no matches returns empty output
- `find` finds files by name pattern
- `find` with no matches returns empty output
- `sort` sorts input lines
- `uniq` deduplicates adjacent lines
- `diff` compares two files
- `tree` shows directory tree
- Edge: special characters in filenames (handled by `shlex.quote()`)

**Test files**: `tests/test_commands/test_read_only.py`

**Verification**: `uv run pytest tests/test_commands/test_read_only.py -v` passes

### U3. Implement mutating commands (mkdir, cp, mv, rm, chmod, tar)

**Goal**: Implement 6 mutating commands with safety checks (preview, confirm, undo).

**Files**:
- `garcon/commands/file_ops.py` — add `execute_mkdir()`, `execute_cp()`, `execute_mv()`, `execute_rm()`
- `garcon/commands/permissions.py` — `execute_chmod()`
- `garcon/commands/archive.py` — `execute_tar()`
- `garcon/commands/safety_rules.py` — detailed safety metadata per command

**Approach**:
- Before mutation: record undo info (file paths, original locations/permissions)
- `rm`: move to `~/.garcon/trash/` instead of real delete. `undo_info = {"type": "restore_trash", "items": [{"trash_path": ..., "original_path": ...}]}`
- `mv`: record source path for reverse. `undo_info = {"type": "reverse_mv", "items": [{"from": ..., "to": ...}]}`
- `cp`: only record undo if overwriting. `undo_info = {"type": "restore_backup", ...}`
- `chmod`: stat original mode before change. `undo_info = {"type": "restore_mode", ...}`
- `mkdir`: no undo needed (creating empty dir is safe to leave)
- `tar extract`: same safety as current `extract_archive` (no traversal, no overwrite)
- Safety: `rm`, `chmod` → `"danger": "high"` (requires confirm). `cp --overwrite`, `mv` → `"danger": "medium"`

**Test scenarios**:
- `mkdir` creates directory
- `mkdir` on existing path returns error
- `cp` copies file to destination
- `cp` with non-existent source returns error
- `mv` moves file
- `mv` with non-existent source returns error
- `rm` moves file to trash (doesn't actually delete)
- `rm` on non-existent file returns error
- `rm` with `-r` flag requires confirmation
- `chmod` changes permissions
- `chmod 777` on system path is blocked
- `tar -xzf` extracts archive safely
- `tar -xzf` with path traversal is rejected
- Undo info is populated for each mutation
- Read-only commands have `undo_info=None`

**Test files**: `tests/test_commands/test_mutating.py`

**Verification**: `uv run pytest tests/test_commands/test_mutating.py -v` passes

### U4. Implement safety layer

**Goal**: Command filter, path validator, and dangerous-command blocker. Centralized safety that all commands call before execution.

**Files**:
- `garcon/commands/safety.py` — `validate_command()`, `is_dangerous_command()`, `is_blocked_path()`, `requires_confirmation()`

**Approach**:
- `validate_command(name, params) → SafetyVerdict(allowed, reason, requires_confirm, undo_info)`
- Blocked commands: `sudo`, piping to `rm -rf /`, `> /etc/passwd`, etc.
- Blocked patterns: `rm -rf /`, `chmod 777 /`, `> /dev/sda`
- Path validation: same `BLOCKED_ROOTS` from current `safety.py` (`/`, `/etc`, `/usr`, `/bin`, `/System`, `/Library`, `/private`, `/var`)
- Danger levels: `high` → must confirm, `medium` → preview recommended, `low` → no confirm

**Test scenarios**:
- `rm -rf /` is blocked
- `chmod 777 /etc` is blocked
- `sudo` in any command is blocked
- `ls /etc` is blocked (path validation)
- `ls ~/Downloads` is allowed
- `rm test.txt` is allowed but requires confirmation
- `mv test.txt ~/Documents/` is allowed
- `cat README.md` is allowed without confirmation
- Substring exploits: `rm -rf /tmp` should be allowed, `/etc` in `ls /etc/issue` should be blocked
- Path traversal: `ls ../etc` resolved is blocked

**Test files**: `tests/test_commands/test_safety.py`

**Verification**: `uv run pytest tests/test_commands/test_safety.py -v` passes

### U5. Build agent loop executor

**Goal**: Iterative agent loop that runs model → execute → feedback → loop → Finish.

**Files**:
- `garcon/executor.py` — `execute_agent_loop()`, `build_context()`, `format_step()`

**Approach**:
```
def execute_agent_loop(user_input, model=None, max_steps=5):
    context = [system_prompt, user_input]
    for step in range(max_steps):
        # 1. Generate next action
        if model:
            output = model.generate(context)
        else:
            output = route_with_rules(user_input)  # single-shot fallback

        # 2. Check for Finish
        if output.action == "Finish":
            print(output.params.get("final_answer", ""))
            break

        # 3. Validate safety
        verdict = validate_command(output.action, output.params)
        if not verdict.allowed:
            print(f"⛔ 차단됨: {verdict.reason}")
            break

        # 4. Preview and confirm
        show_preview(output.action, output.params)
        if verdict.requires_confirm and not user_confirms():
            break

        # 5. Execute
        result = execute_command(output.action, output.params)

        # 6. Record undo
        if result.undo_info:
            record_undo(result.undo_info)

        # 7. Append result to context for next iteration
        context.append(format_assistant_output(output, result))

    # End loop
```

**Test scenarios**:
- Single-step execution (ls → result → Finish)
- Multi-step execution (find → wc → Finish)
- Dangerous command is blocked (rm -rf / → blocked)
- User rejects confirmation → loop stops
- Finish action terminates loop and prints answer
- Context accumulates correctly across steps
- Max steps exceeded → loop terminates with message
- Model unavailable fallback → rule-based single shot
- Model generates malformed action → handled gracefully

**Test files**: `tests/test_executor.py`

**Verification**: `uv run pytest tests/test_executor.py -v` passes

### U6. Update model router for Thought/Action format

**Goal**: Model outputs `Thought:\nAction: xxx_command\nAction Input: {...}` instead of single intent word.

**Files**:
- `garcon/model_router.py` — rewrite: new prompt, new GBNF grammar, new parser
- `garcon/model_router.py` — add `generate_with_context()`, `parse_action_sequence()`

**Approach**:
- System prompt includes tool definitions for all 25 commands (like KLC)
- GBNF grammar allows: `Thought:` text, `Action:` command name, `Action Input:` JSON object
- `parse_action_sequence(raw_text) → list of {thought, action, params}` — handles single or multi-step output
- For iterative loop: extract only the FIRST action from model output, execute it, feed result back
- Keyword validation: if model outputs `ls_command` but input has no list/show keywords → confidence check → fallback
- Rule-based fallback: updated to match all 25 commands (same as U7)

**Test scenarios**:
- Model output parsed correctly (Thought/Action/Action Input)
- Multi-step output extracts first action only (for iterative loop)
- Malformed output returns None (fallback to rules)
- GBNF grammar allows valid action names and rejects invalid ones
- Finish action parsed correctly
- Params JSON with missing fields returns partial params (not None)
- Context construction: system + user + assistant steps → correct format

**Test files**: `tests/test_model_router_v2.py`

**Verification**: `uv run pytest tests/test_model_router_v2.py -v` passes

### U7. Rewrite rule-based router for 25 commands

**Goal**: `route_with_rules()` handles all 25 commands with reasonable param extraction. Used as fallback when model is unavailable or unconfident.

**Files**:
- `garcon/router.py` — rewrite: new patterns for all commands
- `garcon/router.py` — add `_extract_pattern()`, `_extract_count()`, `_extract_options()`

**Approach**:
- Korean patterns for each command category (file ops, search, content, system, network, etc.)
- For each command, extract relevant params from keyword context:
  - `ls`: extract path from `<word> 폴더` or `<word> 목록` → `ls -la <path>`
  - `grep`: extract pattern from quotes or `<word> 찾아줘` pattern
  - `find`: extract extension from `<ext> 파일 찾아줘`
  - `wc`: extract path, default `-l`
  - `head`/`tail`: extract path and line count
  - `rm`: extract path, warn if -r
  - `cp`/`mv`: extract source and destination
  - `mkdir`: extract path
  - `sort`/`uniq`/`diff`: extract file paths
  - `tree`: extract path
  - `ps`/`df`/`du`/`top`: default params
  - `ping`: extract host ("구글" → google.com)
  - `chmod`: extract mode and path
  - `tar`: detect compress vs extract from keywords ("풀어" vs "압축")

**Test scenarios**:
- `tests 폴더 ls 해줘` → `ls -la tests`
- `test.txt 내용 읽어줘` → `cat test.txt`
- `error 찾아줘` → `grep "error" .`
- `py파일 찾아줘` → `find . -name "*.py"`
- `test.py 몇 줄이야` → `wc -l test.py`
- `test.log 마지막 5줄 보여줘` → `tail -n 5 test.log`
- `test.txt 처음 3줄 보여줘` → `head -n 3 test.txt`
- `test.txt 복사해줘` → `cp test.txt <default_dest>`
- `임시파일 삭제해줘` → `rm <path>` (requires confirm)
- `backup.tar.gz 압축 풀어줘` → `tar -xzf backup.tar.gz`
- `구글에 핑 날려봐` → `ping -c 4 google.com`
- `정렬해줘` → `sort <path>`
- `중복 제거해줘` → `uniq <path>`
- `a.txt랑 b.txt 비교해줘` → `diff a.txt b.txt`
- `chmod 755 script.sh` → `chmod 755 script.sh`

**Test files**: `tests/test_router_v2.py`

**Verification**: `uv run pytest tests/test_router_v2.py -v` passes

### U8. Rewrite CLI for agent loop UX

**Goal**: Interactive CLI that shows step-by-step progress with preview and confirm.

**Files**:
- `garcon/cli.py` — rewrite `chat` and `run` commands

**Approach**:
```
> tests 폴더에서 py파일 찾아서 각각 몇 줄인지 알려줘

🔍 Step 1: find . -name "*.py" -path "tests/*"
  → test_a.py, test_b.py

💭 다음 명령어를 실행합니다. 계속할까요? (y/n) > y

🔍 Step 2: wc -l test_a.py
  → 15 lines

💭 다음 명령어를 실행합니다. 계속할까요? (y/n) > y

🔍 Step 3: wc -l test_b.py
  → 22 lines

✅ 완료: tests 폴더에서 2개의 Python 파일을 찾았습니다.
  test_a.py: 15줄, test_b.py: 22줄
```

- `garcon run "..."` — one-shot with limited interaction (auto-confirm safe commands)
- `garcon undo` — restore most recent undo operation
- `garcon trash-list` — show files in trash
- `garcon trash-restore <id>` — restore a specific trash item

**Test scenarios**:
- `chat` mode accepts input and loops
- `run` mode executes one request and exits
- Preview display shows command and params
- Confirm prompt accepts y/n/네/아니요
- Undo restores most recent mutation
- `exit`/`quit`/`종료` terminates chat

**Test files**: `tests/test_cli_v2.py`

**Verification**: `uv run pytest tests/test_cli_v2.py -v` passes

### U9. Undo system (trash-based)

**Goal**: Restore files modified or deleted by mutating commands.

**Files**:
- `garcon/undo.py` — rewrite: `record_undo()`, `undo_last()`, `trash_list()`, `trash_restore()`
- `garcon/cli.py` — add `undo` CLI command

**Approach**:
- `~/.garcon/trash/` — directory with timestamped subdirectories per undo operation
- `~/.garcon/undo_log.json` — array of undo records
- Each record: `{id, timestamp, type, items: [{original_path, trash_path?, original_mode?}], command, params}`
- `undo_last()`: read most recent record, restore each item, remove record
- `rm` → files go to `~/.garcon/trash/<timestamp>/`
- `mv` → reverse: `mv current_path original_path`
- `chmod` → `os.chmod(original_path, original_mode)`
- `cp --overwrite` → restore backup file
- `mkdir` → no undo needed
- Max 100 undo records (rotate oldest)

**Test scenarios**:
- `rm` moves file to trash, `undo` restores it
- `mv` is reversed by `undo`
- `chmod` change is reversed by `undo`
- `undo` with no history returns appropriate message
- Trash directory is created on first use
- Old records are rotated (max 100)
- `trash-list` shows trashed files
- `trash-restore <id>` restores specific item

**Test files**: `tests/test_undo_v2.py`

**Verification**: `uv run pytest tests/test_undo_v2.py -v` passes

### U10. Remove old skills and old tests

**Goal**: Delete obsolete skill files and update entry points.

**Files**:
- `garcon/skills/` — entire directory (10 files + __pycache__)
- `tests/test_skill_*.py` — all skill tests (8 files)
- `tests/test_router.py` — old router tests (replaced by test_router_v2.py)
- `tests/test_safety.py` — old safety tests (replaced by test_commands/test_safety.py)
- `tests/test_model_router.py` — old model router tests (replaced by test_model_router_v2.py)
- `garcon/logger.py` — no longer needed (agent loop replaces session log)

**Approach**:
- `git rm -r garcon/skills/`
- `git rm tests/test_skill_*.py`
- Keep `tests/test_model_manager.py` (model download logic still valid)
- Keep `tests/test_parser.py` (parser utility still used)
- Keep `tests/test_schema.py` (basic schemas still relevant)

**Verification**: `uv run pytest tests/ -v --tb=short -m "not slow"` passes with remaining tests

### U11. Generate fine-tuning data (5K+ samples)

**Goal**: Create training dataset for SmolLM2-135M Korean → command function calling.

**Files**:
- `scripts/generate_training_data.py` — data generation script
- `data/training/` — output directory

**Approach**:
- Generate samples for each of 25 commands (100-200 per command = 2,500-5,000)
- Korean input variations: formal, informal, short, verbose
- Parameter variations: different paths, filenames, options, counts
- Multi-step sequences: 500-1,000 samples with 2-4 steps (composition scenarios)
- Format: `{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "Thought: ...\nAction: ...\nAction Input: {...}"}]}`
- Edge cases: dangerous requests → refuse, ambiguous → ask clarification
- Each multi-step sample includes intermediate "Observation" steps

**Test scenarios**:
- Generated data has correct format (valid JSON)
- All 25 commands represented
- Parameter coverage: each command has samples with different param combinations
- Multi-step sequences chain correctly (one action's output feeds next action)
- No dangerous commands in training data (rm -rf /, sudo, etc.)

**Verification**: `python scripts/generate_training_data.py` completes without error, output files are valid JSON

## Dependencies Between Units

```
U1 (registry) ─┬─→ U2 (read-only commands) ──→ U5 (executor)
               ├─→ U3 (mutating commands) ────→ U5
               ├─→ U4 (safety layer) ─────────→ U5
               └─→ U9 (undo system) ─────────→ U5

U5 (executor) ──→ U8 (CLI)

U6 (model router) ──→ U5 (executor gets model from U6)
U7 (rule router) ───→ U5 (executor fallback)

U10 (cleanup) ─── after U1-U9 are stable
U11 (data gen) ─── independent, can run in parallel
```

## System-Wide Impact

- **Safety**: Moving from Python sandbox to shell commands is a risk increase. Mitigated by 3-layer safety (filter, path, confirm) and command-level validation.
- **Undo**: New trash-based system is simpler and more robust than current per-skill undo.
- **Model**: New output format requires new GBNF grammar and retrained model.
- **Tests**: 70% of test files are replaced. New test structure mirrors command structure.
- **User experience**: Interactive step-by-step feedback replaces single-shot execution. More transparent but slower.

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| shell injection | Low | Critical | `shlex.quote()` all path params. Blocked commands filter. |
| Model hallucinates dangerous commands | Medium | High | Safety layer runs before every command regardless of model output. |
| User accidentally confirms dangerous op | Low | Medium | Preview shows full command string. Dangerous ops require explicit "y" + "확인합니다" confirmation. |
| Fine-tuning fails to converge | Medium | High | Rule-based fallback always available. Model optional. |
| 135M can't learn action sequence format | Medium | Medium | Start with single-action training, add sequences in v2.2. |
| rm by mistake | Low | High | rm → trash (not real delete). Undo restores. |

## Outstanding Questions

- `cd` command: maintain cwd across the agent loop? (Deferred to implementation — simplest: pass `cwd` to each subprocess call)
- Network commands: should `ping` and `curl` be blocked by default? (Deferred — implement in U2 as read-only, safety layer can block if needed)
- `chmod 777`: block entirely or require double confirm? (Deferred to U3 implementation)  
