"""
Query cache using diskcache to avoid re-running expensive LLM calls.
"""
import hashlib
import diskcache

from backend.config import CACHE_DIR

_cache = diskcache.Cache(str(CACHE_DIR))
_TTL   = 3600 * 24   # 24-hour TTL


def _key(query: str) -> str:
    return "q:" + hashlib.sha256(query.lower().strip().encode()).hexdigest()


def get_cached(query: str):
    """Returns cached (answer, confidence, sources) tuple or None."""
    return _cache.get(_key(query))


def set_cached(query: str, answer: str, confidence: float, sources: list):
    _cache.set(_key(query), (answer, confidence, sources), expire=_TTL)


def clear_cache():
    _cache.clear()
