from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import RunRequest, ContinueRequest, RunResponse, AgentStep, ToolCall, MissingField
from .agent import run_agent, continue_agent
from .storage import init_db, save_run, load_run, list_runs, read_run
from fastapi.responses import PlainTextResponse, HTMLResponse
from .reporting import build_markdown_report, markdown_to_basic_html


app = FastAPI(title="AI Workflow Automation Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    result, steps, run_id = run_agent(req.user_goal, req.context)

    status = result.get("status", "ok")
    proposed_plan = result.get("proposed_plan")

    save_run(
        run_id=run_id,
        user_goal=req.user_goal,
        status=status,
        final_answer=result.get("final_answer", ""),
        steps=steps,
        proposed_plan=proposed_plan,
        context=req.context,
    )

    resp = RunResponse(
        run_id=run_id,
        status=status,
        final_answer=result.get("final_answer", ""),
        steps=[AgentStep(**s) for s in steps],
    )

    if status == "needs_input":
        resp.questions = result.get("questions")
        resp.missing_fields = [MissingField(**m) for m in (result.get("missing_fields") or [])]
        resp.proposed_plan = [ToolCall(**tc) for tc in (proposed_plan or [])]

    return resp

@app.post("/continue", response_model=RunResponse)
def cont(req: ContinueRequest):
    saved = load_run(req.run_id)
    if not saved:
        raise HTTPException(status_code=404, detail="run_id not found")

    plan = saved.get("proposed_plan")
    if not plan:
        raise HTTPException(status_code=400, detail="No proposed_plan stored for this run_id")

    # Merge stored context with patch
    context = saved.get("context") or {}
    context_patch = req.context_patch or {}
    merged_context = {**context, **context_patch}

    result, steps, run_id = continue_agent(
        run_id=req.run_id,
        user_goal=saved.get("user_goal", ""),
        plan=plan,
        context=merged_context,
    )

    status = result.get("status", "ok")
    proposed_plan = result.get("proposed_plan")  # might still need input

    save_run(
        run_id=req.run_id,
        user_goal=req.user_goal,
        status=status,
        final_answer=result.get("final_answer", ""),
        steps=steps,
        proposed_plan=proposed_plan,
        context=merged_context,
    )

    resp = RunResponse(
        run_id=req.run_id,
        status=status,
        final_answer=result.get("final_answer", ""),
        steps=[AgentStep(**s) for s in steps],
    )

    if status == "needs_input":
        resp.questions = result.get("questions")
        resp.missing_fields = [MissingField(**m) for m in (result.get("missing_fields") or [])]
        resp.proposed_plan = [ToolCall(**tc) for tc in (proposed_plan or [])]

    return resp
@app.get("/runs")
def runs(limit: int = 50):
    return {"runs": list_runs(limit=limit)}

@app.get("/runs/{run_id}")
def run_details(run_id: str):
    r = read_run(run_id)
    if not r:
        raise HTTPException(status_code=404, detail="run_id not found")
    return r
@app.get("/runs/{run_id}/report.md", response_class=PlainTextResponse)
def report_md(run_id: str):
    r = read_run(run_id)
    if not r:
        raise HTTPException(status_code=404, detail="run_id not found")
    md = build_markdown_report(r)
    return PlainTextResponse(md, media_type="text/markdown")

@app.get("/runs/{run_id}/report.html", response_class=HTMLResponse)
def report_html(run_id: str):
    r = read_run(run_id)
    if not r:
        raise HTTPException(status_code=404, detail="run_id not found")
    md = build_markdown_report(r)
    html = markdown_to_basic_html(md)
    return HTMLResponse(html)
