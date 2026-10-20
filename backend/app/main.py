from contextlib import asynccontextmanager
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: could initialize database tables or verify connections
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    yield
    # Shutdown cleanup
    print(f"[{datetime.now(timezone.utc).isoformat()}] Shutting down {settings.PROJECT_NAME}")


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
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health", tags=["General"])
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get(f"{settings.API_V1_STR}/assistant/status", tags=["Assistant"])
async def check_assistant_status():
    """Check connectivity to the local Ollama instance and query available models."""
    ollama_url = f"{settings.OLLAMA_BASE_URL}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(ollama_url)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "ollama_available": True,
                    "ollama_url": settings.OLLAMA_BASE_URL,
                    "default_model": settings.DEFAULT_MODEL,
                    "installed_models": models,
                }
            return {
                "ollama_available": False,
                "error": f"Ollama returned HTTP status {resp.status_code}",
                "ollama_url": settings.OLLAMA_BASE_URL,
            }
    except Exception as exc:
        return {
            "ollama_available": False,
            "error": str(exc),
            "ollama_url": settings.OLLAMA_BASE_URL,
            "hint": "Ensure Ollama is installed and running (`ollama serve`)",
        }
