from contextlib import asynccontextmanager
import uuid

import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .schemas import RunRequest, ContinueRequest, RunResponse, AgentStep, ToolCall, MissingField
from .agent import run_agent, continue_agent
from .ingest import DocumentIngestError, extract_pdf_text, merge_ingested_context
from .storage import init_db, save_run, load_run, list_runs, read_run
from .reporting import build_markdown_report, markdown_to_basic_html
from .config import APP_TITLE, APP_VERSION, CORS_ALLOW_ORIGINS, DB_PATH, FRONTEND_DIST_DIR, OLLAMA_MODEL, OLLAMA_URL
from ollama_client import OllamaClientError, list_ollama_models, resolve_ollama_model
from .tools import summarize_text


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=APP_TITLE, version=APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS or [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_response(
    run_id: str,
    status: str,
    final_answer: str,
    steps: list[dict],
    proposed_plan: list[dict] | None = None,
    missing_fields: list[dict] | None = None,
    questions: list[str] | None = None,
) -> RunResponse:
    resp = RunResponse(
        run_id=run_id,
        status=status,
        final_answer=final_answer,
        steps=[AgentStep(**step) for step in steps],
    )

    if status == "needs_input":
        resp.questions = questions
        resp.missing_fields = [MissingField(**item) for item in (missing_fields or [])]
        resp.proposed_plan = [ToolCall(**item) for item in (proposed_plan or [])]

    return resp


def _fallback_summary_result(user_goal: str, context: dict, reason: str) -> tuple[dict, list[dict], str]:
    run_id = str(uuid.uuid4())
    summary_result = summarize_text({"text": context.get("text", "")})
    summary_text = summary_result.get("summary", "(no text provided)")
    steps = [
        {
            "thought": "Planner fallback activated because the model did not return valid tool JSON.",
            "tool_call": {"name": "fallback_summary", "args": {"user_goal": user_goal}},
            "tool_result": {"reason": reason},
        },
        {
            "thought": "Summarized the uploaded or pasted text directly.",
            "tool_call": {"name": "summarize_text", "args": {"text": context.get("text", "")}},
            "tool_result": summary_result,
        },
    ]
    result = {"status": "ok", "final_answer": summary_text}
    return result, steps, run_id


@app.get("/health")
def health():
    available_models = []
    resolved_model = None
    model_resolution_error = None
    try:
        available_models = list_ollama_models()
        resolved_model = resolve_ollama_model(OLLAMA_MODEL)
    except OllamaClientError as exc:
        model_resolution_error = str(exc)

    return {
        "status": "ok",
        "app": APP_TITLE,
        "version": APP_VERSION,
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
        "resolved_ollama_model": resolved_model,
        "available_ollama_models": available_models,
        "model_resolution_error": model_resolution_error,
        "db_path": str(DB_PATH),
        "frontend_built": FRONTEND_DIST_DIR.exists(),
    }

@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    try:
        result, steps, run_id = run_agent(req.user_goal, req.context)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

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


@app.post("/run-ingest", response_model=RunResponse)
async def run_ingest(
    user_goal: str = Form(...),
    context_json: str = Form("{}"),
    typed_text: str = Form(""),
    pdf_file: UploadFile | None = File(default=None),
):
    try:
        parsed_context = json.loads(context_json) if context_json.strip() else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Context JSON is invalid: {exc.msg}") from exc

    if parsed_context is not None and not isinstance(parsed_context, dict):
        raise HTTPException(status_code=400, detail="Context JSON must be an object.")

    pdf_text = ""
    if pdf_file is not None:
        if not pdf_file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")
        try:
            pdf_bytes = await pdf_file.read()
            pdf_text = extract_pdf_text(pdf_bytes)
        except DocumentIngestError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    merged_context = merge_ingested_context(parsed_context, typed_text=typed_text, pdf_text=pdf_text)

    try:
        result, steps, run_id = run_agent(user_goal, merged_context)
    except ValueError as exc:
        if "Could not find a JSON array in model output." in str(exc) and merged_context.get("text"):
            result, steps, run_id = _fallback_summary_result(user_goal, merged_context, str(exc))
        else:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    status = result.get("status", "ok")
    proposed_plan = result.get("proposed_plan")

    save_run(
        run_id=run_id,
        user_goal=user_goal,
        status=status,
        final_answer=result.get("final_answer", ""),
        steps=steps,
        proposed_plan=proposed_plan,
        context=merged_context,
    )

    return _build_response(
        run_id=run_id,
        status=status,
        final_answer=result.get("final_answer", ""),
        steps=steps,
        proposed_plan=proposed_plan,
        missing_fields=result.get("missing_fields"),
        questions=result.get("questions"),
    )


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

    try:
        result, steps, run_id = continue_agent(
            run_id=req.run_id,
            user_goal=saved.get("user_goal", ""),
            plan=plan,
            context=merged_context,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    status = result.get("status", "ok")
    proposed_plan = result.get("proposed_plan")  # might still need input

    save_run(
        run_id=req.run_id,
        user_goal=saved.get("user_goal", ""),
        status=status,
        final_answer=result.get("final_answer", ""),
        steps=steps,
        proposed_plan=proposed_plan,
        context=merged_context,
    )

    return _build_response(
        run_id=req.run_id,
        status=status,
        final_answer=result.get("final_answer", ""),
        steps=steps,
        proposed_plan=proposed_plan,
        missing_fields=result.get("missing_fields"),
        questions=result.get("questions"),
    )


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


if FRONTEND_DIST_DIR.exists():
    assets_dir = FRONTEND_DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    def frontend_index():
        return FileResponse(FRONTEND_DIST_DIR / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend_fallback(full_path: str):
        candidate = FRONTEND_DIST_DIR / full_path
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST_DIR / "index.html")
