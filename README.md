# Workflow Automation Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=0A0A0A)](https://react.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-111111)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)
[![Repo](https://img.shields.io/badge/GitHub-workflow--automation--agent-181717?logo=github)](https://github.com/JaiEnfer/workflow-automation-agent)

Local AI workflow automation agent with a FastAPI backend, Ollama-powered planning, SQLite run history, and a simplified React frontend for document summarization.

## What it does

- Accepts pasted text or uploaded PDFs for summarization workflows
- Uses a local Ollama model to plan tool calls
- Falls back to direct summarization when the model does not return valid tool JSON
- Validates and executes supported tools
- Pauses for missing required inputs when needed
- Stores run history and exposes reports
- Serves the built React frontend from FastAPI in production-style setups

## Stack

- FastAPI
- SQLite
- Ollama
- React + Vite

## Supported tools

- `summarize_text`
- `draft_email`
- `create_tasks`
- `schedule_reminder`

## Backend setup

1. Create or activate a virtual environment.
2. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` or set environment variables directly.
4. Make sure Ollama is running and at least one model is installed.
5. Start the API:

```powershell
uvicorn app.main:app --reload
```

## Frontend setup

1. Install frontend dependencies:

```powershell
cd frontend
npm install
```

2. Run the frontend in development:

```powershell
npm run dev
```

The Vite dev server proxies API requests to `http://localhost:8000` by default.

## Typical use

1. Start the backend.
2. Start the frontend.
3. Open the app in the browser.
4. Paste text or upload a text-based PDF.
5. Click `Summarize`.
6. Read the summary in the result panel.

## Production-style frontend serving

Build the frontend:

```powershell
cd frontend
npm run build
```

When `frontend/dist` exists, FastAPI serves the built app at `/`.

## Useful endpoints

- `GET /health`
- `POST /run`
- `POST /run-ingest`
- `POST /continue`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/report.md`
- `GET /runs/{run_id}/report.html`

## Configuration

Backend configuration is environment-driven:

- `APP_TITLE`
- `APP_VERSION`
- `MAX_STEPS`
- `OLLAMA_MODEL`
- `OLLAMA_URL`
- `OLLAMA_TIMEOUT_SECONDS`
- `RUNS_DB_PATH`
- `CORS_ALLOW_ORIGINS`

If `RUNS_DB_PATH` is left empty, the app uses a writable temp-directory SQLite database by default.

## Notes

- The tool implementations are still local/mock workflow actions rather than real SaaS integrations.
- PDF extraction currently works for text-based PDFs. Scanned or image-only PDFs would need OCR as a next step.
- For true production use, the next step would be authentication, authorization, structured logging, and real external integrations.
