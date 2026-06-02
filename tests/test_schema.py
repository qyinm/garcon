from garcon.schema import GarconAction


def test_basic_action():
    action = GarconAction(
        action="use_skill",
        skill="list_files",
        args={"path": "."},
        risk="low",
    )
    assert action.action == "use_skill"
    assert action.skill == "list_files"
    assert action.args == {"path": "."}
    assert action.risk == "low"
    assert action.requires_confirmation is False


def test_refuse_action():
    action = GarconAction(
        action="refuse",
        message="위험한 요청입니다.",
    )
    assert action.action == "refuse"
    assert action.message == "위험한 요청입니다."


def test_clarification_action():
    action = GarconAction(
        action="ask_clarification",
        message="무슨 작업을 할까요?",
    )
    assert action.action == "ask_clarification"


def test_finish_action():
    action = GarconAction(
        action="finish",
        message="종료합니다.",
    )
    assert action.action == "finish"


def test_default_fields():
    action = GarconAction(action="use_skill", skill="test")
    assert action.args == {}
    assert action.risk == "low"
    assert action.requires_confirmation is False
    assert action.message is None
