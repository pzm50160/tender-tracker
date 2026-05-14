"""
健檢標案追蹤系統 — 桌面啟動器
打包後為全自包 .exe，不需另裝 Python。
"""
import os
import sys
import socket
import subprocess
import threading
import time

# 若是 PyInstaller 打包版，APP_DIR 以 .exe 所在目錄為主
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

PORT = 8501
_streamlit_proc = None
_browser_proc   = None


# ── Streamlit 伺服器模式（打包版自呼叫用）────────────────────
if '--_streamlit-server' in sys.argv:
    app_py = os.path.join(APP_DIR, 'app.py')
    os.makedirs(os.path.join(APP_DIR, 'data'), exist_ok=True)
    sys.argv = [
        'streamlit', 'run', app_py,
        '--server.headless=true',
        f'--server.port={PORT}',
        '--server.address=127.0.0.1',
    ]
    from streamlit.web import cli as _stcli
    _stcli.main()
    sys.exit(0)


# ── 工具函式 ─────────────────────────────────────────────────

def find_browser():
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def wait_for_port(timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', PORT), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


# ── 啟動 Streamlit ────────────────────────────────────────────

def start_streamlit():
    global _streamlit_proc
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

    if getattr(sys, 'frozen', False):
        # 打包版：用自身 exe + 特殊旗標啟動 Streamlit 伺服器
        cmd = [sys.executable, '--_streamlit-server']
    else:
        # 開發版：用系統 Python 或 portable Python
        portable = os.path.join(APP_DIR, 'python-portable', 'python.exe')
        python = portable if os.path.exists(portable) else sys.executable
        app_py = os.path.join(APP_DIR, 'app.py')
        cmd = [python, '-m', 'streamlit', 'run', app_py,
               '--server.headless', 'true',
               '--server.port', str(PORT),
               '--server.address', '127.0.0.1']

    _streamlit_proc = subprocess.Popen(cmd, cwd=APP_DIR, creationflags=flags)


def open_window():
    global _browser_proc
    browser = find_browser()
    url = f'http://127.0.0.1:{PORT}'
    if browser:
        _browser_proc = subprocess.Popen([
            browser,
            f'--app={url}',
            '--window-size=1280,860',
            '--disable-extensions',
        ])
    else:
        import webbrowser
        webbrowser.open(url)


def cleanup():
    if _streamlit_proc and _streamlit_proc.poll() is None:
        _streamlit_proc.terminate()


# ── 主流程 ───────────────────────────────────────────────────

start_streamlit()

if not wait_for_port():
    import ctypes
    ctypes.windll.user32.MessageBoxW(
        0, '無法啟動服務，請確認程式完整性。', '錯誤', 0x10)
    sys.exit(1)

open_window()

# ── 系統匣 ───────────────────────────────────────────────────

import pystray
from PIL import Image, ImageDraw


def _make_icon():
    img = Image.new('RGBA', (64, 64), (33, 150, 243, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([28,  8, 36, 56], fill='white')
    d.rectangle([ 8, 28, 56, 36], fill='white')
    return img


def _on_open(icon, item):
    open_window()


def _on_quit(icon, item):
    cleanup()
    icon.stop()


tray = pystray.Icon(
    '健檢標案追蹤',
    _make_icon(),
    '健檢標案追蹤系統',
    pystray.Menu(
        pystray.MenuItem('開啟視窗', _on_open, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('關閉程式', _on_quit),
    ),
)

tray.run()
cleanup()
