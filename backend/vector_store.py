"""
Vector store: FAISS index with SentenceTransformer embeddings.
Supports multiple manuals – all chunks live in a single FAISS index
with metadata stored in a parallel JSON-backed list.
"""
import json
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Any, Optional

from sentence_transformers import SentenceTransformer

from backend.config import (
    FAISS_DIR, EMBEDDING_MODEL, EMBEDDING_DIM, TOP_K
)

_INDEX_FILE = FAISS_DIR / "index.faiss"
_META_FILE  = FAISS_DIR / "metadata.json"

# ── singleton state ───────────────────────────────────────────────────────────
_model: Optional[SentenceTransformer] = None
_index: Optional[faiss.IndexFlatIP] = None   # inner-product (cosine after norm)
_metadata: List[Dict[str, Any]] = []


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"[VectorStore] Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_index() -> faiss.IndexFlatIP:
    global _index, _metadata
    if _index is None:
        if _INDEX_FILE.exists() and _META_FILE.exists():
            _index = faiss.read_index(str(_INDEX_FILE))
            with open(_META_FILE, "r") as f:
                _metadata = json.load(f)
            print(f"[VectorStore] Loaded index with {_index.ntotal} vectors")
        else:
            _index = faiss.IndexFlatIP(EMBEDDING_DIM)
            _metadata = []
            print("[VectorStore] Created new FAISS index")
    return _index


def _save():
    faiss.write_index(_index, str(_INDEX_FILE))
    with open(_META_FILE, "w") as f:
        json.dump(_metadata, f)


def embed(texts: List[str]) -> np.ndarray:
    """Embed a list of texts; returns normalized float32 array."""
    model = _get_model()
    vecs = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    # L2-normalize for cosine similarity via inner-product
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return (vecs / norms).astype("float32")


def add_chunks(chunks: List[Dict[str, Any]]):
    """Embed chunks and add to FAISS index."""
    index = _get_index()
    texts = [c["text"] for c in chunks]
    vecs  = embed(texts)
    index.add(vecs)
    _metadata.extend(chunks)
    _save()
    print(f"[VectorStore] Added {len(chunks)} chunks. Total: {index.ntotal}")


def search(query: str, k: int = TOP_K) -> List[Dict[str, Any]]:
    """
    Semantic search. Returns list of result dicts:
    {chunk metadata} + 'score' (0-1 cosine similarity)
    """
    index = _get_index()
    if index.ntotal == 0:
        return []
    q_vec = embed([query])
    scores, indices = index.search(q_vec, min(k, index.ntotal))
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        entry = dict(_metadata[idx])
        entry["score"] = float(score)          # already cosine (0-1)
        results.append(entry)
    return results


def list_manuals() -> List[str]:
    """Return distinct manual names currently indexed."""
    _get_index()
    return sorted(set(m.get("manual", "") for m in _metadata))


def remove_manual(manual_name: str):
    """
    Remove all chunks belonging to a manual and rebuild the index.
    (FAISS does not support deletion natively.)
    """
    global _index, _metadata
    _get_index()
    kept = [m for m in _metadata if m.get("manual") != manual_name]
    # rebuild
    _index = faiss.IndexFlatIP(EMBEDDING_DIM)
    _metadata = []
    if kept:
        texts = [c["text"] for c in kept]
        vecs  = embed(texts)
        _index.add(vecs)
        _metadata = kept
    _save()
    print(f"[VectorStore] Removed manual '{manual_name}'. Remaining: {_index.ntotal}")


def vector_count() -> int:
    return _get_index().ntotal
