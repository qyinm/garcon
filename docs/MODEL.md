# Model architecture

garcon uses a small language model for intent classification. The architecture is designed for low-parameter models (0.1B-1B) running locally via llama.cpp.

## Architecture

```
User input (Korean)
  ↓
Grammar-constrained intent classification  →  one of 11 words
  ↓
Deterministic parameter extraction         →  action dict
  ↓
validate_action()                          →  safety check
  ↓
execute_action()                           →  command run
```

The model does **not** generate JSON or free text. It outputs a single intent word constrained by a GBNF grammar. Parameter extraction and action construction are deterministic.

## Current model

| Field | Value |
|-------|-------|
| Model | `HuggingFaceTB/SmolLM2-135M-Instruct` |
| Format | Q4_K_M GGUF |
| Size | ~105 MB |
| Provider | `QuantFactory/SmolLM2-135M-Instruct-GGUF` |
| Backend | llama.cpp (via `llama-cpp-python`) |
| Download | `garcon model download` |

### Supported intents

`list`, `read`, `search`, `organize`, `rename`, `compress`, `extract`, `refuse`, `finish`, `greeting`, `other`

## Accuracy

Before fine-tuning, the 135M model's intent classification accuracy is approximately 14%. Most inputs are classified as `list` due to the model's limited capacity and the lack of Korean fine-tuning.

## Fine-tuning roadmap

Fine-tuning `HuggingFaceTB/SmolLM2-135M-Instruct` is the primary path to improving accuracy. The grammar-constrained architecture was chosen specifically for this scenario:

1. **Grammar constraint**: only valid intent words can be generated
2. **Keyword validation**: the model's output is accepted only when the input contains matching keywords
3. **Deterministic execution**: regardless of classification, all actions run through the same safety layer

## Future model options

- Fine-tuned `HuggingFaceTB/SmolLM2-135M-Instruct` (target: >80% accuracy)
- `SmolLM2-360M-Instruct` or `SmolLM2-1.7B-Instruct` for better accuracy with larger model
- Custom Korean intent classification model
