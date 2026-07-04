"""
MedAgentX — Unified Launcher
=============================
Starts both the FastAPI backend (port 8000) and the Streamlit UI (port 8501)
with a single command.

Usage:
    python run_streamlit.py

What it does:
    1. Spawns the FastAPI server (run_server.py) as a background process
    2. Waits until the backend is healthy (GET /health)
    3. Launches Streamlit (medagentx/ui/streamlit_app.py) in the foreground
    4. On Ctrl+C, cleanly shuts down both processes

Ports (configurable via env vars):
    MEDAGENTX_API_PORT     — FastAPI port    (default: 8000)
    MEDAGENTX_UI_PORT      — Streamlit port  (default: 8501)
    MEDAGENTX_API_HOST     — FastAPI host    (default: 0.0.0.0)
"""

import os
import sys
import signal
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
ROOT_DIR       = Path(__file__).parent.resolve()
API_HOST       = os.environ.get("MEDAGENTX_API_HOST", "0.0.0.0")
API_PORT       = int(os.environ.get("MEDAGENTX_API_PORT", "8000"))
UI_PORT        = int(os.environ.get("MEDAGENTX_UI_PORT", "8501"))
HEALTH_URL     = f"http://localhost:{API_PORT}/health"
HEALTH_TIMEOUT = 30   # seconds to wait for backend to be ready
POLL_INTERVAL  = 0.5  # seconds between health check polls

STREAMLIT_APP  = ROOT_DIR / "medagentx" / "ui" / "streamlit_app.py"
SERVER_SCRIPT  = ROOT_DIR / "run_server.py"

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _print_banner():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║          MedAgentX v2.0  —  Unified Launcher        ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Backend  →  http://localhost:{API_PORT}               ║")
    print(f"║  API Docs →  http://localhost:{API_PORT}/docs           ║")
    print(f"║  Frontend →  http://localhost:{UI_PORT}               ║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║  Press Ctrl+C to stop both servers                  ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()


def _check_paths():
    """Validate that required files exist before launching."""
    missing = []
    if not SERVER_SCRIPT.exists():
        missing.append(str(SERVER_SCRIPT))
    if not STREAMLIT_APP.exists():
        missing.append(str(STREAMLIT_APP))
    if missing:
        print("ERROR: Required files not found:")
        for p in missing:
            print(f"  ✗  {p}")
        sys.exit(1)


def _is_backend_healthy() -> bool:
    """Return True if the FastAPI /health endpoint responds with 2xx."""
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2) as r:
            return r.status < 400
    except Exception:
        return False


def _wait_for_backend(timeout: int = HEALTH_TIMEOUT) -> bool:
    """
    Poll /health until the backend is ready or the timeout expires.
    Returns True if healthy, False if timed out.
    """
    print(f"⏳ Waiting for backend to be ready at {HEALTH_URL}", end="", flush=True)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _is_backend_healthy():
            print(" ✓")
            return True
        print(".", end="", flush=True)
        time.sleep(POLL_INTERVAL)
    print(" ✗ (timed out)")
    return False


def _start_backend() -> subprocess.Popen:
    """Start the FastAPI server as a background subprocess."""
    print(f"🚀 Starting FastAPI backend on port {API_PORT}...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        [sys.executable, str(SERVER_SCRIPT)],
        cwd=str(ROOT_DIR),
        env=env,
        # Let stdout/stderr pass through so the user sees backend logs
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return proc


def _start_streamlit() -> subprocess.Popen:
    """Start the Streamlit UI in the foreground."""
    print(f"🖥️  Starting Streamlit UI on port {UI_PORT}...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run",
            str(STREAMLIT_APP),
            f"--server.port={UI_PORT}",
            "--server.address=localhost",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
        ],
        cwd=str(ROOT_DIR),
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return proc


def _kill(proc: subprocess.Popen, name: str):
    """Gracefully terminate a subprocess."""
    if proc and proc.poll() is None:
        print(f"🛑 Stopping {name}...")
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        except Exception:
            pass


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    _check_paths()
    _print_banner()

    backend_proc  = None
    frontend_proc = None

    def _shutdown(signum=None, frame=None):
        print("\n\n⚠️  Shutdown signal received — stopping all services...")
        _kill(frontend_proc, "Streamlit UI")
        _kill(backend_proc,  "FastAPI backend")
        print("✅ All services stopped. Goodbye!")
        sys.exit(0)

    # Register Ctrl+C and SIGTERM handlers
    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # 1. Start the backend
    backend_proc = _start_backend()

    # 2. Wait until it's healthy (or time out)
    if not _wait_for_backend():
        print()
        print("⚠️  Backend did not become healthy in time.")
        print("   Streamlit will still start — it connects to the backend lazily.")
        print("   Check backend logs above for errors.")
        print()

    # 3. Start Streamlit
    frontend_proc = _start_streamlit()

    print()
    print("✅ Both services are running.")
    print(f"   → Open your browser at  http://localhost:{UI_PORT}")
    print(f"   → API docs at           http://localhost:{API_PORT}/docs")
    print("   → Press Ctrl+C to stop everything.")
    print()

    # 4. Keep running — monitor both processes
    try:
        while True:
            # If the backend dies unexpectedly, warn the user
            if backend_proc.poll() is not None:
                print(f"\n⚠️  Backend exited unexpectedly (code {backend_proc.returncode}).")
                print("   Streamlit is still running but may not function correctly.")
                backend_proc = None

            # If Streamlit exits, shut everything down
            if frontend_proc.poll() is not None:
                print(f"\nStreamlit exited (code {frontend_proc.returncode}).")
                _shutdown()
                break

            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown()


if __name__ == "__main__":
    main()
