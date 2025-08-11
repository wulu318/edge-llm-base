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
    """ 获取资源的绝对路径，兼容开发环境和 PyInstaller 打包环境 """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 创建的临时文件夹
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
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
    
    # 获取“启动器脚本”的路径
    runner_script_path = get_resource_path("server_runner.py")

    # 创建完整的命令，包含所有参数
    cmd = [
        sys.executable,
        runner_script_path,
        "--model", MODEL_PATH,
        "--port", str(PORT),
        "--host", HOST,
        "--n_gpu_layers", "-1"
    ]
    
    # 在 Windows 上隐藏子进程的控制台窗口
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
    # 在一个独立的线程中启动服务器，防止阻塞 UI
    threading.Thread(target=start_server, daemon=True).start()

# --- 主程序入口 ---
if __name__ == '__main__':
    # 在 Windows 打包程序中，这行代码是好习惯
    multiprocessing.freeze_support()

    # 创建图标
    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")

    # 定义菜单
    icon.menu = pystray.Menu(
        item('Start Server', lambda: threading.Thread(target=start_server).start(), enabled=lambda _: not running),
        item('Stop Server', stop_server, enabled=lambda _: running),
        item('Exit', on_exit)
    )

    # 运行托盘
    icon.run(setup)