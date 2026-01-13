from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal

class RunRequest(BaseModel):
    user_goal: str = Field(..., examples=["Summarize notes, draft email, and create tasks."])
    context: Optional[Dict[str, Any]] = None

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]

class AgentStep(BaseModel):
    thought: str
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[Any] = None

class MissingField(BaseModel):
    tool: str
    field: str
    reason: str

class RunResponse(BaseModel):
    run_id: str
    status: Literal["ok", "needs_input"] = "ok"
    final_answer: str
    steps: List[AgentStep]

    # Only present when status="needs_input"
    questions: Optional[List[str]] = None
    missing_fields: Optional[List[MissingField]] = None
    proposed_plan: Optional[List[ToolCall]] = None

class ContinueRequest(BaseModel):
    run_id: str
    # user provides missing values here; we merge into stored context
    context_patch: Dict[str, Any] = Field(default_factory=dict)
