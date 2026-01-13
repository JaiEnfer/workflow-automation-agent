from typing import Any, Dict

EMAIL_KEYS = {
    "email_to": "to",
    "recipient": "to",
    "email_subject": "subject",
    "title": "subject",
    "bullets": "bullet_points",
    "bulletpoints": "bullet_points",
}

REMINDER_KEYS = {
    "time": "when",
    "datetime": "when",
    "message": "note",
    "text": "note",
}

def normalize_args(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map common LLM mistakes to our canonical arg keys.
    """
    if not isinstance(args, dict):
        return {}

    out = dict(args)

    if tool_name == "draft_email":
        for k, v in list(out.items()):
            nk = EMAIL_KEYS.get(k)
            if nk and nk not in out:
                out[nk] = v

    if tool_name == "schedule_reminder":
        for k, v in list(out.items()):
            nk = REMINDER_KEYS.get(k)
            if nk and nk not in out:
                out[nk] = v

    return out
