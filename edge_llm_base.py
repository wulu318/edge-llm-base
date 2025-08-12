import os
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image
import sys
import multiprocessing

# --- 关键改动: 导入服务器和配置工具 ---
# 这些库会被 PyInstaller 自动识别并打包
import uvicorn
from llama_cpp.server.app import create_app, Settings

def get_resource_path(relative_path):
    """
    获取资源的绝对路径。在 onedir 模式下，所有文件都在 .exe 旁边。
    """
    if getattr(sys, 'frozen', False):
        # 程序被打包后
        base_path = os.path.dirname(sys.executable)
    else:
        # 从 .py 脚本运行
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- 配置 ---
MODEL_NAME = "qwen3-0.6b-q4.gguf"
MODEL_PATH = get_resource_path(MODEL_NAME)
PORT = 56565
HOST = "127.0.0.1" # 改为 127.0.0.1 更安全，只允许本机访问

# --- 全局变量 ---
server_thread = None
server = None # 用于持有 uvicorn 服务器实例
running = False

def start_server():
    """在程序内部的一个新线程中，直接启动 uvicorn 服务器。"""
    global server, running
    if running:
        return

    try:
        # 1. 创建服务器配置
        settings = Settings(
            model=MODEL_PATH,
            port=PORT,
            host=HOST,
            n_gpu_layers=-1,
        )
        # 2. 根据配置创建 FastAPI 应用
        app = create_app(settings=settings)
        
        # 3. 配置 uvicorn 服务器
        config = uvicorn.Config(
            app,
            host=HOST,
            port=PORT,
            log_level="info",
        )
        
        # 4. 创建服务器实例，以便我们能控制它
        server = uvicorn.Server(config)
        
        running = True
        print(f"服务器准备在 http://{HOST}:{PORT} 启动")
        
        # 5. 运行服务器 (这是一个阻塞调用，会一直运行直到停止)
        server.run()
        
        # 当服务器停止后
        running = False
        print("服务器已停止。")

    except Exception as e:
        print(f"启动服务器时发生致命错误: {e}")
        running = False

def stop_server():
    """优雅地停止 uvicorn 服务器。"""
    global server, running, server_thread
    if not running or server is None:
        return
    
    print("正在请求服务器停止...")
    # uvicorn 提供了优雅退出的方法
    server.should_exit = True
    
    # 等待线程自然结束
    if server_thread is not None and server_thread.is_alive():
        server_thread.join(timeout=5)
    
    running = False
    server = None
    print("服务器停止流程已完成。")

def on_exit(icon, item):
    stop_server()
    icon.stop()

def setup(icon):
    global server_thread
    icon.visible = True
    # 创建并启动服务器线程
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

if __name__ == '__main__':
    multiprocessing.freeze_support()

    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")

    # 菜单可以简化，因为服务器随程序生命周期自动管理
    icon.menu = pystray.Menu(
        item('Exit', on_exit)
    )
    icon.run(setup)
