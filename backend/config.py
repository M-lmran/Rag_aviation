"""
Configuration and settings for AeroAssist backend.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "manuals"
FAISS_DIR = DATA_DIR / "faiss_index"
DB_DIR = DATA_DIR / "db"
CACHE_DIR = DATA_DIR / "cache"

for d in [UPLOAD_DIR, FAISS_DIR, DB_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# --- LLM ---
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-flash-latest"
MAX_TOKENS: int = 2048

# --- Embeddings ---
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
EMBEDDING_DIM: int = 384

# --- Chunking ---
CHUNK_SIZE: int = 512          # characters
CHUNK_OVERLAP: int = 64        # characters

# --- Retrieval ---
TOP_K: int = 5

# --- Auth ---
SECRET_KEY: str = os.getenv("SECRET_KEY", "aeroassist-super-secret-key")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# --- System Prompt ---
SYSTEM_PROMPT = (
    "You are a helpful and expert aircraft maintenance assistant. "
    "Provide a detailed, comprehensive, and well-structured answer based ONLY on the provided context from the maintenance manuals. "
    "Do not give just a single line; explain the procedures, specifications, and reasoning clearly, just as a sophisticated LLM would. "
    "If applicable, use bullet points or numbered lists. "
    "At the very end of your response, explicitly list the references you used based on the source metadata (Manual and Page) provided in the context. "
    "If the answer is not found in the provided context, respond with: 'Not found in manual'. "
    "Always maintain a precise, professional, and safety-conscious tone."
)
