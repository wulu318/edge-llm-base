import os
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image
import sys
import multiprocessing
import logging

# --- 关键改动: 导入服务器和配置工具 ---
# PyInstaller 会通过 .spec 文件正确识别并打包这些库
import uvicorn
from llama_cpp.server.app import create_app, Settings
# <-- 正确的做法: 导入CORS中间件 -->
from starlette.middleware.cors import CORSMiddleware

def get_log_file_path():
    """获取一个保证可写的日志文件路径。"""
    try:
        home_dir = os.path.expanduser("~")
        log_dir = os.path.join(home_dir, ".EdgeLLMBase")
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, "edge_llm_base_log.txt")
    except Exception:
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), "edge_llm_base_log.txt")
        else:
            return "edge_llm_base_log.txt"

LOG_FILE_PATH = get_log_file_path()

def get_resource_path(relative_path):
    """
    获取资源的绝对路径。在 onedir 模式下，所有文件都在 _internal 文件夹中。
    """
    if getattr(sys, 'frozen', False):
        # 关键修正: 程序被打包后，所有依赖项都在 _internal 子文件夹中。
        base_path = os.path.join(os.path.dirname(sys.executable), '_internal')
    else:
        # 程序未被打包 (从 .py 脚本运行)
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- 配置 ---
MODEL_NAME = "qwen3-0.6b-q4.gguf"
MODEL_PATH = get_resource_path(MODEL_NAME) # 现在这个路径会正确地指向 _internal
PORT = 56565
HOST = "127.0.0.1"

# --- 全局变量 ---
server_thread = None
server = None # 用于持有 uvicorn 服务器实例
running = False
icon = None   # 将 icon 提升为全局变量，以便在任何地方更新菜单

def write_log(message):
    """一个辅助函数，用于向日志文件写入信息。"""
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] [MAIN_APP] {message}\n")
        print(f"[MAIN_APP] {message}")
    except Exception as e:
        print(f"写入日志失败: {e}")

def update_menu_state():
    """通知 pystray 更新菜单项的启用/禁用状态。"""
    global icon
    if icon:
        # 通过重新生成并赋值菜单对象来触发 pystray 的更新
        icon.menu = pystray.Menu(
            item('启动服务器', start_server_thread, enabled=lambda _: not running),
            item('停止服务器', stop_server, enabled=lambda _: running),
            item('退出', on_exit)
        )
        write_log(f"菜单状态已更新。Running: {running}")

def start_server_thread():
    """这是一个包装函数，用于从菜单启动服务器线程。"""
    global server_thread
    if not running and (server_thread is None or not server_thread.is_alive()):
        write_log("从菜单请求启动服务器...")
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
    else:
        write_log("服务器已在运行，忽略菜单启动请求。")

def start_server():
    """在程序内部的一个新线程中，直接启动 uvicorn 服务器。"""
    global server, running
    if running:
        return

    try:
        write_log("--- 准备启动服务器 (线程模式) ---")
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

        write_log(f"模型路径: {MODEL_PATH}")
        if not os.path.exists(MODEL_PATH):
            write_log(f"致命错误: 模型文件在路径 {MODEL_PATH} 未找到!")
            return

        # --- 修复 1: 从 Settings 中移除 `cors_origins` ---
        # 这个 Settings 对象是用于配置 llama-cpp 模型本身，而不是Web服务器。
        settings = Settings(
            model=MODEL_PATH,
            port=PORT,
            host=HOST,
            n_gpu_layers=-1
        )
        app = create_app(settings=settings)

        # --- 修复 2: 添加 CORS 作为中间件 (Middleware) ---
        # 这才是为Web应用允许跨域请求的正确方式。
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 允许所有来源
            allow_credentials=True,
            allow_methods=["*"],  # 允许所有方法 (GET, POST 等)
            allow_headers=["*"],  # 允许所有请求头
        )

        config = uvicorn.Config(app, host=HOST, port=PORT, log_config=None)
        server = uvicorn.Server(config)

        # 在服务器阻塞运行前，更新状态并刷新菜单
        running = True
        write_log(f"服务器准备在 http://{HOST}:{PORT} 启动")
        update_menu_state()

        server.run()

        # 服务器停止后，这里的代码才会执行
        running = False
        write_log("服务器已停止。")
        update_menu_state() # 服务器停止后再次更新菜单
    except Exception as e:
        write_log(f"启动服务器时发生致命错误: {e}")
        running = False
        update_menu_state() # 即使启动失败，也要确保菜单状态正确

def stop_server():
    """优雅地停止 uvicorn 服务器。"""
    global server, running
    if not running or server is None:
        write_log("服务器未在运行，忽略停止请求。")
        return
    write_log("--- 准备停止服务器 ---")
    # 发送退出信号，server.run() 将会结束，并触发后续的状态更新
    server.should_exit = True
    write_log("服务器停止请求已发送。")

def on_exit(icon, item):
    write_log("程序退出。")
    # 确保在主线程中请求停止
    if running and server:
        server.should_exit = True
    
    # 等待服务器线程结束
    if server_thread is not None and server_thread.is_alive():
        write_log("等待服务器线程关闭...")
        server_thread.join(timeout=5)
        
    icon.stop()

def setup(icon_ref):
    """pystray 调用的初始化函数"""
    global icon
    icon = icon_ref
    write_log("--- 程序初始化 ---")
    icon.visible = True
    start_server_thread() # 程序启动时自动运行一次

if __name__ == '__main__':
    multiprocessing.freeze_support()

    if os.path.exists(LOG_FILE_PATH):
        try:
            os.remove(LOG_FILE_PATH)
        except OSError as e:
            print(f"移除旧日志文件失败: {e}")

    write_log(f"--- 主程序入口 --- 日志将写入到: {LOG_FILE_PATH}")
    
    # 为托盘图标创建一个简单的占位图像
    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    
    # 在主逻辑中创建 icon 实例，以便可以将其传递给 setup 函数
    icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")
    icon.menu = pystray.Menu(
        item('启动服务器', start_server_thread, enabled=lambda _: not running),
        item('停止服务器', stop_server, enabled=lambda _: running),
        item('退出', on_exit)
    )
    
    # icon.run 会调用 setup 函数，并将 icon 自身作为参数传入
    icon.run(setup)