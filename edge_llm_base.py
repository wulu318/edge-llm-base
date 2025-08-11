import os
import subprocess
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image
import sys

# 配置
MODEL_PATH = "qwen3-0.6b-q4.gguf"  # 您的Qwen3-0.6B INT4 GGUF文件
PORT = 56565  # API端口
HOST = "127.0.0.1"  # 监听所有接口

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
        "--n_gpu_layers", "-1"  # 使用所有可用GPU层，如果有；否则CPU
    ]
    server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    running = True
    print(f"Server started on port {PORT}")

def stop_server():
    global server_process, running
    if not running or server_process is None:
        return
    server_process.terminate()
    server_process.wait()
    running = False
    print("Server stopped")

def on_exit(icon):
    stop_server()
    icon.stop()

def setup(icon):
    icon.visible = True
    # 自动启动服务器
    start_server()

# 创建图标（简单图像；可替换）
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