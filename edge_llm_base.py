import os
import subprocess
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image
import sys

# ... (你之前的 get_resource_path 函数和配置部分保持不变) ...

def get_resource_path(relative_path):
    """ 获取资源的绝对路径，兼容开发环境和 PyInstaller 打包环境 """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 配置
MODEL_NAME = "qwen3-0.6b-q4.gguf"
MODEL_PATH = get_resource_path(MODEL_NAME)
PORT = 56565
HOST = "127.0.0.1"

server_process = None
running = False

def start_server():
    global server_process, running
    if running:
        return
    # 注意：这里的 sys.executable 确保子进程使用和主进程相同的 Python 解释器
    # 这在打包环境中至关重要
    cmd = [
        sys.executable, "-m", "llama_cpp.server",
        "--model", MODEL_PATH,
        "--port", str(PORT),
        "--host", HOST,
        "--n_gpu_layers", "-1"
    ]
    # 为了防止子进程也弹出窗口（如果打包时用了 --console），可以设置创建标志
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW
        
    server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
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

# --- 这是关键的修改部分 ---

# 只有当这个脚本是主程序时，才运行下面的代码
if __name__ == '__main__':
    # 在 Windows 上，需要为 multiprocessing 提供支持
    # 这行代码对于防止子进程重新执行主逻辑至关重要
    import multiprocessing
    multiprocessing.freeze_support()

    def on_exit(icon, item):
        stop_server()
        icon.stop()

    def setup(icon):
        icon.visible = True
        # 在一个独立的线程中启动服务器，防止阻塞 UI
        threading.Thread(target=start_server, daemon=True).start()

    # 创建图标
    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")

    # 定义菜单
    icon.menu = pystray.Menu(
        item('Start Server', start_server, enabled=lambda _: not running),
        item('Stop Server', stop_server, enabled=lambda _: running),
        item('Exit', on_exit)
    )

    # 运行托盘图标
    icon.run(setup)