# Training Data for SmolLM2 Fine-Tuning

This directory stores training data for fine-tuning SmolLM2-135M-Instruct on Korean → Linux command function calling.

## Directory Structure

```
data/training/
├── raw/              # Raw trace logs from garcon --dev
│   └── trace_*.jsonl # Copied from logs/trace.jsonl per session
├── processed/        # Cleaned & formatted training samples
│   └── train_*.jsonl # Chat-format samples for fine-tuning
└── README.md
```

## Data Collection

Run garcon in dev mode to record traces:

```bash
garcon --dev chat
```

Traces are saved to `logs/trace.jsonl` in the current directory. Each line is a JSON object with:

| Field | Description |
|-------|-------------|
| `ts` | ISO 8601 timestamp |
| `user_input` | User's Korean natural language input |
| `classification` | SLM intent classification |
| `model_raw` | Raw router output dict (action, args) |
| `action` | Parsed action type |
| `args` | Command arguments |
| `blocked` | Whether the action was blocked by safety |
| `result_type` | Execution result type |
| `message` | Result message |
| `confirmed` | Whether user confirmed (for risky ops) |
| `duration_ms` | Processing time in milliseconds |

## Conversion to Training Format

Use `scripts/convert_trace_to_dataset.py` to convert raw traces into chat-format training samples:

```bash
python scripts/convert_trace_to_dataset.py logs/trace.jsonl -o data/training/processed/train.jsonl
```

### Chat Format (v2 Architecture)

Traces contain `Thought`/`Action`/`Action Input` format directly. Training samples use the standard OpenAI chat format:

```json
{
  "messages": [
    {"role": "system", "content": "You are a Linux command assistant..."},
    {"role": "user", "content": "tests 폴더에서 py파일 찾아줘"},
    {"role": "assistant", "content": "Thought: tests 디렉토리에서 Python 파일을 검색합니다.\nAction: find_command\nAction Input: {\"path\": \"tests\", \"name\": \"*.py\"}"}
  ]
}
```

### Conversion mapping

```
Router output → Training format
  user_input          → messages[1].content (user)
  model_raw.action    → Action: {action}
  model_raw.args      → Action Input: {...}
  result              → Observation: ... (if multi-step)
```

## Data Generation (Synthetic)

For initial fine-tuning before enough real traces are collected, use:

```bash
python scripts/generate_training_data.py --output data/training/processed/synthetic.jsonl --count 5000
```

This generates synthetic Korean → command pairs covering all commands with parameter variations.
