"""
LLM wrapper: Google Gemini Chat Completion with retrieved context injection.
Falls back gracefully when no API key is set (returns a demo answer).
"""
from typing import List, Dict, Any, Tuple

from backend.config import GEMINI_API_KEY, GEMINI_MODEL, MAX_TOKENS, SYSTEM_PROMPT


def build_context(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks into a readable context block."""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[Source {i} | Manual: {c.get('manual','?')} | Page {c.get('page','?')}]\n"
            f"{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def generate_answer(query: str, chunks: List[Dict[str, Any]]) -> Tuple[str, float]:
    """
    Generate an answer from the LLM using retrieved context.
    Returns (answer, confidence) where confidence is avg cosine similarity (0-1).
    """
    if not chunks:
        return "No relevant information found in the uploaded manuals.", 0.0

    confidence = float(sum(c["score"] for c in chunks) / len(chunks))

    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        # ── Demo mode: return the best matching snippet ────────────────────────
        top = chunks[0]
        snippet = top["text"][:500].replace("\n", " ")
        answer = (
            f"[DEMO MODE – add GEMINI_API_KEY to .env for full AI answers]\n\n"
            f"Most relevant section found in **{top.get('manual','?')}** "
            f"(Page {top.get('page','?')}):\n\n\"{snippet}...\""
        )
        return answer, confidence

    # ── Live Gemini call ──────────────────────────────────────────────────────
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        
        context = build_context(chunks)
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Context from maintenance manuals:\n\n{context}\n\n"
            f"Question: {query}"
        )
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=MAX_TOKENS,
                temperature=0.1,
            )
        )
        return response.text.strip(), confidence
    except Exception as e:
        return f"LLM error: {e}", confidence
