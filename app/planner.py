import json
from typing import Any, Dict, List, Optional, Tuple

from .config import MAX_STEPS
from ollama_client import ollama_chat  # uses your root-level file

TOOL_SPECS = [
    {
        "name": "summarize_text",
        "description": "Summarize a text block.",
        "args_schema": {"text": "string"},
    },
    {
        "name": "draft_email",
        "description": "Draft an email with bullet points.",
        "args_schema": {"to": "string", "subject": "string", "bullet_points": "string[]"},
    },
    {
        "name": "create_tasks",
        "description": "Create task items from a list of task titles.",
        "args_schema": {"tasks": "string[]"},
    },
    {
        "name": "schedule_reminder",
        "description": "Schedule a reminder note for a time.",
        "args_schema": {"when": "string", "note": "string"},
    },
]

SYSTEM = """You are a strict JSON planner for a workflow automation agent.

You MUST output ONLY valid JSON (no markdown, no text).
Output must be a JSON array of tool calls.

Each tool call MUST be exactly:
{"name": "<tool_name>", "args": { ... }}

Rules:
- Use ONLY tools from the registry.
- Do NOT invent new tools.
- Do NOT include extra keys (only "name" and "args").
- Args MUST match the args_schema types.
- Prefer using values from Context JSON.
- If a required arg is missing from context, include the key with an empty string "" (for strings) or [] (for lists).
- Maximum number of tool calls: MAX_STEPS.

Correct examples:
[
  {"name":"summarize_text","args":{"text":"..."}},
  {"name":"draft_email","args":{"to":"team@company.com","subject":"Follow-up","bullet_points":["a","b"]}},
  {"name":"schedule_reminder","args":{"when":"tomorrow 09:00","note":"Follow up"}}
]
"""


def _make_prompt(user_goal: str, context: Optional[Dict[str, Any]]) -> str:
    return f"""
Tool registry (name, description, args schema):
{json.dumps(TOOL_SPECS, indent=2)}

MAX_STEPS = {MAX_STEPS}

User goal:
{user_goal}

Context JSON (may be null):
{json.dumps(context, indent=2) if context else "null"}

Return ONLY the JSON array plan now.
""".strip()

def _extract_json(text: str) -> Any:
    """
    Best-effort extraction if the model accidentally adds text.
    We try to locate the first '[' and last ']' and parse.
    """
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        return json.loads(text)
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("Could not find a JSON array in model output.")

def plan_with_ollama(user_goal: str, context: Optional[Dict[str, Any]] = None, model: str = "llama3.1:8b") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns: (plan, debug_info)
    plan is a list of dicts: {"name":..., "args":...}
    debug_info includes raw model output for logging.
    """
    prompt = _make_prompt(user_goal, context)
    raw = ollama_chat(prompt=prompt, model=model, system=SYSTEM)

    try:
        parsed = _extract_json(raw)
    except Exception as e:
        # One repair attempt: tell model to fix JSON only.
        repair_system = SYSTEM + "\nIf the previous output was invalid, fix it and output ONLY valid JSON."
        raw2 = ollama_chat(prompt=f"Fix this into valid JSON array ONLY:\n\n{raw}", model=model, system=repair_system)
        parsed = _extract_json(raw2)
        raw = raw2

    if not isinstance(parsed, list):
        raise ValueError("Planner output is not a JSON array.")

    # Basic validation + truncation
    plan: List[Dict[str, Any]] = []
    for item in parsed[:MAX_STEPS]:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        args = item.get("args", {})
        if name in {t["name"] for t in TOOL_SPECS} and isinstance(args, dict):
            plan.append({"name": name, "args": args})

    return plan, {"raw_output": raw, "prompt": prompt}
