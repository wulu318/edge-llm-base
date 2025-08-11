import os
import sys
import subprocess
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("edge_llm_base.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def resource_path(relative_path):
    """获取资源文件的真实路径，兼容PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 配置
MODEL_PATH = resource_path("qwen3-0.6b-q4.gguf")  # 您的Qwen3-0.6B INT4 GGUF文件
PORT = 56565  # API端口
HOST = "0.0.0.0"  # 监听所有接口

server_process = None
running = False

def start_server():
    global server_process, running
    if running:
        logging.info("服务器已在运行")
        return
    
    # 检查模型文件是否存在
    if not os.path.exists(MODEL_PATH):
        logging.error(f"模型文件不存在: {MODEL_PATH}")
        return
        
    cmd = [
        sys.executable, "-m", "llama_cpp.server",
        "--model", MODEL_PATH,
        "--port", str(PORT),
        "--host", HOST,
        "--n_gpu_layers", "-1"  # 使用所有可用GPU层，如果有；否则CPU
    ]
    
    try:
        server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        running = True
        logging.info(f"服务器已启动，端口: {PORT}")
    except Exception as e:
        logging.error(f"启动服务器失败: {e}")
        logging.error(traceback.format_exc())

def stop_server():
    global server_process, running
    if not running or server_process is None:
        logging.info("服务器未运行")
        return
    
    try:
        server_process.terminate()
        server_process.wait(timeout=10)  # 等待最多10秒
        running = False
        logging.info("服务器已停止")
    except subprocess.TimeoutExpired:
        server_process.kill()
        server_process.wait()
        logging.warning("服务器强制终止")
    except Exception as e:
        logging.error(f"停止服务器时出错: {e}")
        logging.error(traceback.format_exc())

def on_exit(icon):
    logging.info("正在退出程序...")
    stop_server()
    icon.stop()

def setup(icon):
    try:
        icon.visible = True
        # 自动启动服务器
        start_server()
    except Exception as e:
        logging.error(f"初始化失败: {e}")
        logging.error(traceback.format_exc())
        icon.stop()

# 创建图标（简单图像；可替换）
try:
    # 尝试加载图标文件
    icon_path = resource_path("icon.png")
    if os.path.exists(icon_path):
        image = Image.open(icon_path)
    else:
        # 如果没有图标文件，创建一个简单的图像
        image = Image.new('RGB', (64, 64), color=(73, 109, 137))
except Exception as e:
    logging.warning(f"加载图标失败，使用默认图像: {e}")
    image = Image.new('RGB', (64, 64), color=(73, 109, 137))

# 创建系统托盘图标
icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")

# 菜单
icon.menu = pystray.Menu(
    item('启动服务器', start_server, enabled=lambda: not running),
    item('停止服务器', stop_server, enabled=lambda: running),
    item('退出', lambda: on_exit(icon))
)

if __name__ == "__main__":
    logging.info("Edge LLM Base 启动中...")
    try:
        # 运行托盘
        icon.run(setup)
    except Exception as e:
        logging.error(f"程序运行失败: {e}")
        logging.error(traceback.format_exc())
