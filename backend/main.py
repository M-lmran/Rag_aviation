"""
AeroAssist – FastAPI Backend
Endpoints:
  POST /auth/register   → create account
  POST /auth/login      → get JWT token
  POST /upload          → admin: upload PDF manual
  DELETE /manual/{name} → admin: remove manual
  GET  /manuals         → list indexed manuals
  POST /ask             → engineer/admin: RAG query
  GET  /history         → engineer: own history / admin: all
  POST /feedback        → submit thumbs up/down
  GET  /stats           → admin: aggregate stats
"""
import shutil
import time
from pathlib import Path
from typing import Optional

from fastapi import (
    FastAPI, Depends, HTTPException, UploadFile, File,
    Form, status, BackgroundTasks
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.auth import (
    authenticate_user, create_access_token, create_user,
    get_current_user, require_admin, require_engineer,
    Token, UserIn, UserOut, seed_defaults,
)
from backend.config import UPLOAD_DIR, TOP_K
from backend import ingestion, vector_store, llm, database, cache

# ── app setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AeroAssist API",
    description="Aircraft Maintenance RAG Assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    seed_defaults()
    # warm up embedding model
    vector_store._get_model()


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    query: str
    top_k: int = TOP_K


class FeedbackRequest(BaseModel):
    query_id: str
    vote: str       # "up" | "down"


# ── Auth routes ───────────────────────────────────────────────────────────────
@app.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return Token(access_token=token, token_type="bearer")


@app.post("/auth/register", response_model=UserOut, tags=["Auth"])
async def register(user_in: UserIn, _: dict = Depends(require_admin)):
    """Admin-only: create new user accounts."""
    return create_user(user_in.username, user_in.password, user_in.role)


@app.get("/auth/me", response_model=UserOut, tags=["Auth"])
async def me(current_user: dict = Depends(get_current_user)):
    return UserOut(username=current_user["username"], role=current_user["role"])


# ── Upload routes ─────────────────────────────────────────────────────────────
@app.post("/upload", tags=["Manuals"])
async def upload_manual(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    _: dict = Depends(require_admin),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # process in background so upload returns immediately
    background_tasks.add_task(_index_pdf, dest, file.filename)
    return {"message": f"'{file.filename}' uploaded. Indexing in background…"}


def _index_pdf(pdf_path: Path, filename: str):
    t0 = time.time()
    manual_name = filename.replace(".pdf", "")
    chunks = ingestion.ingest_pdf(pdf_path, manual_name)
    vector_store.add_chunks(chunks)
    cache.clear_cache()    # invalidate old cached answers
    print(f"[Upload] Indexed '{manual_name}' – {len(chunks)} chunks in {time.time()-t0:.1f}s")


@app.delete("/manual/{manual_name}", tags=["Manuals"])
async def delete_manual(manual_name: str, _: dict = Depends(require_admin)):
    manuals = vector_store.list_manuals()
    if manual_name not in manuals:
        raise HTTPException(404, f"Manual '{manual_name}' not found in index")
    vector_store.remove_manual(manual_name)
    cache.clear_cache()
    # try to remove the file too
    pdf_path = UPLOAD_DIR / (manual_name + ".pdf")
    if pdf_path.exists():
        pdf_path.unlink()
    return {"message": f"Manual '{manual_name}' removed"}


@app.get("/manuals", tags=["Manuals"])
async def list_manuals(_: dict = Depends(get_current_user)):
    return {"manuals": vector_store.list_manuals(), "total_vectors": vector_store.vector_count()}


# ── Query route ───────────────────────────────────────────────────────────────
@app.post("/ask", tags=["Query"])
async def ask(req: AskRequest, current_user: dict = Depends(require_engineer)):
    query = req.query.strip()
    if not query:
        raise HTTPException(400, "Query cannot be empty")

    # check cache
    cached = cache.get_cached(query)
    if cached:
        answer, confidence, sources = cached
        query_id = database.save_query(
            current_user["username"], query, answer, confidence, sources
        )
        return {
            "query_id":   query_id,
            "answer":     answer,
            "confidence": confidence,
            "sources":    sources,
            "cached":     True,
        }

    t0 = time.time()
    sources = vector_store.search(query, k=req.top_k)
    answer, confidence = llm.generate_answer(query, sources)
    elapsed = time.time() - t0

    cache.set_cached(query, answer, confidence, sources)
    query_id = database.save_query(
        current_user["username"], query, answer, confidence, sources
    )

    return {
        "query_id":        query_id,
        "answer":          answer,
        "confidence":      round(confidence, 4),
        "sources":         [
            {
                "manual":  s.get("manual"),
                "page":    s.get("page"),
                "score":   round(s.get("score", 0), 4),
                "snippet": s.get("text", "")[:300],
            }
            for s in sources
        ],
        "elapsed_seconds": round(elapsed, 2),
        "cached":          False,
    }


# ── History route ─────────────────────────────────────────────────────────────
@app.get("/history", tags=["History"])
async def get_history(
    limit: int = 50,
    current_user: dict = Depends(require_engineer),
):
    if current_user["role"] == "admin":
        rows = database.get_history(limit=limit)
    else:
        rows = database.get_history(username=current_user["username"], limit=limit)
    return {"history": rows}


# ── Feedback route ────────────────────────────────────────────────────────────
@app.post("/feedback", tags=["Feedback"])
async def feedback(
    req: FeedbackRequest,
    current_user: dict = Depends(require_engineer),
):
    ok = database.save_feedback(req.query_id, current_user["username"], req.vote)
    if not ok:
        raise HTTPException(400, "Invalid vote. Use 'up' or 'down'")
    return {"message": "Feedback recorded"}


# ── Stats route ───────────────────────────────────────────────────────────────
@app.get("/stats", tags=["Admin"])
async def stats(_: dict = Depends(require_admin)):
    return database.get_stats()


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "vectors": vector_store.vector_count()}
