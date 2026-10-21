from contextlib import asynccontextmanager
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import Base, engine
import app.models  # Ensures all models are registered on Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and connections
    Base.metadata.create_all(bind=engine)
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    yield
    # Shutdown cleanup
    print(f"[{datetime.now(timezone.utc).isoformat()}] Shutting down {settings.PROJECT_NAME}")
# above block of code line by line explanation:
""" this code defines an asynchronous context manager called `lifespan` for a FastAPI application. It is used to manage the startup and shutdown events of the application."""
""" the startup section prints a message indicating that the application is starting, along with the current UTC timestamp, project name, and version. This is useful for logging purposes."""
"""this is how output of this code looks like:
[2024-06-15T12:34:56.789Z] Starting Personal
 Activity Server & Assistant v0.1.0
"""
""" the `yield` statement allows the application to run while the context manager is active. After the application is done running, the code after `yield` executes."""

# representation of settings.PROJECT_NAME means that the title of the FastAPI application 
# is set to the value of the PROJECT_NAME attribute from the settings object, which is 
# "Personal Activity Server & Assistant". This title is used in the automatically generated API documentation and provides a clear identification of the application.
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
#same for this block of code line by line explanation:
""" this code adds Cross-Origin Resource Sharing (CORS) middleware to the FastAPI application."""
""" it allows requests from specific origins defined in `settings.CORS_ORIGINS`, which includes localhost and other specified URLs."""
""" it also allows requests from any Chrome extension by using a regular expression to match the origin."""
""" the middleware is configured to allow credentials, all HTTP methods, and all headers, enabling flexible communication between the frontend and backend of the application."""
#do this is basically for website telementtry and analytics, to allow the frontend to communicate with the backend without being blocked by the browser's same-origin policy.


# Mount API v1 Routers (Telemetry events, analytics, assistant)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["General"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
"""
this is get function to handle the root endpoint ("/") of the FastAPI application. When a GET request is made to this endpoint, it returns a JSON response containing the project name, version, status (online), URL for API documentation ("/docs"), and the current UTC timestamp. This provides a simple way to check the application's basic information and status.
"""
#the tags = ["General"] is used to categorize this endpoint in the automatically generated API documentation, making it easier for developers to find and understand the purpose of this endpoint.

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
        async with httpx.AsyncClient(timeout=3.0) as client: #httpx.AsyncClient is an asynchronous HTTP client provided by the httpx library. It allows you to make HTTP requests in an asynchronous manner, which is useful for non-blocking I/O operations in applications that require high concurrency or responsiveness.
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

