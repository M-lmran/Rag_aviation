# ✈️ AeroAssist – Aircraft Maintenance Assistant

An AI-powered RAG (Retrieval-Augmented Generation) application for aircraft maintenance manuals.

---

## 📁 Project Structure

```
rag_aviation/
├── backend/
│   ├── main.py          # FastAPI app & all API endpoints
│   ├── config.py        # Settings, paths, env vars
│   ├── auth.py          # JWT authentication & role-based access
│   ├── ingestion.py     # PDF extraction & chunking
│   ├── vector_store.py  # FAISS index + SentenceTransformer embeddings
│   ├── llm.py           # OpenAI / demo-mode answer generation
│   ├── database.py      # TinyDB history & feedback storage
│   └── cache.py         # Disk-based query caching
├── frontend/
│   ├── app.py           # Streamlit UI
│   └── api_client.py    # HTTP client for backend
├── data/                # Auto-created at runtime
│   ├── manuals/         # Uploaded PDFs
│   ├── faiss_index/     # FAISS index + metadata
│   ├── db/              # TinyDB JSON files
│   └── cache/           # Query cache
├── run_backend.py       # Start FastAPI server
├── run_frontend.py      # Start Streamlit UI
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (optional – demo mode works without it)
```

### 3. Start the Backend (Terminal 1)

```bash
python run_backend.py
# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 4. Start the Frontend (Terminal 2)

```bash
python run_frontend.py
# UI available at http://localhost:8501
```

---

## 🔑 Default Credentials

| Role       | Username   | Password   | Permissions                        |
|------------|-----------|------------|-------------------------------------|
| Admin      | `admin`   | `admin123` | Upload manuals, ask queries, manage users |
| Engineer   | `engineer`| `eng123`   | Ask queries, view own history       |

---

## 🧠 RAG Pipeline

```
PDF Upload → Text Extraction (PyMuPDF) → Chunking (512 chars, 64 overlap)
    → Embeddings (all-MiniLM-L6-v2) → FAISS IndexFlatIP (cosine similarity)
    → Top-K Retrieval → Context injection → OpenAI GPT-3.5 → Answer
```

## 🌐 API Endpoints

| Method | Endpoint             | Auth     | Description              |
|--------|----------------------|----------|--------------------------|
| POST   | `/auth/login`        | Public   | Get JWT token            |
| POST   | `/auth/register`     | Admin    | Create new user          |
| GET    | `/auth/me`           | Any      | Current user info        |
| POST   | `/upload`            | Admin    | Upload PDF manual        |
| GET    | `/manuals`           | Any      | List indexed manuals     |
| DELETE | `/manual/{name}`     | Admin    | Remove a manual          |
| POST   | `/ask`               | Engineer | RAG query                |
| GET    | `/history`           | Engineer | Query history            |
| POST   | `/feedback`          | Engineer | Thumbs up/down           |
| GET    | `/stats`             | Admin    | Aggregate statistics     |
| GET    | `/health`            | Public   | Health check             |

Full Swagger docs: `http://localhost:8000/docs`

---

## ⚙️ Configuration

Edit `backend/config.py` or set via `.env`:

| Variable                  | Default           | Description              |
|---------------------------|-------------------|--------------------------|
| `OPENAI_API_KEY`          | *(empty)*         | OpenAI key (optional)    |
| `OPENAI_MODEL`            | `gpt-3.5-turbo`   | LLM model                |
| `EMBEDDING_MODEL`         | `all-MiniLM-L6-v2`| SentenceTransformer model|
| `CHUNK_SIZE`              | `512`             | Chars per chunk          |
| `CHUNK_OVERLAP`           | `64`              | Overlap between chunks   |
| `TOP_K`                   | `5`               | Retrieved chunks per query|

---

## 🔧 Tech Stack

| Layer        | Technology                        |
|--------------|-----------------------------------|
| Frontend     | Streamlit                         |
| Backend      | FastAPI + Uvicorn                 |
| Embeddings   | SentenceTransformers (MiniLM)     |
| Vector DB    | FAISS (IndexFlatIP – cosine)      |
| LLM          | OpenAI GPT-3.5 (or demo mode)     |
| Auth         | JWT (python-jose) + bcrypt        |
| Storage      | TinyDB (JSON)                     |
| Cache        | diskcache (disk-backed)           |
| PDF Parsing  | PyMuPDF (fitz)                    |
