import sys, os, time, subprocess, urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_URL = "http://127.0.0.1:5000"

def is_server_running():
    try:
        with urllib.request.urlopen(SERVER_URL + "/api/system/info", timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False

def start_server():
    if is_server_running():
        print("[Desktop App] Server is already running on http://127.0.0.1:5000")
        return None
    
    print("[Desktop App] Starting local application server...")
    python_exe = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe") if sys.platform == "win32" and os.path.exists(os.path.join(BASE_DIR, ".venv")) else sys.executable
    server_script = os.path.join(BASE_DIR, "server.py")
    
    proc = subprocess.Popen([python_exe, server_script], cwd=BASE_DIR)
    
    # Wait for server to start
    for _ in range(30):
        if is_server_running():
            print("[Desktop App] Server started successfully!")
            return proc
        time.sleep(0.5)
    return proc

def main():
    server_proc = start_server()
    
    try:
        import webview
        print("[Desktop App] Launching native Desktop Window via pywebview...")
        window = webview.create_window(
            title="Document Trimmer & Word Exporter Pro",
            url=SERVER_URL,
            width=1280,
            height=850,
            resizable=True,
            min_size=(900, 600)
        )
        webview.start()
    except Exception as e:
        print(f"[Desktop App] pywebview window fallback ({e}). Opening app window in browser...")
        import webbrowser
        webbrowser.open(SERVER_URL)
        print("[Desktop App] App opened. Press Ctrl+C in this window to stop the server.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    finally:
        if server_proc and server_proc.poll() is None:
            print("[Desktop App] Stopping local server...")
            server_proc.terminate()

if __name__ == "__main__":
    main()
