# AI Workflow Automation Agent (Local Ollama)

A production-style AI workflow automation agent powered by a **local Ollama LLM**.  
The system plans tool calls as **strict JSON**, validates and executes them deterministically, supports **clarification + resume flows**, stores full **audit logs**, and provides a **web UI with run history and report export**.

This project demonstrates how to build **reliable, controllable LLM systems** beyond simple chatbots.

---

## Key Features

### LLM-Based Planning (Ollama)
- Uses a **local Ollama model** to plan actions
- Outputs **strict JSON tool calls**
- Planner is isolated from execution logic (safe design)

### Deterministic Tool Execution
- Tools implemented as pure Python functions
- Arguments validated with **Pydantic**
- Common LLM mistakes automatically normalized

### Clarification & Resume Flow
- If required inputs are missing, agent returns:
  - `needs_input` status
  - specific missing fields
  - human-readable questions
- Execution can be resumed via `/continue` without replanning

### Audit Logging & Observability
- Full step-by-step execution log
- Planner output, tool calls, and results stored
- SQLite backend for persistence

### Report Export
- Export any run as:
  - Markdown (`/report.md`)
  - HTML (`/report.html`)
- Suitable for sharing, debugging, or compliance

### Simple Web UI
- Run new tasks
- Answer clarification questions
- Resume execution
- View run history and full logs

---

## Architecture Overview
```text
User / UI
↓
FastAPI API
↓
LLM Planner (Ollama)
↓
JSON Tool Plan
↓
Validation (Pydantic)
↓
Deterministic Tools
↓
SQLite Audit Log
```

Key design principle:  
**LLM decides *what* to do — code decides *how* it’s done.**

---

## Tech Stack

- Python 3.10+
- FastAPI
- Ollama (local LLM)
- SQLite
- Pydantic
- Minimal HTML / JavaScript frontend

---

## Setup (Windows)

### Install Ollama & pull a model
```powershell
ollama pull llama3.1:8b
```
Verify:
```sh
ollama run llama3.1:8b "Say hello"
```
### Clone repo & create virtual environment
```sh
git clone https://github.com/JaiEnfer/workflow-automation-agent.git
cd workflow-automation-agent
```
```sh
python -m venv .venv
.\.venv\Scripts\activate
```
### Install dependencies
```sh
pip install fastapi uvicorn[standard] httpx pydantic python-dotenv
```
### Run the API
```sh
python -m uvicorn app.main:app --reload
```
Swagger UI: 
```html
htpp://localhost:8000/docs
```

### Run the UI
```sh
python -m http.server 3000
```

Web UI: 
```html
http://localhost:3000/web/index.html
```

## API Endpoints
### Core

**POST /run** — start a new workflow

**POST /continue** — resume after missing inputs

### History

**GET /runs** — list previous runs

**GET /runs/{run_id}** — detailed run data

### Reports

**GET /runs/{run_id}/report.md**

**GET /runs/{run_id}/report.html**

---

## Why This Project

This project was built to demonstrate:

1. How to safely integrate LLMs into production systems
2. Separation of planning and execution
3. Robust handling of invalid or missing model outputs
4. Observability and auditability of AI decisions

It reflects real-world patterns used in AI agents, workflow automation, and internal tooling.

---

## Future Improvements
1. Real integrations (Google Calendar, Jira, Slack)
2. PDF report export
3. Authentication & multi-user support
4. Tool-level permissioning
5. Async/background execution
---

___THANK YOU___
