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
        return None
    
    python_exe = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe") if sys.platform == "win32" and os.path.exists(os.path.join(BASE_DIR, ".venv")) else sys.executable
    server_script = os.path.join(BASE_DIR, "server.py")
    
    proc = subprocess.Popen([python_exe, server_script], cwd=BASE_DIR)
    
    for _ in range(30):
        if is_server_running():
            return proc
        time.sleep(0.5)
    return proc

def main():
    server_proc = start_server()
    
    # Priority 1: PyQt6 Native Application Window
    try:
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QIcon
        from PyQt6.QtWidgets import QApplication, QMainWindow
        from PyQt6.QtWebEngineWidgets import QWebEngineView

        app = QApplication(sys.argv)
        app.setApplicationName("Document Trimmer & Word Exporter Pro")
        
        window = QMainWindow()
        window.setWindowTitle("Microsoft Word & PDF Page Exporter Pro")
        window.resize(1280, 850)
        
        icon_path = os.path.join(BASE_DIR, "app_icon.ico")
        if os.path.exists(icon_path):
            window.setWindowIcon(QIcon(icon_path))
            app.setWindowIcon(QIcon(icon_path))

        view = QWebEngineView()
        view.setUrl(QUrl(SERVER_URL))
        window.setCentralWidget(view)
        window.show()
        
        ret = app.exec()
        if server_proc and server_proc.poll() is None:
            server_proc.terminate()
        sys.exit(ret)
        return
    except Exception as e:
        print(f"[Native App] PyQt6 fallback ({e}), checking webview...")

    # Priority 2: PyWebView Native Window
    try:
        import webview
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
        print(f"[Desktop App Error] Could not launch native window: {e}")
    finally:
        if server_proc and server_proc.poll() is None:
            server_proc.terminate()

if __name__ == "__main__":
    main()
