import os
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image
import sys
import multiprocessing
import logging

# --- 關鍵改動: 導入服務器和配置工具 ---
# 這些庫會被 PyInstaller 通過 .spec 文件正確識別並打包
import uvicorn
from llama_cpp.server.app import create_app, Settings

def get_log_file_path():
    """獲取一個保證可寫的日誌文件路徑。"""
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
    獲取資源的絕對路徑。在 onedir 模式下，所有文件都在 _internal 文件夾中。
    """
    if getattr(sys, 'frozen', False):
        # 關鍵修正: 程序被打包後，所有依賴項都在 _internal 子文件夾中。
        base_path = os.path.join(os.path.dirname(sys.executable), '_internal')
    else:
        # 程序未被打包 (從 .py 腳本運行)
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- 配置 ---
MODEL_NAME = "qwen3-0.6b-q4.gguf"
MODEL_PATH = get_resource_path(MODEL_NAME) # 現在這個路徑會正確地指向 _internal
PORT = 56565
HOST = "127.0.0.1"

# --- 全局變量 ---
server_thread = None
server = None # 用於持有 uvicorn 服務器實例
running = False

def write_log(message):
    """一個輔助函數，用於向日誌文件寫入信息。"""
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] [MAIN_APP] {message}\n")
        print(f"[MAIN_APP] {message}")
    except Exception as e:
        print(f"寫入日誌失敗: {e}")

def start_server_thread():
    """這是一個包裝函數，用於從菜單啟動服務器線程。"""
    global server_thread
    if not running and (server_thread is None or not server_thread.is_alive()):
        write_log("從菜單請求啟動服務器...")
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
    else:
        write_log("服務器已在運行，忽略菜單啟動請求。")

def start_server():
    """在程序內部的一個新線程中，直接啟動 uvicorn 服務器。"""
    global server, running
    if running:
        return

    try:
        write_log("--- 準備啟動服務器 (線程模式) ---")
        write_log(f"模型路徑: {MODEL_PATH}")
        if not os.path.exists(MODEL_PATH):
            write_log(f"致命錯誤: 模型文件在路徑 {MODEL_PATH} 未找到!")
            return

        settings = Settings(model=MODEL_PATH, port=PORT, host=HOST, n_gpu_layers=-1)
        app = create_app(settings=settings)
        
        # 關鍵修正: 將 log_config 設置為 None，徹底禁用 uvicorn 的日誌配置。
        config = uvicorn.Config(app, host=HOST, port=PORT, log_config=None)
        
        server = uvicorn.Server(config)
        
        running = True
        write_log(f"服務器準備在 http://{HOST}:{PORT} 啟動")
        
        server.run()
        
        running = False
        write_log("服務器已停止。")

    except Exception as e:
        write_log(f"啟動服務器時發生致命錯誤: {e}")
        running = False

def stop_server():
    """優雅地停止 uvicorn 服務器。"""
    global server, running, server_thread
    if not running or server is None:
        write_log("服務器未在運行，忽略停止請求。")
        return
    
    write_log("--- 準備停止服務器 ---")
    server.should_exit = True
    
    if server_thread is not None and server_thread.is_alive():
        server_thread.join(timeout=5)
    
    running = False
    server = None
    server_thread = None
    write_log("服務器停止流程已完成。")

def on_exit(icon, item):
    write_log("程序退出。")
    stop_server()
    icon.stop()

def setup(icon):
    write_log("--- 程序初始化 ---")
    icon.visible = True
    start_server_thread() # 程序啟動時自動運行一次

if __name__ == '__main__':
    multiprocessing.freeze_support()

    if os.path.exists(LOG_FILE_PATH):
        try:
            os.remove(LOG_FILE_PATH)
        except OSError as e:
            print(f"移除舊日誌文件失敗: {e}")

    write_log(f"--- 主程序入口 --- 日誌將寫入到: {LOG_FILE_PATH}")

    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")

    # 恢復完整的右鍵菜單
    icon.menu = pystray.Menu(
        item('Start Server', start_server_thread, enabled=lambda _: not running),
        item('Stop Server', stop_server, enabled=lambda _: running),
        item('Exit', on_exit)
    )
    icon.run(setup)
