from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

from src.rag.schemas import CVChunk, CVDocument


def read_cv(path: str | Path, cv_id: str) -> CVDocument:
    path = Path(path)
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("CV exceeds the 10 MiB input limit.")
    if path.suffix.lower() in {".md", ".txt"}:
        raw = path.read_text(encoding="utf-8-sig")
    elif path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported; export an unlocked copy.")
        pages = [page.extract_text() or "" for page in reader.pages]
        if any(not page.strip() for page in pages):
            raise ValueError("PDF contains a page without extractable text. Run OCR or export Markdown first.")
        raw = "\n\n".join(pages)
    else:
        raise ValueError("Supported CV formats: .pdf, .md, .txt")
    raw = unicodedata.normalize("NFKC", raw).replace("\x00", "")
    text = "\n".join(re.sub(r"[^\S\n]+", " ", line).strip() for line in raw.splitlines()).strip()
    if not text:
        raise ValueError("CV contains no extractable text.")
    return CVDocument(cv_id=cv_id, source_name=path.name,
                      content_hash=hashlib.sha256(text.encode()).hexdigest(), text=text)


def chunk_cv(document: CVDocument, chunk_size: int = 900, overlap: int = 150) -> list[CVChunk]:
    """Section-aware character windows; offsets refer to normalized document text."""
    if not 32 <= chunk_size <= 2000 or not 0 <= overlap < chunk_size:
        raise ValueError("Use chunk_size 32..2000 and 0 <= overlap < chunk_size.")
    text = document.text
    headings = list(re.finditer(r"(?m)^#{1,6} +(.+)$", text))
    boundaries = [(0, "Document")]
    for match in headings:
        if match.start() == 0:
            boundaries[0] = (0, match[1])
        else:
            boundaries.append((match.start(), match[1]))
    chunks = []
    for i, (start, section) in enumerate(boundaries):
        stop = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
        while start < stop:
            end = min(start + chunk_size, stop)
            if end < stop:
                split = text.rfind(" ", start + chunk_size // 2, end)
                if split > start:
                    end = split
            left, right = start, end
            while left < right and text[left].isspace():
                left += 1
            while right > left and text[right - 1].isspace():
                right -= 1
            if left < right:
                digest = hashlib.sha256(f"{document.cv_id}:{document.content_hash}:{left}:{right}".encode()).hexdigest()[:24]
                chunks.append(CVChunk(chunk_id=digest, cv_id=document.cv_id, section=section,
                                      ordinal=len(chunks), text=text[left:right], start=left, end=right))
            if end == stop:
                break
            start = max(start + 1, end - overlap)
    return chunks
