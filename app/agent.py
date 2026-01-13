from typing import Any, Dict, List, Optional, Tuple
import uuid

from .tools import TOOL_REGISTRY
from .config import MAX_STEPS
from .planner import plan_with_ollama
from .tool_validation import validate_tool_args
from .clarify import extract_missing_fields, questions_for_missing
from .arg_mapping import normalize_args
from .context_fill import fill_from_context


def _execute_plan(
    plan: List[Dict[str, Any]],
    user_goal: str,
    context: Optional[Dict[str, Any]],
    run_id: str,
    include_planner_step: bool = False,
    planner_debug: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], str]:
    steps: List[Dict[str, Any]] = []

    if include_planner_step:
        steps.append({
            "thought": "Planner (Ollama) produced tool calls.",
            "tool_call": {"name": "planner", "args": {"user_goal": user_goal}},
            "tool_result": {
                "plan": plan,
                "raw_output": (planner_debug or {}).get("raw_output"),
            },
        })

    for call in plan[:MAX_STEPS]:
        name = call.get("name")
        raw_args = call.get("args", {}) or {}
        raw_args = normalize_args(name, raw_args)
        raw_args = fill_from_context(name, raw_args, context or {})


        if not isinstance(name, str) or name not in TOOL_REGISTRY:
            steps.append({
                "thought": "Planner returned an unknown tool. Skipping.",
                "tool_call": call,
                "tool_result": {"error": {"type": "unknown_tool", "message": f"Unknown tool: {name}"}},
            })
            continue

        # Validate
        steps.append({"thought": f"Validating tool args: {name}", "tool_call": call, "tool_result": None})
        clean_args, err = validate_tool_args(name, raw_args)

        if err:
            steps[-1]["tool_result"] = {"error": err}

            if err.get("type") == "validation_error":
                missing = extract_missing_fields(err)
                questions = questions_for_missing(missing)
                return (
                    {
                        "status": "needs_input",
                        "final_answer": "I’m missing a few details before I can continue.",
                        "missing_fields": missing,
                        "questions": questions,
                        "proposed_plan": plan,
                    },
                    steps,
                    run_id,
                )

            continue

        # Execute
        steps.append({
            "thought": f"Calling tool: {name}",
            "tool_call": {"name": name, "args": clean_args},
            "tool_result": None,
        })

        fn = TOOL_REGISTRY[name]
        try:
            steps[-1]["tool_result"] = fn(clean_args)
        except Exception as e:
            steps[-1]["tool_result"] = {"error": {"type": "tool_runtime_error", "message": str(e)}}

    # Compile final answer
    parts: List[str] = []
    for s in steps:
        tc = s.get("tool_call") or {}
        tool_name = tc.get("name")
        if tool_name and tool_name != "planner" and s.get("tool_result") is not None:
            parts.append(f"{tool_name}: {s['tool_result']}")

    final_answer = "Done.\n\n" + "\n".join(parts) if parts else "Done."
    return {"status": "ok", "final_answer": final_answer}, steps, run_id


def run_agent(user_goal: str, context: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]], str]:
    run_id = str(uuid.uuid4())
    plan, debug = plan_with_ollama(user_goal, context)
    return _execute_plan(plan, user_goal, context, run_id, include_planner_step=True, planner_debug=debug)


def continue_agent(run_id: str, user_goal: str, plan: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]], str]:
    # Resume the given plan without replanning
    return _execute_plan(plan, user_goal, context, run_id, include_planner_step=False)
