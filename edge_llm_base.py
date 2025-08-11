import os
import subprocess
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image
import sys
import multiprocessing

# --- 已移除之前错误的 "虚拟导入" ---

def get_resource_path(relative_path):
    """
    获取资源的绝对路径，对开发环境和 PyInstaller 的 onedir 模式都有效。
    """
    if getattr(sys, 'frozen', False):
        # 程序被打包了 (frozen)
        base_path = os.path.dirname(sys.executable)
    else:
        # 程序未被打包 (从 .py 脚本运行)
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- 配置 ---
MODEL_NAME = "qwen3-0.6b-q4.gguf"
MODEL_PATH = get_resource_path(MODEL_NAME)
PORT = 56565
HOST = "127.0.0.1"

# --- 全局变量 ---
server_process = None
running = False

def start_server():
    global server_process, running
    if running:
        return
    
    python_exe_name = "python.exe" if sys.platform == "win32" else "python"
    python_path = get_resource_path(python_exe_name)
    runner_script_path = get_resource_path("server_runner.py")

    cmd = [
        python_path,
        runner_script_path,
        "--model", MODEL_PATH,
        "--port", str(PORT),
        "--host", HOST,
        "--n_gpu_layers", "-1"
    ]
    
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW
        
    print("Starting server with command:", " ".join(cmd))
    server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
    running = True
    print("Server process started.")

def stop_server():
    global server_process, running
    if not running or server_process is None:
        return
    print("Stopping server process...")
    server_process.terminate()
    server_process.wait()
    running = False
    print("Server process stopped.")

def on_exit(icon, item):
    stop_server()
    icon.stop()

def setup(icon):
    icon.visible = True
    threading.Thread(target=start_server, daemon=True).start()

if __name__ == '__main__':
    multiprocessing.freeze_support()

    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")

    icon.menu = pystray.Menu(
        item('Start Server', lambda: threading.Thread(target=start_server).start(), enabled=lambda _: not running),
        item('Stop Server', stop_server, enabled=lambda _: running),
        item('Exit', on_exit)
    )
    icon.run(setup)

