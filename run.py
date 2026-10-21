"""Entry-point script to start the Personal Server."""
import os
import sys
import uvicorn

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings

if __name__ == "__main__":
    print(f"Starting server on http://{settings.HOST}:{settings.PORT}")
    print(f"Interactive Swagger Docs available at http://{settings.HOST}:{settings.PORT}/docs")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )

