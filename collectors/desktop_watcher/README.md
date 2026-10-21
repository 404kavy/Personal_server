# Windows Desktop Activity Collector

A lightweight, background telemetry collector for Windows that monitors the active foreground window and sends heartbeats to your local Personal Server.

---

## Features
- **Accurate Foreground Tracking**: Uses Windows API (`win32gui`, `win32process`) and `psutil` to track the focused process (`Code.exe`, `Valorant.exe`, etc.) and window title.
- **Hardware-Efficient**: Consumes < 0.1% CPU and ~15MB RAM.
- **Smart Idle Detection**: Pauses recording when no keyboard/mouse input is detected for 2+ minutes (`IDLE_THRESHOLD_SECONDS`).
- **Resilient Reconnection**: If the server is offline or restarting, the watcher automatically waits and reconnects when the server comes back up.

---

## How to Run

With your virtual environment activated:

```bash
python collectors/desktop_watcher/watcher.py
```

### Configuration (`config.py`)
- `INGEST_URL`: Target server endpoint (`http://127.0.0.1:8000/api/v1/events/ingest`).
- `LOCAL_AUTH_TOKEN`: Security token matching `backend/.env`.
- `HEARTBEAT_INTERVAL_SECONDS`: Default is `5` seconds.
- `IDLE_THRESHOLD_SECONDS`: Default is `120` seconds (2 minutes).

