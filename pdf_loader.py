"""
pdf_loader.py
Loads PDFs from data/ folder and provides FAISS vector search.
- Extracts text only (images in PDFs are ignored automatically)
- Supports both English and Urdu text
- Uses sentence-transformers for embeddings + FAISS for search
"""

import os
import numpy as np
from pathlib import Path
import pdfplumber
import PyPDF2

DATA_DIR = Path("data")
_chunks: list[dict] = []

# Try to use FAISS + embeddings, fall back to keyword search if not available
_use_faiss = False
_index     = None
_model     = None

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    _model    = SentenceTransformer("all-MiniLM-L6-v2")
    _index    = None  # built after loading chunks
    _use_faiss = True
    print("[pdf_loader] FAISS + embeddings enabled.")
except Exception:
    print("[pdf_loader] FAISS not available, using keyword search.")


def load_all():
    """Call once at startup to ingest every PDF in data/."""
    DATA_DIR.mkdir(exist_ok=True)
    pdfs = list(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        print("[pdf_loader] No PDFs found in data/ — knowledge base is empty.")
        return
    for pdf in pdfs:
        _ingest(pdf)
    _rebuild_index()
    print(f"[pdf_loader] Loaded {len(_chunks)} chunks from {len(pdfs)} PDF(s).")


def search(query: str, top_k: int = 4) -> str:
    """Return the most relevant chunks as a single context string."""
    if not _chunks:
        return ""
    if _use_faiss and _index is not None:
        return _faiss_search(query, top_k)
    return _keyword_search(query, top_k)


# ── internals ─────────────────────────────────────────────────

def _ingest(path: Path):
    """Extract text from PDF and split into chunks. Images are ignored."""
    text = _extract_text(path)
    if not text.strip():
        print(f"[pdf_loader] Warning: no text extracted from {path.name} (may be image-only)")
        return
    for chunk in _split(text, source=path.name):
        _chunks.append(chunk)


def _extract_text(path: Path) -> str:
    """
    Extract text only from PDF using pdfplumber (falls back to PyPDF2).
    Images, charts, and photos in the PDF are automatically skipped.
    Supports English and Urdu text both.
    """
    # Try pdfplumber first (better text extraction)
    try:
        with pdfplumber.open(path) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            result = "\n".join(pages_text)
            if result.strip():
                return result
    except Exception:
        pass

    # Fall back to PyPDF2
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
    except Exception as e:
        print(f"[pdf_loader] Could not read {path.name}: {e}")
        return ""


def _split(text: str, source: str, size: int = 400, overlap: int = 40) -> list[dict]:
    """Split text into overlapping chunks."""
    words  = text.split()
    chunks = []
    i      = 0
    while i < len(words):
        body = " ".join(words[i: i + size])
        if len(body) > 60:
            chunks.append({"text": body, "source": source})
        i += size - overlap
    return chunks


def _rebuild_index():
    """Build FAISS index from all loaded chunks."""
    global _index
    if not _use_faiss or not _chunks:
        return
    try:
        texts      = [c["text"] for c in _chunks]
        embeddings = _model.encode(texts, show_progress_bar=False).astype("float32")
        _index     = faiss.IndexFlatL2(embeddings.shape[1])
        _index.add(embeddings)
        print(f"[pdf_loader] FAISS index built with {len(_chunks)} vectors.")
    except Exception as e:
        print(f"[pdf_loader] FAISS index build failed: {e}")


def _faiss_search(query: str, top_k: int) -> str:
    """Search using FAISS vector similarity."""
    try:
        q_vec      = _model.encode([query]).astype("float32")
        _, indices = _index.search(q_vec, top_k)
        results    = [_chunks[i]["text"] for i in indices[0] if i < len(_chunks)]
        return "\n\n".join(results)
    except Exception:
        return _keyword_search(query, top_k)


def _keyword_search(query: str, top_k: int) -> str:
    """Fallback keyword search."""
    words  = set(query.lower().split())
    scored = sorted(
        _chunks,
        key=lambda c: len(words & set(c["text"].lower().split())),
        reverse=True,
    )
    return "\n\n".join(c["text"] for c in scored[:top_k])