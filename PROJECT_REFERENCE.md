# Project Reference

## Overview

This project is a local-first workflow automation agent built with FastAPI, a simple static HTML frontend, SQLite for run history, and Ollama for planning tool calls.

The app accepts a natural-language goal plus optional JSON context, asks a local LLM to produce a structured tool plan, validates and executes the plan, persists the run, and exposes the result plus an audit log through API and UI.

## What the Project Does

The current agent supports four workflow-style tools:

1. `summarize_text`
2. `draft_email`
3. `create_tasks`
4. `schedule_reminder`

The system is intentionally lightweight:

- Planning is LLM-driven.
- Execution is deterministic Python code.
- Missing arguments are handled through validation plus a follow-up `needs_input` flow.
- Every run is stored in `runs.db` and can be revisited later.

## Architecture

High-level flow:

1. Client sends `user_goal` and optional `context` to `POST /run`.
2. `app.agent.run_agent()` generates a `run_id`.
3. `app.planner.plan_with_ollama()` asks Ollama for a JSON array of tool calls.
4. `app.agent._execute_plan()` normalizes args, fills from context, validates, then executes tools from `TOOL_REGISTRY`.
5. If required arguments are missing, the API returns `status = "needs_input"` with questions and a stored `proposed_plan`.
6. Client sends `run_id` plus `context_patch` to `POST /continue`.
7. The stored plan resumes without replanning.
8. Run results, steps, plan, and context are saved to SQLite.

## Main Components

### Backend

- [app/main.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/main.py) defines the FastAPI app and all HTTP endpoints.
- [app/agent.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/agent.py) orchestrates planning, validation, execution, and final response assembly.
- [app/planner.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/planner.py) builds the LLM prompt and parses planner output into tool calls.
- [ollama_client.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/ollama_client.py) wraps the Ollama HTTP API.
- [app/tools.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/tools.py) contains the executable tool implementations.
- [app/tool_validation.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/tool_validation.py) validates tool inputs with Pydantic models.
- [app/tool_schemas.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/tool_schemas.py) defines tool argument schemas.
- [app/arg_mapping.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/arg_mapping.py) maps common LLM argument-name mistakes to canonical keys.
- [app/context_fill.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/context_fill.py) fills blank planner args from provided context.
- [app/clarify.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/clarify.py) converts validation failures into user-facing questions.
- [app/storage.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/storage.py) manages SQLite persistence.
- [app/reporting.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/reporting.py) generates Markdown and simple HTML run reports.
- [app/schemas.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/schemas.py) defines API request and response models.
- [app/config.py](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/app/config.py) holds simple runtime constants.

### Frontend

- [web/index.html](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/web/index.html) is a static UI that talks directly to the FastAPI backend.

Frontend capabilities:

- Start a run with goal + context JSON
- Continue a paused run after missing-field prompts
- View response payload and debug steps
- Browse previous runs from history
- Load full details for a selected run

### Data

- [runs.db](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/runs.db) stores persisted run history.
- [assets/UI_screenshot.png](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/assets/UI_screenshot.png) appears to be a UI reference asset.
- [AI_Workflow_Agent_Report_and_Interview_Prep.docx](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/AI_Workflow_Agent_Report_and_Interview_Prep.docx) is present but currently untracked by git.

## Tool Inventory

### `summarize_text`

Input:

- `text: str`

Behavior:

- Returns the first non-empty lines from the input text as a lightweight summary.

### `draft_email`

Input:

- `to: str`
- `subject: str`
- `bullet_points: list[str]`

Behavior:

- Builds a plain-text email body from provided bullets.

### `create_tasks`

Input:

- `tasks: list[str]`

Behavior:

- Returns task objects with short generated IDs and titles.

### `schedule_reminder`

Input:

- `when: str`
- `note: str`

Behavior:

- Returns reminder metadata with timestamped creation time.

## API Reference

### `POST /run`

Request body:

```json
{
  "user_goal": "Summarize notes, create tasks, draft an email, and schedule a reminder",
  "context": {
    "text": "Meeting notes...",
    "to": "team@company.com",
    "subject": "MVP timeline follow-up",
    "bullet_points": ["Ship MVP in 2 weeks"],
    "when": "tomorrow 09:00",
    "note": "Follow up on action items"
  }
}
```

