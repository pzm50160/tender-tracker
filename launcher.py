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

# 啟動日誌（方便除錯）
import datetime
_LOG = os.path.join(APP_DIR, 'launcher.log')
def _log(msg):
    ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:12]
    line = f"[{ts}] {msg}\n"
    try:
        with open(_LOG, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass

PORT = 8501
_streamlit_proc = None
_browser_proc   = None


# ── Streamlit 伺服器模式（打包版自呼叫用）────────────────────
if '--_streamlit-server' in sys.argv:
    _log(f"[server] 啟動 streamlit server, APP_DIR={APP_DIR}")
    app_py = os.path.join(APP_DIR, 'app.py')
    os.makedirs(os.path.join(APP_DIR, 'data'), exist_ok=True)

    # PyInstaller bundle 裡 streamlit 誤判為開發模式（__file__ 不含 site-packages）
    # 在 import streamlit 前 patch env_util.is_pex() 讓它回傳 True，
    # 使 developmentMode 預設值變為 False
    import streamlit.env_util as _env_util
    _env_util.is_pex = lambda: True

    sys.argv = ['streamlit', 'run', app_py,
                '--server.headless=true',
                '--server.address=127.0.0.1',
                f'--server.port={PORT}',
                '--server.fileWatcherType=none',
                '--server.runOnSave=false']
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
               '--server.address', '127.0.0.1',
               '--server.fileWatcherType=none',
               '--server.runOnSave=false']

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
        try:
            subprocess.call(
                ['taskkill', '/F', '/T', '/PID', str(_streamlit_proc.pid)],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            _streamlit_proc.terminate()


# ── 主流程 ───────────────────────────────────────────────────

_log(f"[main] 啟動，frozen={getattr(sys,'frozen',False)}, exe={sys.executable}")
_log(f"[main] APP_DIR={APP_DIR}")

# 單實例鎖：已有一份在跑就只開瀏覽器，不重複啟動 server
import ctypes as _ctypes
_MUTEX_NAME = '健檢標案追蹤系統_SingleInstance'
_mutex = _ctypes.windll.kernel32.CreateMutexW(None, True, _MUTEX_NAME)
if _ctypes.windll.kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
    _log("[main] 已有實例在執行，等待 server 後開瀏覽器視窗")
    wait_for_port(timeout=10)
    open_window()
    sys.exit(0)

start_streamlit()
_log(f"[main] start_streamlit() 完成，PID={_streamlit_proc.pid if _streamlit_proc else 'None'}")

if not wait_for_port():
    _log("[main] wait_for_port 失敗，彈出錯誤訊息")
    _ctypes.windll.user32.MessageBoxW(
        0, '無法啟動服務，請確認程式完整性。', '錯誤', 0x10)
    sys.exit(1)

_log("[main] port 已開，呼叫 open_window()")
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


_log("[main] 建立 tray icon")
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

def _run_tray():
    _log("[main] tray.run() 開始")
    try:
        tray.run()
    except Exception as e:
        _log(f"[main] tray.run() 例外: {e}")
    _log("[main] tray.run() 結束")

_tray_thread = threading.Thread(target=_run_tray, daemon=True)
_tray_thread.start()

# 主 thread 監控子程序；server 掛了嘗試重啟一次，再掛才退出
_server_restarts = 0
while True:
    time.sleep(3)
    if not _tray_thread.is_alive():
        _log("[main] tray thread 已結束，程式退出")
        break
    if _streamlit_proc and _streamlit_proc.poll() is not None:
        if _server_restarts < 1:
            _server_restarts += 1
            _log(f"[main] streamlit 子程序意外結束，嘗試重啟 (第{_server_restarts}次)")
            start_streamlit()
            if not wait_for_port(timeout=30):
                _log("[main] 重啟後 port 未開，放棄")
                tray.stop()
                break
        else:
            _log(f"[main] streamlit 子程序再次結束，放棄重啟")
            tray.stop()
            break

cleanup()
