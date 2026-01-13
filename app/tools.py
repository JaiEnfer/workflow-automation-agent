from typing import Dict, Any, List
import uuid
import datetime

def summarize_text(args: Dict[str, Any]) -> Dict[str, Any]:
    text = str(args.get("text", "")).strip()
    if not text:
        return {"summary": "(no text provided)"}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    summary = "\n".join(lines[:8])
    return {"summary": summary}

def draft_email(args: Dict[str, Any]) -> Dict[str, Any]:
    to = str(args.get("to", "team@company.com"))
    subject = str(args.get("subject", "Follow-up"))
    bullet_points = args.get("bullet_points", [])
    if not isinstance(bullet_points, list):
        bullet_points = [str(bullet_points)]

    body = "Hi,\n\nFollowing up:\n"
    for bp in bullet_points[:10]:
        body += f"- {str(bp)}\n"
    body += "\nBest,\n"
    return {"to": to, "subject": subject, "body": body}

def create_tasks(args: Dict[str, Any]) -> Dict[str, Any]:
    tasks = args.get("tasks", [])
    if not isinstance(tasks, list):
        tasks = [str(tasks)]
    created = [{"id": str(uuid.uuid4())[:8], "title": str(t)} for t in tasks]
    return {"created": created}

def schedule_reminder(args: Dict[str, Any]) -> Dict[str, Any]:
    when = str(args.get("when", "tomorrow 09:00"))
    note = str(args.get("note", "Reminder"))
    created_at = datetime.datetime.now().isoformat(timespec="seconds")
    return {"scheduled_for": when, "note": note, "created_at": created_at}

TOOL_REGISTRY = {
    "summarize_text": summarize_text,
    "draft_email": draft_email,
    "create_tasks": create_tasks,
    "schedule_reminder": schedule_reminder,
}
