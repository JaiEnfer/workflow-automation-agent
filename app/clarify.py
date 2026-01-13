from typing import Any, Dict, List, Tuple

def extract_missing_fields(err: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Convert our validation_error structure into a simple list:
    [{"tool": "...", "field": "...", "reason": "..."}]
    """
    out: List[Dict[str, str]] = []
    if not err or err.get("type") != "validation_error":
        return out

    tool = err.get("tool", "unknown")
    details = err.get("details", []) or []
    for d in details:
        loc = d.get("loc", [])
        field = loc[-1] if loc else "unknown"
        msg = d.get("msg", "invalid or missing")
        out.append({"tool": tool, "field": str(field), "reason": str(msg)})
    return out

def questions_for_missing(missing: List[Dict[str, str]]) -> List[str]:
    """
    Turn missing_fields into user questions. Keep it simple and clear.
    """
    questions = []
    # group by tool
    by_tool: Dict[str, List[Dict[str, str]]] = {}
    for m in missing:
        by_tool.setdefault(m["tool"], []).append(m)

    for tool, items in by_tool.items():
        fields = [i["field"] for i in items]
        if tool == "draft_email":
            if "to" in fields:
                questions.append("Who should I email? (provide an address like team@company.com)")
            if "subject" in fields:
                questions.append("What should the email subject be?")
            if "bullet_points" in fields:
                questions.append("What bullet points should I include in the email?")
        elif tool == "schedule_reminder":
            if "when" in fields:
                questions.append("When should I schedule the reminder? (e.g., tomorrow 09:00)")
            if "note" in fields:
                questions.append("What should the reminder say?")
        elif tool == "summarize_text":
            if "text" in fields:
                questions.append("What text should I summarize? Paste it in the context.")
        elif tool == "create_tasks":
            if "tasks" in fields:
                questions.append("What tasks should I create? Provide a list of task titles.")
        else:
            questions.append(f"I need more info for tool `{tool}`: {', '.join(fields)}")

    # remove duplicates while preserving order
    seen = set()
    uniq = []
    for q in questions:
        if q not in seen:
            uniq.append(q)
            seen.add(q)
    return uniq
