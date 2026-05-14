"""
健檢標案追蹤系統 — 桌面啟動器
啟動 Streamlit server，並用 pywebview 開獨立視窗，系統匣常駐。
"""
import os
import sys
import socket
import subprocess
import threading
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8501
_proc = None


def find_python():
    portable = os.path.join(APP_DIR, 'python-portable', 'python.exe')
    if os.path.exists(portable):
        return portable
    # 走到這裡代表使用系統 Python（開發環境用）
    return sys.executable


def wait_for_port(timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', PORT), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def start_streamlit():
    global _proc
    python = find_python()
    app_py = os.path.join(APP_DIR, 'app.py')
    os.makedirs(os.path.join(APP_DIR, 'data'), exist_ok=True)
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    _proc = subprocess.Popen(
        [python, '-m', 'streamlit', 'run', app_py,
         '--server.headless', 'true',
         '--server.port', str(PORT),
         '--server.address', '127.0.0.1'],
        cwd=APP_DIR,
        creationflags=flags,
    )


def cleanup():
    if _proc and _proc.poll() is None:
        _proc.terminate()


# ── 啟動 Streamlit ────────────────────────────────────────
start_streamlit()
ready = wait_for_port()
if not ready:
    import ctypes
    ctypes.windll.user32.MessageBoxW(0, '無法啟動服務，請確認 Python 環境正常。', '錯誤', 0x10)
    sys.exit(1)

# ── 載入 GUI 套件 ─────────────────────────────────────────
import webview
import pystray
from PIL import Image, ImageDraw

# ── 建立系統匣圖示 ────────────────────────────────────────
def _make_icon():
    img = Image.new('RGBA', (64, 64), (33, 150, 243, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([28,  8, 36, 56], fill='white')   # 十字縱線
    d.rectangle([ 8, 28, 56, 36], fill='white')   # 十字橫線
    return img


_window = None


def _show():
    if _window:
        _window.show()
        _window.restore()


def _quit(icon, _item):
    cleanup()
    icon.stop()
    if _window:
        _window.destroy()


_tray = pystray.Icon(
    '健檢標案追蹤',
    _make_icon(),
    '健檢標案追蹤系統',
    pystray.Menu(
        pystray.MenuItem('開啟視窗', _show, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('關閉程式', _quit),
    ),
)
threading.Thread(target=_tray.run, daemon=True).start()

# ── 建立 webview 視窗 ─────────────────────────────────────
_window = webview.create_window(
    '健檢標案追蹤系統',
    f'http://127.0.0.1:{PORT}',
    width=1280,
    height=860,
    min_size=(900, 600),
)


def _on_closing():
    _window.hide()
    return False   # 攔截關閉，改為隱藏到系統匣


_window.events.closing += _on_closing

webview.start()
cleanup()
