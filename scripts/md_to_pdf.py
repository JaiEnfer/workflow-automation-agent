from pathlib import Path
import re
import sys


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 54
TOP_MARGIN = 54
BOTTOM_MARGIN = 54
FONT_SIZE = 11
LEADING = 15
MAX_CHARS = 90


def clean_markdown_line(line: str) -> str:
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    line = line.replace("`", "")
    line = line.replace("**", "")
    line = line.replace("### ", "")
    line = line.replace("## ", "")
    line = line.replace("# ", "")
    return line.rstrip()


def wrap_line(text: str, width: int = MAX_CHARS) -> list[str]:
    if not text:
        return [""]
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def markdown_to_lines(markdown_text: str) -> list[str]:
    output: list[str] = []
    in_code = False

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip("\n")

        if line.startswith("```"):
            in_code = not in_code
            output.append("")
            continue

        if in_code:
            output.extend(wrap_line(f"    {line}", MAX_CHARS - 4))
            continue

        cleaned = clean_markdown_line(line)
        if not cleaned.strip():
            output.append("")
            continue

        if raw_line.lstrip().startswith(("- ", "* ")):
            cleaned = f"- {cleaned.lstrip('-* ').strip()}"

        output.extend(wrap_line(cleaned))

    return output


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_content_stream(lines: list[str]) -> bytes:
    commands = ["BT", f"/F1 {FONT_SIZE} Tf"]
    y = PAGE_HEIGHT - TOP_MARGIN
    for line in lines:
        if y < BOTTOM_MARGIN:
            break
        commands.append(f"1 0 0 1 {LEFT_MARGIN} {y} Tm")
        commands.append(f"({escape_pdf_text(line)}) Tj")
        y -= LEADING
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def paginate(lines: list[str]) -> list[list[str]]:
    lines_per_page = ((PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN) // LEADING) + 1
    return [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)] or [[]]


def write_pdf(markdown_path: Path, pdf_path: Path) -> None:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    pages = paginate(markdown_to_lines(markdown_text))

    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    content_ids: list[int] = []

    placeholder_pages_id = add_object(b"<< /Type /Pages /Kids [] /Count 0 >>")

    for page_lines in pages:
        stream = build_content_stream(page_lines)
        content = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream
            + b"\nendstream"
        )
        content_id = add_object(content)
        content_ids.append(content_id)

        page = (
            f"<< /Type /Page /Parent {placeholder_pages_id} 0 R "
            f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("latin-1")
        page_id = add_object(page)
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[placeholder_pages_id - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    ).encode("latin-1")

    catalog_id = add_object(f"<< /Type /Catalog /Pages {placeholder_pages_id} 0 R >>".encode("latin-1"))

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_start}\n%%EOF\n"
    )
    pdf.extend(trailer.encode("latin-1"))

    pdf_path.write_bytes(pdf)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/md_to_pdf.py <input.md> <output.pdf>")
        return 1

    markdown_path = Path(sys.argv[1])
    pdf_path = Path(sys.argv[2])
    write_pdf(markdown_path, pdf_path)
    print(pdf_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
