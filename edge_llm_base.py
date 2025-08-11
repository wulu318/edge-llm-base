import os
import subprocess
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image
import sys
import multiprocessing

def get_resource_path(relative_path):
    """ 在 onedir 模式下，获取资源的绝对路径 """
    # sys.executable 是指 edge_llm_base.exe
    # os.path.dirname(sys.executable) 就是它所在的文件夹
    base_path = os.path.dirname(sys.executable)
    return os.path.join(base_path, relative_path)

# --- 配置 ---
MODEL_NAME = "qwen3-0.6b-q4.gguf"
# 在 onedir 模式下，模型和 exe 在同一个文件夹里
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
    
    # 获取“启动器脚本”的路径
    runner_script_path = get_resource_path("server_runner.py")
    
    # 【关键】我们不再使用 sys.executable (它指向主程序)
    # 而是直接调用 python.exe (或 python)，它和主程序在同一个文件夹里
    python_exe = "python.exe" if sys.platform == "win32" else "python"
    python_path = get_resource_path(python_exe)


    cmd = [
        python_path, # <-- 使用文件夹内的 python 解释器
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