import os
import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


def _load_dotenv() -> None:
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _default_db_path() -> Path:
    return Path(tempfile.gettempdir()) / "workflow-agent" / "runs.db"


_load_dotenv()

MAX_STEPS = int(os.getenv("MAX_STEPS", "6"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))
DB_PATH = Path(os.getenv("RUNS_DB_PATH") or _default_db_path())
CORS_ALLOW_ORIGINS = _split_csv(os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"))
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
APP_TITLE = os.getenv("APP_TITLE", "AI Workflow Automation Agent")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
