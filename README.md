# EmployeeMate - RAG + Agentic Employee Assistant

EmployeeMate is a full-stack AI assistant for employee policy questions and basic HR actions. It combines a Retrieval-Augmented Generation pipeline with an agentic workflow that can choose between company document search, employee profile lookup, and leave application tools.

---

## Bonus Features Reference Guide

The codebase includes all 10 bonus features and security enhancements:

| # | Feature | Location in Code | How to Test |
|---|---|---|---|
| **1** | **Streaming Responses** | `app/rag.py` (`RAGPipeline.stream_query`), `app/main.py` (`chat_stream`), `frontend/src/services/api.js` (`sendChatMessageStream`) | `POST /chat/stream` with curl or submit query in UI to watch real-time token streaming. |
| **2** | **Conversation Memory** | `app/memory.py` (`ConversationMemory`), `app/conversation.py` (`rewrite_followup`) | `pytest tests/test_backend.py -k test_memory_isolation` |
| **3** | **Metadata Filtering** | `app/rag.py` (`derive_category_from_filename`), `app/agents/knowledge_agent.py` (`_infer_category`) | `pytest tests/test_backend.py -k test_category_derivation` |
| **4** | **Reranking** | `app/rag.py` (`TwoStageReranker.rerank_with_scores`) | `pytest tests/test_backend.py -k test_offline_answer_synthesis` |
| **5** | **Retrieval Confidence Threshold** | `app/rag.py` (`search_company_documents` cutoff `MIN_RERANK_SCORE`), `app/config.py` | `pytest tests/test_backend.py -k test_confidence_threshold_rejection` |
| **6** | **Docker Setup** | `Dockerfile`, `docker-compose.yml`, `.dockerignore` | `docker-compose up --build` |
| **7** | **Unit Tests** | `tests/conftest.py`, `tests/test_backend.py` | `python -m pytest tests/test_backend.py -q` |
| **8** | **Logging & Observability** | `app/logging_config.py` (`setup_logging`), `app/main.py` (`logging_request_id_middleware`), `/metrics` | `curl http://localhost:8000/metrics` or check server JSON stdout logs. |
| **9** | **Prompt Injection Protection** | `app/security.py` (`detect_prompt_injection`, `sanitize_history`, `wrap_context`, `verify_canary`), `app/agents/orchestrator.py` | `pytest tests/test_backend.py -k test_prompt_injection_detection` |
| **10** | **Basic Authorization (RBAC & JWT)** | `app/auth.py` (`Principal`, `get_current_user`, `require_hr`, `enforce_prompt_scope`), `app/main.py` (`/auth/login`, `/employees`) | `pytest tests/test_backend.py -k test_auth_matrix` |

---

## Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic V2, PyJWT
- **RAG Framework**: LangChain, ChromaDB
- **Embeddings**: Hugging Face `all-MiniLM-L6-v2` (with `DeterministicHashEmbeddings` fallback)
- **LLM Provider**: Configurable switch supporting Google Gemini (`gemini-3.6-flash`), OpenAI (`gpt-4o-mini`), LM Studio / Ollama (`gemma`), and offline answer synthesis fallback.
- **Reranking**: Sentence Transformers `CrossEncoder`
- **Testing**: `pytest`, FastAPI `TestClient`

---

## Setup & Running Locally

### 1. Environment Setup

Create a `.env` file from `.env.example`:

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-3.6-flash

JWT_SECRET=your_jwt_secret_key_here
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173
DEMO_EMPLOYEE_PASSWORD=emp123
DEMO_HR_PASSWORD=hr123
LOG_LEVEL=INFO
```

### 2. Backend Startup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Startup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to access the chat UI and login screen.

---

## Docker Setup & LLM Provider Switching

### Build & Run Full Stack Container

```bash
docker-compose up --build
```

### Run with Local Ollama Container (Compose Profile)

To run a containerized Ollama instance alongside the app:

```bash
docker-compose --profile local-llm up --build
```

### Switching LLM Providers

Change the `LLM_PROVIDER` environment variable in `.env` or `docker-compose.yml`:
- `LLM_PROVIDER=gemini` (uses `GOOGLE_API_KEY` and `GEMINI_MODEL`)
- `LLM_PROVIDER=openai` (uses `OPENAI_API_KEY` and `OPENAI_MODEL`)
- `LLM_PROVIDER=ollama` or `lmstudio` (uses `LMSTUDIO_BASE_URL` e.g. `http://host.docker.internal:11434/v1` and `LMSTUDIO_MODEL`)
- `LLM_PROVIDER=none` (forces offline document synthesis fallback)

---

## Testing

Run all unit tests offline with `pytest`:

```bash
python -m pytest -q
```

---

## Authentication & API Usage

### 1. Login to acquire JWT Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"emp_id": "EMP001", "password": "emp123"}'
```

### 2. Health Check

```bash
curl http://localhost:8000/health
```

### 3. Chat Endpoint (Authenticated)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -d '{"prompt": "What is the WFH policy?", "emp_id": "EMP001"}'
```

### 4. Streaming SSE Chat Endpoint

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -d '{"prompt": "What is the WFH policy?", "emp_id": "EMP001"}'
```
