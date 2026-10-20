# Personal Server & Activity Assistant

A local-first, privacy-focused activity intelligence platform combining automated multi-source telemetry collection, deterministic SQL analytics, and local LLM tool calling via Ollama on an RTX 3050 GPU.

---

## Quick Start

### 1. Run the Server
Using Python with the virtual environment activated:
```bash
python run.py
```

### 2. Available Endpoints
- **API Status**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Ollama Assistant Status**: [http://127.0.0.1:8000/api/v1/assistant/status](http://127.0.0.1:8000/api/v1/assistant/status)

---

## Code Walkthrough: Where to Start Reading

If you are exploring the codebase, follow this sequential reading order:

```
1. backend/app/core/config.py  ──>  2. backend/app/main.py  ──>  3. run.py  ──>  4. backend/.env.example
      (Settings & Env)                  (FastAPI Engine)             (Launcher)         (Overrides)
```

### 1. `backend/app/core/config.py` (Settings & Constants)
*The blueprint for the entire backend.*
- Uses Pydantic (`BaseSettings`) to manage and validate environment variables.
- Configures server host/port (`127.0.0.1:8000`), local Ollama runtime URL (`http://127.0.0.1:11434`), default database connection (`sqlite:///./personal_server.db` or PostgreSQL), and shared secret tokens for telemetry collectors (`X-Local-Token`).

### 2. `backend/app/main.py` (FastAPI Engine & Routes)
*The core HTTP server.*
- Sets up modern FastAPI lifespan events for clean startup and shutdown.
- Implements strict CORS restrictions (allowing localhost dashboards and `chrome-extension://*`).
- Defines status and health routes (`/`, `/health`).
- Includes an async status check for Ollama (`/api/v1/assistant/status`) that queries local models via HTTP.

### 3. `run.py` (Server Entry-Point)
*The single-command launcher.*
- Resolves paths so `backend/` is on the Python module path (`sys.path`).
- Launches `uvicorn` with hot-reload enabled (`reload=True`), automatically updating the server on code changes.

### 4. `backend/.env.example` (Configuration Overrides)
*Customization template.*
- Illustrates how to override database URLs, change default Ollama models, or update security tokens without altering source code.

---

## Project Structure

```
Personal_server/
├── docs/
│   └── architecture.md         # Full system architecture, ERDs, and tool-calling specs
├── design/
│   ├── index.html              # Embedded interactive Figma preview
│   └── README.md               # UI design notes and canvas links
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # FastAPI routers (events, analytics, assistant)
│   │   ├── core/               # Configuration, security, database settings
│   │   ├── db/                 # Database engine & session management
│   │   ├── models/             # Database tables (SQLModel / SQLAlchemy)
│   │   ├── schemas/            # Pydantic schemas for validation
│   │   ├── services/           # Deterministic analytics logic
│   │   └── tools/              # Ollama tool definitions & handlers
│   ├── requirements.txt        # Pinned Python dependencies
│   └── .env.example            # Environment variables template
├── collectors/
│   ├── desktop_watcher/        # Windows process & active window monitor
│   ├── chrome_extension/       # Browser activity tracker
│   └── spotify_sync/           # Spotify playback tracker
├── dashboard/                  # Web dashboard for analytics & assistant chat
└── run.py                      # One-click server launcher
```

---

## Documentation & Design
- **System Architecture**: [`docs/architecture.md`](docs/architecture.md)
- **UI Wireframes**: [`design/index.html`](design/index.html)