Response notes:

- Returns `status: "ok"` when execution completes.
- Returns `status: "needs_input"` when required tool args are missing.
- Includes `steps` as an execution/audit log.

### `POST /continue`

Request body:

```json
{
  "run_id": "<existing run id>",
  "context_patch": {
    "to": "team@company.com",
    "subject": "Follow-up"
  }
}
```

Behavior:

- Loads the previously saved `proposed_plan`
- Merges stored context with the patch
- Resumes execution without asking Ollama to replan

### `GET /runs`

Returns recent run summaries.

### `GET /runs/{run_id}`

Returns full stored run details including steps, plan, and context.

### `GET /runs/{run_id}/report.md`

Returns a generated Markdown report for a run.

### `GET /runs/{run_id}/report.html`

Returns a lightweight HTML rendering of the same report.

## Persistence Model

SQLite table: `runs`

Columns:

- `run_id TEXT PRIMARY KEY`
- `created_at INTEGER`
- `user_goal TEXT`
- `status TEXT`
- `final_answer TEXT`
- `steps_json TEXT`
- `proposed_plan_json TEXT`
- `context_json TEXT`

The app uses JSON-encoded text fields for steps, plan, and context rather than normalized relational tables.

## Planner and Validation Behavior

Planner rules:

- The LLM is instructed to return only a JSON array of tool calls.
- The planner is limited by `MAX_STEPS = 6`.
- Only tools listed in `TOOL_SPECS` are accepted.
- A best-effort JSON extraction and one repair pass are implemented.

Execution safeguards:

- Unknown tools are skipped and logged in steps.
- Common argument key mistakes are remapped before validation.
- Blank values may be filled from request context.
- Pydantic validation failures are translated into missing-field prompts for the user.

## Run States

### `ok`

Execution finished and a final answer was assembled.

### `needs_input`

Execution paused because a validated tool call is missing required data. The API returns:

- `questions`
- `missing_fields`
- `proposed_plan`

That plan is persisted and reused in `/continue`.

## Expected Local Runtime

This project appears intended to run locally with:

- Python
- FastAPI
- Pydantic
- HTTPX
- Uvicorn or another ASGI server
- Ollama running at `http://localhost:11434`
- A local Ollama model such as `llama3.1:8b`

Likely backend start command:

```powershell
uvicorn app.main:app --reload
```

Frontend use:

- Open [web/index.html](/d:/Project/Machine%20Learning/ai_agent/workflow-agent/web/index.html) in a browser.
- The UI expects the API at `http://localhost:8000`.

## Repository Map

```text
workflow-agent/
|-- app/
|   |-- agent.py
|   |-- arg_mapping.py
|   |-- clarify.py
|   |-- config.py
|   |-- context_fill.py
|   |-- main.py
|   |-- planner.py
|   |-- reporting.py
|   |-- schemas.py
|   |-- storage.py
|   |-- tool_schemas.py
|   |-- tool_validation.py
|   `-- tools.py
|-- assets/
|   `-- UI_screenshot.png
|-- web/
|   `-- index.html
|-- ollama_client.py
|-- runs.db
|-- test_ollama.py
`-- PROJECT_REFERENCE.md
```

## Known Gaps and Risks

- No `README.md` is present, so setup knowledge currently lives in code.
- No dependency manifest such as `requirements.txt` or `pyproject.toml` is present.
- `ollama_client.py` declares `payload: DICT[str, Any]`, which looks like a typo and may fail at runtime because `DICT` is not imported.
- Some UI strings appear to have encoding artifacts such as `Iâ€™m` and `â€¢`.
- CORS is fully open with `allow_origins=["*"]`, which is acceptable for local demos but not production-ready.
- Tool implementations are mock/local behaviors rather than real integrations with email, task systems, or calendar/reminder backends.
- Report HTML rendering is intentionally basic and does not fully parse Markdown semantics.

## Suggested Next Improvements

1. Add `README.md` with install, run, and architecture notes.
2. Add a dependency file and reproducible setup instructions.
3. Fix the `DICT` typo in `ollama_client.py`.
4. Add automated tests for planner parsing, validation, and `/continue` flow.
5. Replace mock tools with real integrations or adapter interfaces.
6. Move hard-coded frontend API URL into configuration.
