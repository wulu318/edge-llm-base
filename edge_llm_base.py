import os
import subprocess
import threading
import time
import pystray
from pystray import MenuItem as item
from PIL import Image
import sys
import multiprocessing

# --- 决定性的修复: 重新定义路径获取逻辑 ---

# 首先，一次性地、清晰地确定我们的程序资源根目录 (BASE_DIR) 在哪里。
if getattr(sys, 'frozen', False):
    # 如果程序被打包了，所有依赖项都在 _internal 子文件夹中。
    # sys.executable 是指 C:\...\EdgeLLMBase\edge_llm_base.exe
    BASE_DIR = os.path.join(os.path.dirname(sys.executable), '_internal')
else:
    # 如果是从 .py 脚本运行（开发环境），资源就在脚本旁边。
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_log_file_path():
    """获取一个保证可写的日志文件路径。"""
    try:
        home_dir = os.path.expanduser("~")
        log_dir = os.path.join(home_dir, ".EdgeLLMBase")
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, "edge_llm_base_log.txt")
    except Exception:
        # Fallback
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), "edge_llm_base_log.txt")
        else:
            return "edge_llm_base_log.txt"

LOG_FILE_PATH = get_log_file_path()

# --- 配置 ---
MODEL_NAME = "qwen3-0.6b-q4.gguf"
PORT = 56565
HOST = "127.0.0.1"

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

    write_log("--- 准备启动服务器 (subprocess 模式) ---")
    
    python_exe_name = "python.exe" if sys.platform == "win32" else "python"
    
    # 使用确定的 BASE_DIR 来构建所有路径，不再有额外的 "."
    python_path = os.path.join(BASE_DIR, python_exe_name)
    runner_script_path = os.path.join(BASE_DIR, "server_runner.py")
    model_path = os.path.join(BASE_DIR, MODEL_NAME)

    write_log(f"程序资源根目录 (BASE_DIR): {BASE_DIR}")
    write_log(f"期望的 Python 解释器路径: {python_path}")
    write_log(f"期望的启动器脚本路径: {runner_script_path}")
    write_log(f"期望的模型路径: {model_path}")

    if not os.path.exists(python_path):
        write_log(f"致命错误: 未找到 Python 解释器。")
        return

    cmd = [
        python_path,
        runner_script_path,
        "--model", model_path,
        "--port", str(PORT),
        "--host", HOST,
        "--n_gpu_layers", "-1"
    ]
    
    env = os.environ.copy()
    env["PYTHONHOME"] = BASE_DIR
    env["PYTHONPATH"] = BASE_DIR
    write_log(f"为子进程设置 PYTHONHOME: {BASE_DIR}")

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW
        
    try:
        write_log(f"执行命令: {' '.join(cmd)}")
        log_file_handle = open(LOG_FILE_PATH, "a", encoding="utf-8", buffering=1)
        
        server_process = subprocess.Popen(
            cmd, 
            stdout=log_file_handle, 
            stderr=log_file_handle, 
            creationflags=creationflags,
            env=env
        )
        running = True
        write_log(f"服务器子进程已成功启动，进程号: {server_process.pid}")
    except Exception as e:
        write_log(f"致命错误: 启动子进程失败。 错误信息: {e}")
        running = False

def stop_server():
    global server_process, running
    if not running or server_process is None:
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

    if os.path.exists(LOG_FILE_PATH):
        try:
            os.remove(LOG_FILE_PATH)
        except OSError as e:
            print(f"移除旧日志文件失败: {e}")

    write_log(f"--- 主程序入口 --- 日志将写入到: {LOG_FILE_PATH}")

    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    icon = pystray.Icon("Edge LLM Base", image, "Edge LLM Base")

    icon.menu = pystray.Menu(
        item('Start Server', lambda: threading.Thread(target=start_server).start(), enabled=lambda _: not running),
        item('Stop Server', stop_server, enabled=lambda _: running),
        item('Exit', on_exit)
    )
    icon.run(setup)
