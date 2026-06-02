import json
import re

from garcon.commands import COMMANDS

SYSTEM_PROMPT = """You are garcon, a Korean-language terminal assistant.
You help users by running Linux commands step by step.

You have access to the following tools:
[
  {"name": "ls_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "options": {"type": "string"}}, "required": ["path"]}},
  {"name": "find_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "name": {"type": "string"}}, "required": ["path"]}},
  {"name": "grep_command", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern", "path"]}},
  {"name": "cat_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
  {"name": "wc_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "options": {"type": "string"}}, "required": ["path"]}},
  {"name": "head_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "lines": {"type": "integer"}}, "required": ["path"]}},
  {"name": "tail_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "lines": {"type": "integer"}}, "required": ["path"]}},
  {"name": "mkdir_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
  {"name": "rm_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "recursive": {"type": "boolean"}}, "required": ["path"]}},
  {"name": "cp_command", "parameters": {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}}, "required": ["source", "destination"]}},
  {"name": "mv_command", "parameters": {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}}, "required": ["source", "destination"]}},
  {"name": "cd_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
  {"name": "chmod_command", "parameters": {"type": "object", "properties": {"mode": {"type": "string"}, "path": {"type": "string"}}, "required": ["mode", "path"]}},
  {"name": "tar_command", "parameters": {"type": "object", "properties": {"operation": {"type": "string"}, "archive": {"type": "string"}, "files": {"type": "string"}}, "required": ["operation", "archive"]}},
  {"name": "sort_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
  {"name": "uniq_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
  {"name": "diff_command", "parameters": {"type": "object", "properties": {"path1": {"type": "string"}, "path2": {"type": "string"}}, "required": ["path1", "path2"]}},
  {"name": "tree_command", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
  {"name": "Finish", "parameters": {"type": "object", "properties": {"return_type": {"type": "string"}, "final_answer": {"type": "string"}}, "required": ["return_type"]}}
]

Always respond in the following format:
Thought: (your reasoning in Korean)
Action: (command name from the list)
Action Input: (JSON object with parameters)"""

GBNF_GRAMMAR = """
root ::= thought action action-input
thought ::= "Thought:" [^\\n]+ "\\n"
action ::= "Action:" ("ls_command" | "find_command" | "grep_command" | "cat_command" | "wc_command" | "head_command" | "tail_command" | "mkdir_command" | "rm_command" | "cp_command" | "mv_command" | "cd_command" | "chmod_command" | "tar_command" | "sort_command" | "uniq_command" | "diff_command" | "tree_command" | "Finish") "\\n"
action-input ::= "Action Input:" json-object
json-object ::= "{" [^}]* "}"
"""

VALID_ACTIONS = {
    "ls_command", "find_command", "grep_command", "cat_command",
    "wc_command", "head_command", "tail_command", "mkdir_command",
    "rm_command", "cp_command", "mv_command", "cd_command",
    "chmod_command", "tar_command", "sort_command", "uniq_command",
    "diff_command", "tree_command", "Finish",
}


def parse_action_sequence(raw_text: str) -> dict | None:
    thought_m = re.search(r"Thought:\s*(.*?)\n", raw_text)
    action_m = re.search(r"Action:\s*(\S+)", raw_text)
    input_m = re.search(r"Action Input:\s*(\{.*\})", raw_text, re.DOTALL)

    if not action_m:
        return None

    action = action_m.group(1).strip()

    if action not in VALID_ACTIONS:
        return None

    params = {}
    if input_m:
        try:
            params = json.loads(input_m.group(1))
        except json.JSONDecodeError:
            pass

    return {
        "thought": thought_m.group(1).strip() if thought_m else "",
        "action": action,
        "params": params,
    }


def generate_with_context(context: list[dict], model_path: str) -> dict | None:
    try:
        from llama_cpp import Llama, LlamaGrammar

        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            verbose=False,
        )

        messages = []
        for msg in context:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("system", "user", "assistant"):
                messages.append({"role": role, "content": content})

        grammar = LlamaGrammar.from_string(GBNF_GRAMMAR)
        response = llm.create_chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=256,
            grammar=grammar,
        )

        raw = response["choices"][0]["message"]["content"]
        return parse_action_sequence(raw)

    except Exception:
        return None


def router(user_input: str, model_path: str) -> dict | None:
    context = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    return generate_with_context(context, model_path)
