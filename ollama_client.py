import httpx
from typing import Optional, Dict, Any, List

from app.config import OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS, OLLAMA_URL


DEFAULT_MODEL = OLLAMA_MODEL


class OllamaClientError(RuntimeError):
    pass


def list_ollama_models() -> List[str]:
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=OLLAMA_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException as exc:
        raise OllamaClientError("Ollama model list request timed out.") from exc
    except httpx.HTTPStatusError as exc:
        raise OllamaClientError(
            f"Ollama model list request failed with status {exc.response.status_code}."
        ) from exc
    except httpx.HTTPError as exc:
        raise OllamaClientError("Failed to reach Ollama. Check OLLAMA_URL and server status.") from exc
    except ValueError as exc:
        raise OllamaClientError("Ollama returned invalid JSON for model list.") from exc

    models = data.get("models", [])
    out: List[str] = []
    for item in models:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip():
                out.append(name)
    return out


def resolve_ollama_model(requested_model: str) -> str:
    available_models = list_ollama_models()
    if requested_model in available_models:
        return requested_model
    if available_models:
        return available_models[0]
    raise OllamaClientError(
        f"Configured model '{requested_model}' is not available and no fallback models were found."
    )


def ollama_chat(prompt: str, model: str = DEFAULT_MODEL, system: Optional[str] = None) -> str:
    """
    Minimal ollama chat wrapper using api/chat.
    """
    message = []
    if system:
        message.append({"role": "system", "content": system})
    message.append({"role": "user", "content": prompt})

    resolved_model = resolve_ollama_model(model)

    payload: Dict[str, Any] = {
        "model": resolved_model,
        "messages": message,
        "stream": False,
        "options": {"temperature": 0.2},
    }

    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException as exc:
        raise OllamaClientError("Ollama request timed out.") from exc
    except httpx.HTTPStatusError as exc:
        raise OllamaClientError(
            f"Ollama request failed with status {exc.response.status_code}."
        ) from exc
    except httpx.HTTPError as exc:
        raise OllamaClientError("Failed to reach Ollama. Check OLLAMA_URL and server status.") from exc
    except ValueError as exc:
        raise OllamaClientError("Ollama returned invalid JSON.") from exc

    content = data.get("message", {}).get("content")
    if not isinstance(content, str):
        raise OllamaClientError("Ollama response did not contain message content.")
    return content
