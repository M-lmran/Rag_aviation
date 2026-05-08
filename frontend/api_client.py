"""
API client helper for Streamlit frontend → FastAPI backend.
"""
import requests
from typing import Optional

API_BASE = "http://localhost:8000"


def _headers(token: Optional[str] = None) -> dict:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# ── Auth ──────────────────────────────────────────────────────────────────────
def login(username: str, password: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    return resp.json() if resp.ok else {"error": resp.json().get("detail", "Login failed")}


def me(token: str) -> dict:
    resp = requests.get(f"{API_BASE}/auth/me", headers=_headers(token), timeout=5)
    return resp.json() if resp.ok else {}


def register(token: str, username: str, password: str, role: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/auth/register",
        json={"username": username, "password": password, "role": role},
        headers=_headers(token),
        timeout=10,
    )
    return resp.json()


# ── Manuals ───────────────────────────────────────────────────────────────────
def list_manuals(token: str) -> dict:
    resp = requests.get(f"{API_BASE}/manuals", headers=_headers(token), timeout=10)
    return resp.json() if resp.ok else {"manuals": [], "total_vectors": 0}


def upload_manual(token: str, file_bytes: bytes, filename: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/upload",
        files={"file": (filename, file_bytes, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
        timeout=3600,  # 1 hour timeout for 1GB files
    )
    return resp.json()


def delete_manual(token: str, manual_name: str) -> dict:
    resp = requests.delete(
        f"{API_BASE}/manual/{manual_name}",
        headers=_headers(token),
        timeout=30,
    )
    return resp.json()


# ── Query ─────────────────────────────────────────────────────────────────────
def ask(token: str, query: str, top_k: int = 5) -> dict:
    resp = requests.post(
        f"{API_BASE}/ask",
        json={"query": query, "top_k": top_k},
        headers=_headers(token),
        timeout=60,
    )
    return resp.json() if resp.ok else {"error": resp.json().get("detail", "Query failed")}


# ── History ───────────────────────────────────────────────────────────────────
def get_history(token: str, limit: int = 50) -> list:
    resp = requests.get(
        f"{API_BASE}/history?limit={limit}",
        headers=_headers(token),
        timeout=10,
    )
    if resp.ok:
        return resp.json().get("history", [])
    return []


# ── Feedback ──────────────────────────────────────────────────────────────────
def send_feedback(token: str, query_id: str, vote: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/feedback",
        json={"query_id": query_id, "vote": vote},
        headers=_headers(token),
        timeout=10,
    )
    return resp.json()


# ── Stats ─────────────────────────────────────────────────────────────────────
def get_stats(token: str) -> dict:
    resp = requests.get(f"{API_BASE}/stats", headers=_headers(token), timeout=10)
    return resp.json() if resp.ok else {}


# ── Health ────────────────────────────────────────────────────────────────────
def health() -> bool:
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=3)
        return resp.ok
    except Exception:
        return False
