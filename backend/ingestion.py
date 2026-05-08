"""
PDF ingestion: extract text, split into overlapping chunks, return metadata.
"""
import re
from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF

from backend.config import CHUNK_SIZE, CHUNK_OVERLAP


def extract_text_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Extract page-level text from a PDF.
    Returns a list of dicts: {page: int, text: str}
    """
    pages = []
    doc = fitz.open(str(pdf_path))
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        text = _clean(text)
        if text.strip():
            pages.append({"page": page_num + 1, "text": text})
    doc.close()
    return pages


def chunk_pages(pages: List[Dict[str, Any]], manual_name: str) -> List[Dict[str, Any]]:
    """
    Split page texts into fixed-size overlapping character chunks.
    Returns list of chunk dicts with metadata.
    """
    chunks = []
    chunk_id = 0
    for page_data in pages:
        text = page_data["text"]
        page_num = page_data["page"]
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk_text = text[start:end].strip()
            if len(chunk_text) > 30:          # skip tiny fragments
                chunks.append({
                    "chunk_id": f"{manual_name}::p{page_num}::c{chunk_id}",
                    "manual": manual_name,
                    "page": page_num,
                    "text": chunk_text,
                })
                chunk_id += 1
            start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def ingest_pdf(pdf_path: Path, manual_name: str) -> List[Dict[str, Any]]:
    """Full pipeline: extract → chunk."""
    pages = extract_text_from_pdf(pdf_path)
    return chunk_pages(pages, manual_name)


# ── helpers ───────────────────────────────────────────────────────────────────
def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()
