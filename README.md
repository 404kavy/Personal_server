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
- Uses Pydantic (`BaseSettings` & `SettingsConfigDict`) to manage and validate environment variables.
- Utilizes `@lru_cache` on `get_settings()` so the environment variables and `.env` file are parsed only once into memory, returning the identical cached configuration instance across all requests for optimal performance.
- Configures server host/port (`127.0.0.1:8000`), local Ollama runtime URL (`http://127.0.0.1:11434`), default database connection (`sqlite:///./personal_server.db` or PostgreSQL), security keys, and shared secret tokens for telemetry collectors (`X-Local-Token`).

#### Configuration Template Format:
If you want to customize your own settings, this is the exact pattern used:

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "My FastAPI App"
    app_version: str = "1.0.0"
    debug: bool = False

    # API
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite:///./personal_server.db"

    # Security
    secret_key: str = "dev-secret-key-change-in-env"
    access_token_expire_minutes: int = 30

    # Environment configuration (.env file support)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton: loaded once, reused across requests."""
    return Settings()


settings = get_settings()
```

### 2. `backend/app/main.py` (FastAPI Engine & Routes)
*The core HTTP server.*
- Sets up modern FastAPI lifespan events for clean startup and shutdown.
- Implements strict CORS restrictions (allowing localhost dashboards and `chrome-extension://*`).
- Defines status and health routes (`/`, `/health`).
- Includes an async status check for Ollama (`/api/v1/assistant/status`) that queries local models via HTTP.

#### Application Template Format:
If you want to customize your `main.py` entry point, this is the standard pattern used:

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager: handles startup and shutdown logic."""
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    yield
    print(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Local-first Personal Activity Tracker and Ollama AI Assistant Engine",
    lifespan=lifespan,
)

# CORS configuration: Localhost and Chrome Extension origin support
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
async def root():
    """Root status endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health", tags=["General"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

### 3. `run.py` (Server Entry-Point)
*The single-command launcher.*
- Resolves paths so `backend/` is on the Python module path (`sys.path`).
- Launches `uvicorn` with hot-reload enabled (`reload=True`), automatically updating the server on code changes.

### 4. `backend/.env.example` (Configuration Overrides)
*Customization template.*
- Illustrates how to override database URLs, change default Ollama models, or update security tokens without altering source code.

---

## AI Assistant Deterministic Tools (`backend/app/tools/`)

To prevent the local LLM from hallucinating numbers or calculating durations incorrectly from thousands of raw log events, the LLM is given **strictly typed Python tools** rather than direct SQL database access. 

When you ask a question like *"How much time did I study yesterday?"*, the LLM selects the matching tool, FastAPI calculates the exact duration deterministically from the database, and the LLM formats the results into conversational English.

```python
# ==============================================================================
# IMPORTANT ANALYTICAL TOOL FUNCTIONS GIVEN TO OLLAMA
# ==============================================================================

def get_daily_summary(target_date: str) -> dict:
    """
    Retrieves the complete aggregate breakdown for a given day (YYYY-MM-DD).
    - Calculates total study duration, total gaming duration, and total distraction time.
    - Returns exact seconds, formatted hours/minutes, and top applications used.
    """
    pass

def get_study_duration(start_date: str, end_date: str) -> dict:
    """
    Queries study and productive coding sessions between two dates.
    - Filters events belonging to IDEs (e.g., Code.exe, Neovim) and educational domains.
    - Aggregates total focused work time without double-counting idle periods.
    """
    pass

def get_gaming_duration(start_date: str, end_date: str) -> dict:
    """
    Queries gaming activity duration between two dates.
    - Filters processes launched from Steam, Epic Games, or recognized DirectX/Vulkan game executables.
    - Computes continuous play sessions and peak active hours.
    """
    pass

def get_distraction_breakdown(target_date: str, limit: int = 5) -> list[dict]:
    """
    Identifies non-productive time sinks for a specific date.
    - Analyzes browser domain logs (e.g., YouTube, Reddit, Twitter/X) and social desktop apps.
    - Returns a ranked list of top distractions with individual durations and visit counts.
    """
    pass

def compare_activity_periods(period_a_start: str, period_a_end: str, period_b_start: str, period_b_end: str) -> dict:
    """
    Performs comparative trend analysis between two distinct timeframes (e.g., this week vs last week).
    - Computes percentage change in study vs gaming ratio.
    - Provides delta metrics (+/- hours) used by the LLM to generate actionable recommendations.
    """
    pass

def get_music_history(target_date: str) -> dict:
    """
    Retrieves recorded Spotify playback history for a target date.
    - Summarizes top tracks, artists, and total listening duration.
    - Allows the AI assistant to correlate background music genre with study focus blocks.
    """
    pass
```

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
