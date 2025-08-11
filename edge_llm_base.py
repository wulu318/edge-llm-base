import os
import sys
import subprocess
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, filename="edge_llm_base.log", filemode="w")

def resource_path(relative_path):
    """ 获取资源文件的真实路径，兼容 PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 配置
MODEL_PATH = resource_path("qwen3-0.6b-q4.gguf")
PORT = 56565
HOST = "127.0.0.1"

server_process = None
running = False

def start_server():
    global server_process, running
    if running:
        return
    cmd = [
        sys.executable, "-m", "llama_cpp.server",
        "--model", MODEL_PATH,
        "--port", str(PORT),
        "--host", HOST,
        "--n_gpu_layers", "-1"
    ]
    server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    running = True
    logging.info(f"Server started on port {PORT}")

def stop_server():
    global server_process, running
    if not running or server_process is None:
        return
    server_process.terminate()
    server_process.wait()
    running = False
    logging.info("Server stopped")

def on_exit(icon):
    stop_server()
    icon.stop()

def setup(icon):
    icon.visible = True
    start_server()

# 创建图标
image = Image.new('RGB', (64, 64), color=(73, 109, 137))
icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")

# 菜单
icon.menu = pystray.Menu(
    item('Start Server', start_server, enabled=lambda: not running),
    item('Stop Server', stop_server, enabled=lambda: running),
    item('Exit', lambda: on_exit(icon))
)

# 运行托盘
icon.run(setup)
