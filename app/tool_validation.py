from typing import Any, Dict, Tuple, Optional
from pydantic import ValidationError

from .tool_schemas import (
    SummarizeTextArgs,
    DraftEmailArgs,
    CreateTasksArgs,
    ScheduleReminderArgs,
)

def _ensure_list_of_str(x: Any) -> list[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    # if it's a single string, wrap it
    return [str(x)]

def validate_tool_args(tool_name: str, args: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Returns: (clean_args, error_dict)
    If valid -> clean_args dict, error None
    If invalid -> clean_args None, error dict
    """
    args = args or {}

    try:
        if tool_name == "summarize_text":
            model = SummarizeTextArgs(**args)
            return model.model_dump(), None

        if tool_name == "draft_email":
            # normalize bullet_points
            args["bullet_points"] = _ensure_list_of_str(args.get("bullet_points"))
            model = DraftEmailArgs(**args)
            return model.model_dump(), None

        if tool_name == "create_tasks":
            args["tasks"] = _ensure_list_of_str(args.get("tasks"))
            model = CreateTasksArgs(**args)
            return model.model_dump(), None

        if tool_name == "schedule_reminder":
            model = ScheduleReminderArgs(**args)
            return model.model_dump(), None

        return None, {"type": "unknown_tool", "message": f"Unknown tool: {tool_name}"}

    except ValidationError as e:
        return None, {
            "type": "validation_error",
            "tool": tool_name,
            "message": "Tool arguments failed validation",
            "details": e.errors(),
        }
