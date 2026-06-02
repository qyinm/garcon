from garcon.model_router import (
    VALID_ACTIONS,
    GBNF_GRAMMAR,
    parse_action_sequence,
)


def test_parse_valid_action():
    text = "Thought: 파일 목록을 확인합니다.\nAction: ls_command\nAction Input: {\"path\": \".\"}"
    result = parse_action_sequence(text)
    assert result is not None
    assert result["action"] == "ls_command"
    assert result["params"] == {"path": "."}
    assert "파일 목록" in result["thought"]


def test_parse_finish_action():
    text = "Thought: 작업 완료.\nAction: Finish\nAction Input: {\"return_type\": \"final\", \"final_answer\": \"완료되었습니다.\"}"
    result = parse_action_sequence(text)
    assert result is not None
    assert result["action"] == "Finish"
    assert result["params"]["final_answer"] == "완료되었습니다."


def test_parse_first_action_only():
    text = "Thought: 첫 번째 단계.\nAction: ls_command\nAction Input: {\"path\": \".\"}\nThought: 두 번째 단계.\nAction: wc_command\nAction Input: {\"path\": \"test.txt\"}"
    result = parse_action_sequence(text)
    assert result is not None
    assert result["action"] == "ls_command"


def test_malformed_output_returns_none():
    result = parse_action_sequence("이건 잘못된 출력입니다")
    assert result is None


def test_invalid_action_returns_none():
    text = "Thought: test\nAction: invalid_action\nAction Input: {}"
    result = parse_action_sequence(text)
    assert result is None


def test_finish_in_valid_actions():
    assert "Finish" in VALID_ACTIONS


def test_ls_in_valid_actions():
    assert "ls_command" in VALID_ACTIONS


def test_all_actions_are_valid():
    for action in ["ls_command", "cat_command", "wc_command", "head_command",
                   "tail_command", "grep_command", "find_command", "mkdir_command",
                   "rm_command", "cp_command", "mv_command", "cd_command",
                   "chmod_command", "tar_command", "sort_command", "uniq_command",
                   "diff_command", "tree_command", "Finish"]:
        assert action in VALID_ACTIONS


def test_parse_partial_params():
    text = "Thought: test\nAction: ls_command\nAction Input: {}"
    result = parse_action_sequence(text)
    assert result is not None
    assert result["params"] == {}


def test_grammar_contains_action_names():
    for action in ["ls_command", "cat_command", "Finish"]:
        assert action in GBNF_GRAMMAR


def test_grammar_rejects_invalid():
    assert "sudo_command" not in GBNF_GRAMMAR
