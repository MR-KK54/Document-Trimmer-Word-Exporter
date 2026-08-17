"""
Document Trimmer Pro - Desktop Application Launcher & Server Controller
Launches local server with auto-reload capability and native Desktop App window.
"""
import os
import sys
import time
import socket
import subprocess
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 5000
SERVER_URL = f"http://127.0.0.1:{PORT}"


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def start_server():
    """Start server.py if not already running."""
    if not is_port_in_use(PORT):
        print("[Desktop App] Starting local application server on port 5000...")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        cmd = [sys.executable, os.path.join(BASE_DIR, "server.py")]
        subprocess.Popen(cmd, cwd=BASE_DIR, env=env)
        for _ in range(30):
            if is_port_in_use(PORT):
                print("[Desktop App] Server is live and ready!")
                break
            time.sleep(0.5)
    else:
        print("[Desktop App] Server is already running on port 5000.")


def launch_desktop_window():
    """Open native desktop application window using Edge App mode or system browser."""
    print(f"[Desktop App] Opening desktop application window at {SERVER_URL}")
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge_exe = next((p for p in edge_paths if os.path.exists(p)), None)

    if edge_exe:
        cmd = [edge_exe, f"--app={SERVER_URL}", "--name=Document Trimmer Pro"]
        subprocess.Popen(cmd)
    else:
        webbrowser.open(SERVER_URL)


if __name__ == "__main__":
    start_server()
    launch_desktop_window()
