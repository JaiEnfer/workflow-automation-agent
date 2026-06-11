# Frontend

This folder contains a React + Vite frontend for the local workflow agent backend.

## Run locally

1. Install dependencies:

```powershell
npm install
```

2. Start the FastAPI backend on `http://localhost:8000`.

3. Start the frontend:

```powershell
npm run dev
```

## Configuration

Copy `.env.example` to `.env` if you want to override the backend URL:

```powershell
VITE_API_BASE_URL=http://localhost:8000
```

## Features

- Run a new workflow with goal + JSON context
- Paste plain text to summarize without hand-writing JSON
- Upload a PDF and merge extracted text into the run context
- Inspect run output and tool execution steps
- Continue `needs_input` runs with a patch payload
- Browse persisted run history
- Open and inspect full run detail from the sidebar
