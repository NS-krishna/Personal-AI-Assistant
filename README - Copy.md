# 🤖 Personal AI Agent

A multi-agent personal AI assistant with Gmail, Google Calendar, RAG, and voice support — powered by Groq + Ollama.

---

## Architecture

```
User ──→ React Frontend ──→ FastAPI Backend
                                  │
                   ┌──────────────┼──────────────┐
                   ▼              ▼              ▼
              Planner        Executor        Critic
            (plan steps)   (run tools)   (evaluate quality)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
           Gmail          Calendar       Doc Summarizer
                              │
                        ┌─────┼─────┐
                        ▼           ▼
                    Groq API     Ollama
                   (cloud/fast)  (local/private)
                              │
                        ┌─────┼─────┐
                        ▼           ▼
                   Episodic     Semantic
                   Memory       Memory
                   (ChromaDB)   (ChromaDB)
```

## Features

| Feature | Status |
|---------|--------|
| Multi-agent pipeline (Planner → Executor → Critic) | 🔲 Scaffold |
| Dual LLM routing (Groq + Ollama) | 🔲 Scaffold |
| Gmail: read, search, draft, send | 🔲 Scaffold |
| Google Calendar: list, create, free slots | 🔲 Scaffold |
| RAG: PDF/DOCX → ChromaDB → Q&A | 🔲 Scaffold |
| Two-layer memory (episodic + semantic) | 🔲 Scaffold |
| Voice I/O (Whisper + Web Speech API) | 🔲 Scaffold |
| Streaming responses (SSE) | 🔲 Scaffold |
| Evaluation dashboard | 🔲 Scaffold |
| React frontend (Tailwind) | 🔲 Scaffold |

## Tech Stack

- **LLMs**: Groq API (llama3-70b) + Ollama (qwen2.5-coder)
- **Agent Framework**: LangChain
- **Memory**: ChromaDB (persistent, local)
- **Embeddings**: sentence-transformers (local)
- **Backend**: FastAPI + Uvicorn
- **Frontend**: React + Vite + Tailwind CSS
- **Voice**: OpenAI Whisper (local) + Web Speech API
- **Google**: google-api-python-client, google-auth-oauthlib

## Project Structure

```
personal-ai-app/
├── agent/               # Multi-agent system
│   ├── planner.py       # Breaks queries into tool steps
│   ├── executor.py      # Runs tools, collects results
│   └── critic.py        # Evaluates quality, triggers retries
├── tools/               # External integrations
│   ├── auth.py          # Google OAuth 2.0
│   ├── gmail_reader_tool.py
│   ├── calendar_tool.py
│   └── document_summarizer_tool.py
├── memory/              # Two-layer memory
│   ├── episodic_memory.py
│   ├── semantic_memory.py
│   └── memory_manager.py
├── models/              # LLM providers
│   ├── groq_client.py
│   ├── ollama_client.py
│   └── llm_router.py
├── voice/               # Voice I/O
│   ├── stt.py
│   └── tts.py
├── api/                 # FastAPI backend
│   ├── routes.py
│   └── streaming.py
├── evaluation/
│   └── evaluator.py
├── frontend/            # React + Tailwind
│   └── src/components/
├── main.py              # Entry point
├── config.py            # Environment config
└── requirements.txt
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama installed with `qwen2.5-coder` pulled
- Google OAuth `credentials.json` in project root
- Groq API key in `.env`

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
# → API at http://localhost:8000
# → Docs at http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# → UI at http://localhost:5173
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message, get response |
| POST | `/api/chat/stream` | Streaming response (SSE) |
| POST | `/api/upload` | Upload document for RAG |
| GET | `/api/emails` | Fetch recent emails |
| GET | `/api/calendar` | List upcoming events |
| POST | `/api/calendar` | Create calendar event |
| POST | `/api/voice/stt` | Transcribe audio |
| GET | `/api/metrics` | Evaluation metrics |
| GET | `/api/health` | Service health check |

## Environment Variables

Copy `.env` and fill in your values:

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key |
| `OLLAMA_MODEL` | Local model name (default: `qwen2.5-coder`) |
| `GROQ_MODEL` | Cloud model name (default: `llama3-70b-8192`) |
| `WHISPER_MODEL` | Whisper model size (default: `base`) |

## License

MIT
