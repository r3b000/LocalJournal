#!/usr/bin/env python3
"""
LocalJournal Desktop Launcher - cx_Freeze Compatible
"""

import sys
import subprocess
import time
import urllib.request
import os
from pathlib import Path


def get_project_root():
    if getattr(sys, "frozen", False):
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir:
            return Path(bundle_dir)
        return Path(sys.executable).parent
    return Path(__file__).parent


PROJECT_ROOT = get_project_root()
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config.constants import APP_NAME, APP_VERSION
except:
    APP_NAME, APP_VERSION = "LocalJournal", "1.0.0"

import webview


def log(msg):
    print(f"[LocalJournal] {msg}")


def find_python():
    """Find python.exe - bundled venv copy in frozen mode."""
    if not getattr(sys, "frozen", False):
        return sys.executable

    # Frozen: use the bundled venv python we shipped
    exe_dir = Path(sys.executable).parent
    bundled_python = exe_dir / "venv_python" / "python.exe"

    if bundled_python.exists():
        log(f"Found bundled Python: {bundled_python}")
        return str(bundled_python)

    log(f"[ERROR] Bundled python.exe not found at {bundled_python}")
    return None


def start_streamlit(port=8501):
    python_exe = find_python()
    if not python_exe:
        log("[ERROR] Cannot find python.exe to run Streamlit")
        return None

    app_path = str(PROJECT_ROOT / "app.py")

    # Set PYTHONPATH so bundled python finds site-packages
    env = os.environ.copy()
    if getattr(sys, "frozen", False):
        site_pkgs = str(PROJECT_ROOT / "venv_python" / "site-packages")
        env["PYTHONPATH"] = site_pkgs

    cmd = [
        python_exe,
        "-m", "streamlit", "run", app_path,
        "--server.headless=true",
        f"--server.port={port}",
        "--server.enableXsrfProtection=false",
        "--server.enableCORS=false",
        "--browser.gatherUsageStats=false",
    ]

    log(f"Python: {python_exe}")
    log(f"CMD:    {' '.join(cmd)}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    return proc



def wait_for_server(port, timeout=60):
    url = f"http://localhost:{port}"
    log(f"Waiting for {url}...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            log(f"[OK] Server ready!")
            return True
        except:
            pass
        time.sleep(0.5)

    return False


def main():
    print("=" * 60)
    print(f"{APP_NAME} v{APP_VERSION}")
    print(f"Mode: {'FROZEN' if getattr(sys, 'frozen', False) else 'DEVELOPMENT'}")
    print(f"Root: {PROJECT_ROOT}")
    print(f"Exe:  {sys.executable}")
    print("=" * 60)

    port = 8501

    streamlit_proc = start_streamlit(port)

    if streamlit_proc.poll() is not None:
        log(f"[ERROR] Streamlit exited immediately")
        return

    if not wait_for_server(port):
        log("[ERROR] Server timeout - reading Streamlit output:")
        out, _ = streamlit_proc.communicate(timeout=5)
        print(out.decode(errors="replace"))
        return

    log("Opening WebView window...")
    try:
        webview.create_window(
            f"{APP_NAME} v{APP_VERSION}",
            f"http://localhost:{port}",
            width=1400,
            height=900,
            resizable=True,
        )
        webview.start()
    except Exception as e:
        log(f"[ERROR] WebView: {e}")

    log("Closing Streamlit...")
    streamlit_proc.terminate()
    streamlit_proc.wait(timeout=5)
    log("Done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"[FATAL] {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter...")
        sys.exit(1)
