from typing import Any, Literal

from pydantic import BaseModel, Field

ActionType = Literal[
    "use_skill",
    "ask_clarification",
    "show_plan",
    "finish",
    "refuse",
]

RiskLevel = Literal["low", "medium", "high"]


class GarconAction(BaseModel):
    action: ActionType
    skill: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    risk: RiskLevel = "low"
    requires_confirmation: bool = False
    message: str | None = None
