import inspect

from garcon.commands import execute_command, get_command
from garcon.commands.register_all import register_all
from garcon.commands.safety import SafetyVerdict, validate_command
from garcon.undo import record_undo

register_all()

MAX_STEPS = 10


def build_initial_context(user_input: str, system_prompt: str) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]


def _format_observation(output: dict, result) -> str:
    stdout = result.stdout or ""
    if len(stdout) > 2000:
        stdout = stdout[:2000] + f"\n... (truncated, {len(result.stdout)} chars total)"
    return f"Observation:\n```\n{stdout}\n```\n(exit code: {0 if result.success else 1})"


def show_preview(action: str, params: dict) -> str:
    cmd = action.replace("_command", "")
    parts = [cmd]
    for k, v in params.items():
        if v is not None and v != "":
            parts.append(f"--{k}={v}")
    return " ".join(parts)


def user_confirms(preview: str) -> bool:
    print(f"\n실행할 명령어: {preview}")
    answer = input("실행할까요? (y/n): ").strip().lower()
    return answer in ("y", "yes", "네", "응", "예", "ㅇ")


def _filter_params(fn, params: dict) -> dict:
    sig = inspect.signature(fn)
    valid = set(sig.parameters.keys())
    return {k: v for k, v in params.items() if k in valid}


def execute_single_step(action: str, params: dict) -> dict:
    cmd_fn = get_command(action)
    if cmd_fn is None:
        return {"success": False, "error": f"Unknown command: {action}", "result": None}

    verdict = validate_command(action, params)
    if not verdict.allowed:
        return {"success": False, "error": verdict.reason, "result": None, "verdict": verdict}

    preview = show_preview(action, params)
    if verdict.requires_confirm and not user_confirms(preview):
        return {"success": False, "error": "사용자가 취소했습니다.", "result": None}

    filtered = _filter_params(cmd_fn, params)
    result = cmd_fn(**filtered)
    if result.undo_info:
        record_undo(action, params, result.undo_info)

    return {"success": True, "result": result, "verdict": verdict}


def execute_agent_loop(
    user_input: str,
    actions: list[dict],
    system_prompt: str = "You are garcon, a Korean-language terminal assistant.",
) -> list[dict]:
    context = build_initial_context(user_input, system_prompt)
    steps: list[dict] = []

    for step_num, action_def in enumerate(actions):
        action = action_def.get("action", "")
        params = action_def.get("params", {})

        step_result = execute_single_step(action, params)
        step = {
            "step": step_num + 1,
            "action": action,
            "params": params,
            "success": step_result["success"],
        }

        if not step_result["success"]:
            step["error"] = step_result.get("error", "")
            steps.append(step)
            break

        result = step_result["result"]
        observation = _format_observation(action_def, result)
        context.append({"role": "assistant", "content": observation})
        step["observation"] = observation
        step["result"] = result
        steps.append(step)

    return steps


def execute_plan(actions: list[dict]) -> list[dict]:
    steps: list[dict] = []

    for step_num, action_def in enumerate(actions):
        action = action_def.get("action", "")
        params = action_def.get("params", {})

        step_result = execute_single_step(action, params)
        step = {
            "step": step_num + 1,
            "action": action,
            "params": params,
            "success": step_result["success"],
        }

        if not step_result["success"]:
            step["error"] = step_result.get("error", "")
            steps.append(step)
            return steps

        result = step_result["result"]
        step["result"] = result.stdout if result.stdout else "ok"
        steps.append(step)

    return steps
