import ctypes
from datetime import datetime, timezone
import time
from typing import Dict, Optional
import httpx
import psutil
import win32gui
import win32process

from config import (
    HEARTBEAT_INTERVAL_SECONDS,
    IDLE_THRESHOLD_SECONDS,
    INGEST_URL,
    LOCAL_AUTH_TOKEN,
    REQUEST_TIMEOUT_SECONDS,
)


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def get_idle_seconds() -> float:
    """Returns number of seconds since last user keyboard or mouse input."""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        # dwTime is in milliseconds from system boot
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return max(0.0, millis / 1000.0)
    return 0.0


def get_active_window_info() -> Optional[Dict[str, str]]:
    """
    Safely captures active foreground window title and process name.
    Returns None if screen is locked or window handle is invalid.
    """
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd or hwnd == 0:
        return None

    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid <= 0:
            return None

        proc = psutil.Process(pid)
        process_name = proc.name()
        window_title = win32gui.GetWindowText(hwnd).strip()

        # Ignore empty system windows or task switcher
        if not process_name:
            return None

        return {
            "app_or_domain": process_name,
            "window_title": window_title or "Untitled",
            "pid": str(pid),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
        return None
    except Exception:
        return None


class DesktopWatcher:
    """Lightweight background watcher sending activity heartbeats to the Personal Server."""

    def __init__(self):
        self.headers = {
            "X-Local-Token": LOCAL_AUTH_TOKEN,
            "Content-Type": "application/json",
        }
        self.client = httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS)
        self.last_app: Optional[str] = None
        self.last_title: Optional[str] = None
        self.server_online: bool = True

    def send_heartbeat(self, app_info: Dict[str, str]) -> bool:
        """Sends telemetry payload to FastAPI ingestion endpoint."""
        payload = {
            "source": "desktop",
            "app_or_domain": app_info["app_or_domain"],
            "window_title": app_info["window_title"],
            "client_timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"pid": app_info.get("pid")},
        }

        try:
            resp = self.client.post(INGEST_URL, json=payload, headers=self.headers)
            if resp.status_code == 201:
                if not self.server_online:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Server reconnected!")
                    self.server_online = True
                data = resp.json()
                category = data.get("session_category", "unknown")
                return category
            elif resp.status_code == 401:
                print(f"[ERROR] 401 Unauthorized: Check LOCAL_AUTH_TOKEN in config.py")
                return False
            else:
                print(f"[WARN] Ingest returned HTTP {resp.status_code}: {resp.text}")
                return False
        except httpx.RequestError:
            if self.server_online:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Server unreachable at {INGEST_URL}. Waiting for server...")
                self.server_online = False
            return False

    def run(self):
        """Main monitoring loop."""
        print("=" * 60)
        print("   Personal Server — Windows Desktop Activity Collector")
        print(f"   Target: {INGEST_URL}")
        print(f"   Heartbeat: every {HEARTBEAT_INTERVAL_SECONDS}s | Idle threshold: {IDLE_THRESHOLD_SECONDS}s")
        print("=" * 60)
        print("Collector running... Press Ctrl+C to stop.\n")

        try:
            while True:
                idle_sec = get_idle_seconds()

                if idle_sec >= IDLE_THRESHOLD_SECONDS:
                    # User is away from desk; pause telemetry
                    time.sleep(HEARTBEAT_INTERVAL_SECONDS)
                    continue

                info = get_active_window_info()
                if info:
                    app = info["app_or_domain"]
                    title = info["window_title"]

                    category = self.send_heartbeat(info)

                    # Print to terminal on app change or heartbeats
                    if app != self.last_app or title != self.last_title:
                        tag = f"[{category.upper()}]" if category else "[OFFLINE]"
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {tag:14} {app:<18} -> {title[:45]}")
                        self.last_app = app
                        self.last_title = title

                time.sleep(HEARTBEAT_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\nCollector stopped gracefully.")
        finally:
            self.client.close()


if __name__ == "__main__":
    watcher = DesktopWatcher()
    watcher.run()

