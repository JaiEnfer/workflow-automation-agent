from io import BytesIO
from typing import Any, Dict, Optional


class DocumentIngestError(ValueError):
    pass


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise DocumentIngestError(
            "PDF upload requires the 'pypdf' package to be installed."
        ) from exc

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:
        raise DocumentIngestError("Could not read the uploaded PDF.") from exc

    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            parts.append(text)

    combined = "\n\n".join(parts).strip()
    if not combined:
        raise DocumentIngestError("The uploaded PDF did not contain extractable text.")
    return combined


def merge_ingested_context(
    base_context: Optional[Dict[str, Any]],
    typed_text: str = "",
    pdf_text: str = "",
) -> Dict[str, Any]:
    context = dict(base_context or {})

    existing_text = context.get("text")
    text_segments = []
    if isinstance(existing_text, str) and existing_text.strip():
        text_segments.append(existing_text.strip())
    if typed_text.strip():
        text_segments.append(typed_text.strip())
    if pdf_text.strip():
        text_segments.append(pdf_text.strip())

    if text_segments:
        context["text"] = "\n\n".join(text_segments)

    return context


def extract_pdf_text(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        return ""
    return _extract_pdf_text(pdf_bytes)
