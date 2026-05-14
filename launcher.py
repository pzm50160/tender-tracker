"""
健檢標案追蹤系統 — 桌面啟動器
用 Edge/Chrome App 模式開獨立視窗（無網址列），系統匣常駐。
"""
import os
import sys
import socket
import subprocess
import threading
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8501
_streamlit_proc = None
_browser_proc = None


# ── 工具函式 ─────────────────────────────────────────────

def find_python():
    portable = os.path.join(APP_DIR, 'python-portable', 'python.exe')
    if os.path.exists(portable):
        return portable
    return sys.executable


def find_browser():
    """找 Edge 或 Chrome，優先 Edge（Windows 內建）"""
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


def wait_for_port(timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', PORT), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


# ── 啟動 Streamlit ────────────────────────────────────────

def start_streamlit():
    global _streamlit_proc
    python = find_python()
    app_py = os.path.join(APP_DIR, 'app.py')
    os.makedirs(os.path.join(APP_DIR, 'data'), exist_ok=True)
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    _streamlit_proc = subprocess.Popen(
        [python, '-m', 'streamlit', 'run', app_py,
         '--server.headless', 'true',
         '--server.port', str(PORT),
         '--server.address', '127.0.0.1'],
        cwd=APP_DIR,
        creationflags=flags,
    )


def open_window():
    """用 App 模式開獨立視窗（沒有瀏覽器 UI）"""
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
        # 找不到 Edge/Chrome，退回系統預設瀏覽器
        import webbrowser
        webbrowser.open(url)


def cleanup():
    if _streamlit_proc and _streamlit_proc.poll() is None:
        _streamlit_proc.terminate()


# ── 主流程 ───────────────────────────────────────────────

start_streamlit()

if not wait_for_port():
    import ctypes
    ctypes.windll.user32.MessageBoxW(
        0, '無法啟動服務，請確認 Python 環境正常。', '錯誤', 0x10)
    sys.exit(1)

open_window()

# ── 系統匣 ───────────────────────────────────────────────

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

tray.run()   # 阻塞直到使用者點「關閉程式」
cleanup()
