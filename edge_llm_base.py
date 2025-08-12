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
# 这些库会被 PyInstaller 通过 .spec 文件正确识别并打包
import uvicorn
from llama_cpp.server.app import create_app, Settings

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

def write_log(message):
    """一个辅助函数，用于向日志文件写入信息。"""
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] [MAIN_APP] {message}\n")
        print(f"[MAIN_APP] {message}")
    except Exception as e:
        print(f"写入日志失败: {e}")

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
        write_log(f"模型路径: {MODEL_PATH}")
        if not os.path.exists(MODEL_PATH):
            write_log(f"致命错误: 模型文件在路径 {MODEL_PATH} 未找到!")
            return

        settings = Settings(model=MODEL_PATH, port=PORT, host=HOST, n_gpu_layers=-1)
        app = create_app(settings=settings)
        
        # 关键修正: 为 uvicorn 提供一个明确的日志配置，以解决打包后的 formatter 错误
        LOGGING_CONFIG = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(message)s",
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
            },
        }
        
        config = uvicorn.Config(app, host=HOST, port=PORT, log_level="info", log_config=LOGGING_CONFIG)
        
        server = uvicorn.Server(config)
        
        running = True
        write_log(f"服务器准备在 http://{HOST}:{PORT} 启动")
        
        server.run()
        
        running = False
        write_log("服务器已停止。")

    except Exception as e:
        write_log(f"启动服务器时发生致命错误: {e}")
        running = False

def stop_server():
    """优雅地停止 uvicorn 服务器。"""
    global server, running, server_thread
    if not running or server is None:
        write_log("服务器未在运行，忽略停止请求。")
        return
    
    write_log("--- 准备停止服务器 ---")
    server.should_exit = True
    
    if server_thread is not None and server_thread.is_alive():
        server_thread.join(timeout=5)
    
    running = False
    server = None
    server_thread = None
    write_log("服务器停止流程已完成。")

def on_exit(icon, item):
    write_log("程序退出。")
    stop_server()
    icon.stop()

def setup(icon):
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

    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")

    # 恢复完整的右键菜单
    icon.menu = pystray.Menu(
        item('Start Server', start_server_thread, enabled=lambda _: not running),
        item('Stop Server', stop_server, enabled=lambda _: running),
        item('Exit', on_exit)
    )
    icon.run(setup)
