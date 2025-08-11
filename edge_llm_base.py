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
    """
    获取资源的绝对路径，对开发环境和 PyInstaller 的 onedir 模式都有效。
    """
    if getattr(sys, 'frozen', False):
        # 程序被打包了 (frozen)
        base_path = os.path.dirname(sys.executable)
    else:
        # 程序未被打包 (从 .py 脚本运行)
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- 配置 ---
MODEL_NAME = "qwen3-0.6b-q4.gguf"
MODEL_PATH = get_resource_path(MODEL_NAME)
PORT = 56565
HOST = "127.0.0.1"
LOG_FILE_NAME = "edge_llm_base_log.txt"
LOG_FILE_PATH = get_resource_path(LOG_FILE_NAME)

# --- 全局变量 ---
server_process = None
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

def start_server():
    global server_process, running
    if running:
        write_log("服务器已在运行，忽略启动请求。")
        return

    write_log("--- 准备启动服务器 ---")
    
    python_exe_name = "python.exe" if sys.platform == "win32" else "python"
    python_path = get_resource_path(python_exe_name)
    runner_script_path = get_resource_path("server_runner.py")

    # 启动前检查关键文件是否存在
    if not os.path.exists(python_path):
        write_log(f"致命错误: 在 {python_path} 未找到 Python 解释器。")
        return
    if not os.path.exists(runner_script_path):
        write_log(f"致命错误: 在 {runner_script_path} 未找到启动器脚本。")
        return
    if not os.path.exists(MODEL_PATH):
        write_log(f"致命错误: 在 {MODEL_PATH} 未找到模型文件。")
        return

    cmd = [
        python_path,
        runner_script_path,
        "--model", MODEL_PATH,
        "--port", str(PORT),
        "--host", HOST,
        "--n_gpu_layers", "-1"
    ]
    
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW
        
    try:
        write_log(f"执行命令: {' '.join(cmd)}")
        # 以追加模式打开日志文件，用于接收子进程的所有输出
        log_file_handle = open(LOG_FILE_PATH, "a", encoding="utf-8", buffering=1)
        
        server_process = subprocess.Popen(
            cmd, 
            stdout=log_file_handle, 
            stderr=log_file_handle, 
            creationflags=creationflags
        )
        running = True
        write_log(f"服务器子进程已成功启动，进程号: {server_process.pid}")
    except Exception as e:
        write_log(f"致命错误: 启动子进程失败。 错误信息: {e}")
        running = False

def stop_server():
    global server_process, running
    if not running or server_process is None:
        write_log("服务器未在运行，忽略停止请求。")
        return
    
    write_log(f"--- 准备停止服务器，进程号: {server_process.pid} ---")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
        write_log("服务器进程已成功终止。")
    except subprocess.TimeoutExpired:
        write_log("服务器进程在5秒内未响应终止信号，强制结束。")
        server_process.kill()
        write_log("服务器进程已被强制结束。")
    
    running = False
    server_process = None

def on_exit(icon, item):
    write_log("程序退出。")
    stop_server()
    icon.stop()

def setup(icon):
    write_log("--- 程序初始化 ---")
    icon.visible = True
    threading.Thread(target=start_server, daemon=True).start()

if __name__ == '__main__':
    multiprocessing.freeze_support()

    # 启动前清空一次日志文件，方便查看本次运行的日志
    if os.path.exists(LOG_FILE_PATH):
        try:
            os.remove(LOG_FILE_PATH)
        except OSError as e:
            print(f"移除旧日志文件失败: {e}")

    write_log("--- 主程序入口 ---")

    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")

    icon.menu = pystray.Menu(
        item('Start Server', lambda: threading.Thread(target=start_server).start(), enabled=lambda _: not running),
        item('Stop Server', stop_server, enabled=lambda _: running),
        item('Exit', on_exit)
    )
    icon.run(setup)
