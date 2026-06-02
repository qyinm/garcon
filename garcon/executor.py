from garcon.schema import GarconAction
from garcon.skills.compress_files import CompressFilesSkill
from garcon.skills.extract_archive import ExtractArchiveSkill
from garcon.skills.find_large_files import FindLargeFilesSkill
from garcon.skills.list_files import ListFilesSkill
from garcon.skills.organize_files import OrganizeFilesSkill
from garcon.skills.read_file import ReadFileSkill
from garcon.skills.rename_files import RenameFilesSkill
from garcon.skills.search_text import SearchTextSkill
from garcon.undo import record_undo

SKILLS = {
    "list_files": ListFilesSkill(),
    "read_file": ReadFileSkill(),
    "search_text": SearchTextSkill(),
    "find_large_files": FindLargeFilesSkill(),
    "organize_files": OrganizeFilesSkill(),
    "rename_files": RenameFilesSkill(),
    "compress_files": CompressFilesSkill(),
    "extract_archive": ExtractArchiveSkill(),
}

EXECUTOR_RESULT_OK = "ok"
EXECUTOR_RESULT_NEEDS_CONFIRMATION = "needs_confirmation"
EXECUTOR_RESULT_REFUSED = "refused"
EXECUTOR_RESULT_CLARIFICATION = "clarification"


def execute_action(
    action: GarconAction, confirmed: bool = False
) -> dict:
    if action.action == "refuse":
        return {
            "type": EXECUTOR_RESULT_REFUSED,
            "ok": True,
            "message": action.message or "요청을 거부했습니다.",
        }

    if action.action == "ask_clarification":
        return {
            "type": EXECUTOR_RESULT_CLARIFICATION,
            "ok": True,
            "message": action.message or "무슨 작업을 할지 더 구체적으로 알려주세요.",
        }

    if action.action == "finish":
        return {
            "type": EXECUTOR_RESULT_OK,
            "ok": True,
            "message": action.message or "작업을 완료했습니다.",
        }

    if action.action == "show_plan":
        return {
            "type": EXECUTOR_RESULT_OK,
            "ok": True,
            "message": action.message or "garcon이 준비됐어요.",
        }

    if action.action != "use_skill":
        return {
            "type": EXECUTOR_RESULT_OK,
            "ok": False,
            "message": f"지원하지 않는 action입니다: {action.action}",
        }

    if action.skill not in SKILLS:
        return {
            "type": EXECUTOR_RESULT_OK,
            "ok": False,
            "message": f"알 수 없는 skill입니다: {action.skill}",
        }

    skill = SKILLS[action.skill]

    if action.requires_confirmation and not confirmed:
        preview_result = skill.preview(action.args)
        return {
            "type": EXECUTOR_RESULT_NEEDS_CONFIRMATION,
            "ok": preview_result.ok,
            "message": preview_result.message,
            "data": preview_result.data,
            "skill": action.skill,
            "args": action.args,
        }

    result = skill.execute(action.args)

    if result.ok and result.undo:
        record_undo(action.skill, result.undo)

    return {
        "type": EXECUTOR_RESULT_OK if result.ok else EXECUTOR_RESULT_REFUSED,
        "ok": result.ok,
        "message": result.message,
        "data": result.data,
        "undo": result.undo,
    }
