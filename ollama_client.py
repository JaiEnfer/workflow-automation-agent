import httpx
from typing import Optional, Dict, Any

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1:8b"

def ollama_chat(prompt: str, model: str = DEFAULT_MODEL, system: Optional[str]= None) -> str:
    '''
    Minimal ollama chat wrapper using api/chat.
    '''
    message = []
    if system:
        message.append({"role":"system", "content":system})
    message.append({"role":"user", "content":prompt})

    payload: DICT[str, Any] = {
        "model":model,
        "messages": message,
        "stream":False,
        "options": {"temperature": 0.2}
    }

    r = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]