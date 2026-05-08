"""
Query history and feedback persistence using TinyDB.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from tinydb import TinyDB, Query

from backend.config import DB_DIR

_db      = TinyDB(DB_DIR / "history.json")
_feedback_db = TinyDB(DB_DIR / "feedback.json")
_HistQ   = Query()


# ── History ───────────────────────────────────────────────────────────────────
def save_query(
    username: str,
    query: str,
    answer: str,
    confidence: float,
    sources: List[Dict[str, Any]],
) -> str:
    """Persist a Q&A pair. Returns the generated query_id."""
    query_id = str(uuid.uuid4())
    _db.insert({
        "query_id":  query_id,
        "username":  username,
        "query":     query,
        "answer":    answer,
        "confidence": round(confidence, 4),
        "sources":   [
            {
                "manual": s.get("manual"),
                "page":   s.get("page"),
                "score":  round(s.get("score", 0), 4),
                "snippet": s.get("text", "")[:200],
            }
            for s in sources
        ],
        "timestamp": datetime.utcnow().isoformat(),
        "feedback":  None,
    })
    return query_id


def get_history(username: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """Return query history, optionally filtered by user."""
    if username:
        rows = _db.search(_HistQ.username == username)
    else:
        rows = _db.all()
    # sort by timestamp desc
    rows = sorted(rows, key=lambda x: x.get("timestamp", ""), reverse=True)
    return rows[:limit]


def get_query_by_id(query_id: str) -> Optional[Dict]:
    result = _db.search(_HistQ.query_id == query_id)
    return result[0] if result else None


# ── Feedback ──────────────────────────────────────────────────────────────────
def save_feedback(query_id: str, username: str, vote: str) -> bool:
    """
    vote: 'up' or 'down'
    Also updates the history record's feedback field.
    """
    if vote not in ("up", "down"):
        return False
    _feedback_db.insert({
        "query_id":  query_id,
        "username":  username,
        "vote":      vote,
        "timestamp": datetime.utcnow().isoformat(),
    })
    _db.update({"feedback": vote}, _HistQ.query_id == query_id)
    return True


def get_stats() -> Dict[str, Any]:
    """Return aggregate statistics."""
    all_rows = _db.all()
    total = len(all_rows)
    thumbs_up   = sum(1 for r in all_rows if r.get("feedback") == "up")
    thumbs_down = sum(1 for r in all_rows if r.get("feedback") == "down")
    avg_confidence = (
        sum(r.get("confidence", 0) for r in all_rows) / total if total else 0
    )
    return {
        "total_queries": total,
        "thumbs_up":     thumbs_up,
        "thumbs_down":   thumbs_down,
        "avg_confidence": round(avg_confidence, 3),
    }
