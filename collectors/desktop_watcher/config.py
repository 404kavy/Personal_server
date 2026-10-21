import os
from dotenv import load_dotenv

# Load root or local .env if available
load_dotenv()

SERVER_HOST = os.getenv("HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("PORT", 8000))
INGEST_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/api/v1/events/ingest"

# Pre-shared security token
LOCAL_AUTH_TOKEN = os.getenv("LOCAL_AUTH_TOKEN", "dev-secret-token-change-in-env")

# Heartbeat & Polling parameters
HEARTBEAT_INTERVAL_SECONDS = 5  # Seconds between active window checks
IDLE_THRESHOLD_SECONDS = 120  # 2 minutes of no input triggers idle state
REQUEST_TIMEOUT_SECONDS = 3.0  # HTTP request timeout
