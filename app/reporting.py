from typing import Any, Dict, List, Optional
import datetime
import json

def _ts(ts: Optional[int]) -> str:
    if not ts:
        return ""
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def build_markdown_report(run: Dict[str, Any]) -> str:
    """
    run is the object returned by storage.read_run(run_id)
    """
    run_id = run.get("run_id", "")
    created_at = _ts(run.get("created_at"))
    user_goal = run.get("user_goal", "")
    status = run.get("status", "")
    final_answer = run.get("final_answer", "")

    context = run.get("context")
    proposed_plan = run.get("proposed_plan")
    steps: List[Dict[str, Any]] = run.get("steps", []) or []

    md = []
    md.append(f"# Workflow Agent Report\n")
    md.append(f"- **Run ID:** `{run_id}`")
    md.append(f"- **Created:** {created_at}")
    md.append(f"- **Status:** `{status}`")
    md.append(f"\n## Goal\n{user_goal}\n")

    md.append("## Final Answer\n")
    md.append(final_answer if final_answer else "_(empty)_")
    md.append("")

    if context is not None:
        md.append("## Context\n")
        md.append("```json")
        md.append(json.dumps(context, indent=2, ensure_ascii=False))
        md.append("```")
        md.append("")

    if proposed_plan is not None:
        md.append("## Proposed Plan (Tool Calls)\n")
        md.append("```json")
        md.append(json.dumps(proposed_plan, indent=2, ensure_ascii=False))
        md.append("```")
        md.append("")

    md.append("## Execution Steps (Audit Log)\n")
    for i, s in enumerate(steps, start=1):
        thought = s.get("thought", "")
        tool_call = s.get("tool_call")
        tool_result = s.get("tool_result")

        md.append(f"### Step {i}")
        if thought:
            md.append(f"**Thought:** {thought}\n")

        if tool_call is not None:
            md.append("**Tool call:**")
            md.append("```json")
            md.append(json.dumps(tool_call, indent=2, ensure_ascii=False))
            md.append("```")

        if tool_result is not None:
            md.append("**Tool result:**")
            md.append("```json")
            md.append(json.dumps(tool_result, indent=2, ensure_ascii=False))
            md.append("```")

        md.append("")

    return "\n".join(md)

def markdown_to_basic_html(md_text: str) -> str:
    """
    No extra dependencies. Very basic Markdown-ish HTML renderer.
    Keeps code blocks and paragraphs readable.
    """
    # Minimal safe escaping in non-code lines
    def esc(s: str) -> str:
        return (s.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))

    lines = md_text.splitlines()
    html = []
    html.append("<!doctype html><html><head><meta charset='utf-8'>")
    html.append("<title>Workflow Agent Report</title>")
    html.append("<style>body{font-family:system-ui;max-width:980px;margin:24px auto;padding:0 12px;}pre{background:#f6f6f6;padding:12px;border-radius:10px;overflow:auto;}code{font-family:ui-monospace,Menlo,monospace;}h1,h2,h3{margin-top:20px;}</style>")
    html.append("</head><body>")

    in_code = False
    code_lang = ""

    for line in lines:
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = line[3:].strip()
                html.append("<pre><code>")
            else:
                in_code = False
                code_lang = ""
                html.append("</code></pre>")
            continue

        if in_code:
            html.append(esc(line))
            continue

        # headings
        if line.startswith("# "):
            html.append(f"<h1>{esc(line[2:])}</h1>")
        elif line.startswith("## "):
            html.append(f"<h2>{esc(line[3:])}</h2>")
        elif line.startswith("### "):
            html.append(f"<h3>{esc(line[4:])}</h3>")
        elif line.startswith("- **"):
            # bullet line
            html.append(f"<p>{esc(line)}</p>")
        elif line.strip() == "":
            html.append("<br/>")
        else:
            html.append(f"<p>{esc(line)}</p>")

    if in_code:
        html.append("</code></pre>")

    html.append("</body></html>")
    return "\n".join(html)
