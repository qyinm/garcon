"""
Convert garcon --dev trace logs to training dataset for SmolLM2 fine-tuning.

Usage:
    python scripts/convert_trace_to_dataset.py logs/trace.jsonl -o data/training/processed/train.jsonl
"""

import json
import argparse
from pathlib import Path


def convert_trace(trace_path: str, output_path: str):
    traces = []
    with open(trace_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                traces.append(json.loads(line))

    samples = []
    for t in traces:
        user_input = t.get("user_input", "")
        if not user_input:
            continue

        model_raw = t.get("model_raw") or {}
        action = t.get("action")
        skill = t.get("skill")
        args = t.get("args")
        result_type = t.get("result_type")
        message = t.get("message")

        if t.get("error"):
            continue

        if t.get("blocked"):
            samples.append({
                "messages": [
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": f"Thought: 안전 정책에 따라 차단되었습니다.\nAction: refuse_command\nAction Input: {{}}"},
                ]
            })
            continue

        assistant_parts = []
        assistant_parts.append(f"Thought: {skill} 작업을 실행합니다.")
        assistant_parts.append(f"Action: {skill}_command")
        if args:
            assistant_parts.append(f"Action Input: {json.dumps(args, ensure_ascii=False)}")
        else:
            assistant_parts.append("Action Input: {}")

        samples.append({
            "messages": [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": "\n".join(assistant_parts)},
            ]
        })

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print(f"Converted {len(traces)} traces → {len(samples)} training samples")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert trace logs to training dataset")
    parser.add_argument("trace_path", help="Path to trace.jsonl file")
    parser.add_argument("-o", "--output", default="data/training/processed/train.jsonl", help="Output path")
    args = parser.parse_args()
    convert_trace(args.trace_path, args.output)
