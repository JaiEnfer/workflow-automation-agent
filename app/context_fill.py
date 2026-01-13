from typing import Any, Dict

def fill_from_context(tool_name: str, args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    If planner left some keys empty, fill from context if available.
    """
    ctx = context or {}
    out = dict(args or {})

    if tool_name == "summarize_text":
        if not out.get("text") and isinstance(ctx.get("text"), str):
            out["text"] = ctx["text"]

    if tool_name == "draft_email":
        if not out.get("to") and isinstance(ctx.get("to"), str):
            out["to"] = ctx["to"]
        if not out.get("subject") and isinstance(ctx.get("subject"), str):
            out["subject"] = ctx["subject"]
        if not out.get("bullet_points") and isinstance(ctx.get("bullet_points"), list):
            out["bullet_points"] = ctx["bullet_points"]

    if tool_name == "create_tasks":
        if not out.get("tasks") and isinstance(ctx.get("tasks"), list):
            out["tasks"] = ctx["tasks"]

    if tool_name == "schedule_reminder":
        if not out.get("when") and isinstance(ctx.get("when"), str):
            out["when"] = ctx["when"]
        if not out.get("note") and isinstance(ctx.get("note"), str):
            out["note"] = ctx["note"]

    return out
