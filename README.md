# Personal Server & Activity Assistant

A local-first, privacy-focused activity intelligence platform combining automated multi-source telemetry collection, deterministic SQL analytics, and local LLM tool calling via Ollama on an RTX 3050 GPU.

## Project Structure

```
Personal_server/
├── docs/
│   └── architecture.md         # Full system architecture and design specifications
├── backend/
│   └── app/
│       ├── api/v1/endpoints/   # FastAPI routers (events, analytics, assistant)
│       ├── core/               # Configuration, security, database settings
│       ├── db/                 # Database engine & session management
│       ├── models/             # Database tables (SQLModel / SQLAlchemy)
│       ├── schemas/            # Pydantic schemas for validation
│       ├── services/           # Deterministic analytics logic
│       └── tools/              # Ollama tool definitions & handlers
├── collectors/
│   ├── desktop_watcher/        # Windows process & active window monitor
│   ├── chrome_extension/       # Browser activity tracker
│   └── spotify_sync/           # Spotify playback tracker
└── dashboard/                  # Web dashboard for analytics & assistant chat
```

## Documentation
See [`docs/architecture.md`](docs/architecture.md) for full architecture details, endpoint specifications, and database schema.
