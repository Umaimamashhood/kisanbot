"""
pdf_loader.py
Loads all PDFs from the data/ folder and provides semantic search using FAISS.
"""

import os
from pathlib import Path
import pdfplumber
import PyPDF2
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# Folder containing PDFs
DATA_DIR = Path("data")

# Embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# FAISS index (384 dimensions for this model)
index = faiss.IndexFlatL2(384)

# Storage for text chunks
_chunks = []


# ── LOAD ALL PDFs ─────────────────────────────────────

def load_all():
    """Load and process all PDFs in the data directory."""
    
    pdfs = list(DATA_DIR.glob("*.pdf"))

    if not pdfs:
        print("[pdf_loader] No PDFs found in data/")
        return

    for pdf in pdfs:
        _ingest(pdf)

    print(f"[pdf_loader] Loaded {len(_chunks)} chunks from {len(pdfs)} PDF(s)")


# ── SEARCH FUNCTION (FAISS) ───────────────────────────

def search(query: str, top_k: int = 4) -> str:
    """Return most relevant text chunks using semantic search."""

    if len(_chunks) == 0:
        return ""

    # Convert query to embedding
    query_vector = model.encode(query)

    # Search FAISS index
    D, I = index.search(np.array([query_vector]).astype("float32"), top_k)

    results = []

    for idx in I[0]:
        if idx < len(_chunks):
            results.append(_chunks[idx]["text"])

    return "\n\n".join(results)


# ── INTERNAL FUNCTIONS ─────────────────────────────────


def _ingest(path: Path):
    """Extract text and store embeddings."""

    text = _extract(path)

    if not text.strip():
        print(f"[pdf_loader] Warning: no text extracted from {path.name}")
        return

    chunks = _split(text, source=path.name)

    for chunk in chunks:

        text_chunk = chunk["text"]

        # Convert chunk to embedding
        embedding = model.encode(text_chunk)

        # Add to FAISS index
        index.add(np.array([embedding]).astype("float32"))

        # Store text chunk
        _chunks.append(chunk)


def _extract(path: Path) -> str:
    """Extract text from PDF."""

    try:
        with pdfplumber.open(path) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)

        if text.strip():
            return text
    except Exception:
        pass

    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        print(f"[pdf_loader] Could not read {path.name}: {e}")
        return ""


def _split(text: str, source: str, size: int = 400, overlap: int = 40):
    """Split text into overlapping chunks."""

    words = text.split()

    chunks = []
    i = 0

    while i < len(words):

        body = " ".join(words[i:i + size])

        if len(body) > 60:
            chunks.append({
                "text": body,
                "source": source
            })

        i += size - overlap

    return chunks