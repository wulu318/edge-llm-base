import os
import sys
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageFont
import uvicorn
from llama_cpp.server.app import app, Settings, router

# --- 1. 路径解决方案 ---
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# --- 2. 图标生成函数 ---
def create_image(emoji="🤖"):
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font_path = None
    if sys.platform == "win32":
        font_path = "C:/Windows/Fonts/seguiemj.ttf"
    elif sys.platform == "darwin":
        font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
    
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 48)
        else:
            noto_path = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
            if os.path.exists(noto_path):
                 font = ImageFont.truetype(noto_path, 48)
            else:
                font = ImageFont.load_default()
    except IOError:
        font = ImageFont.load_default()
        
    left, top, right, bottom = font.getbbox(emoji)
    text_width = right - left
    text_height = bottom - top
    x = (image.width - text_width) / 2 - left
    y = (image.height - text_height) / 2 - top
    draw.text((x, y), emoji, font=font, embedded_color=True)
    return image

# --- 配置 ---
BASE_PATH = get_base_path()
MODEL_PATH = os.path.join(BASE_PATH, "qwen3-0.6b-q4.gguf")
PORT = 56565
HOST = "127.0.0.1"

server_thread = None
stop_server_event = threading.Event()

def run_server():
    global stop_server_event
    if not os.path.exists(MODEL_PATH):
        print(f"致命错误：模型文件未找到于 {MODEL_PATH}")
        return
        
    settings = Settings(model=MODEL_PATH, host=HOST, port=PORT, n_gpu_layers=-1)
    app.dependency_overrides[router.get_settings] = lambda: settings
    config = uvicorn.Config(app, host=settings.host, port=settings.port, log_level="info")
    server = uvicorn.Server(config)
    server.run()
    print("服务器线程已停止。")

def start_server(icon):
    global server_thread, stop_server_event
    if server_thread is not None and server_thread.is_alive():
        return
    print("正在启动服务器...")
    stop_server_event.clear()
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    update_menu(icon)
    print(f"服务器已在端口 {PORT} 启动")

def stop_server(icon):
    global server_thread
    if server_thread is None or not server_thread.is_alive():
        return
    print("正在停止服务器...")
    stop_server_event.set()
    # 这里的停止逻辑可以简化，因为守护线程会随主程序退出
    server_thread = None
    update_menu(icon)
    print("服务器已停止")

def on_exit(icon):
    stop_server(icon)
    icon.stop()

def get_menu():
    is_running = server_thread is not None and server_thread.is_alive()
    yield item('Start Server', lambda: start_server(icon), enabled=not is_running)
    yield item('Stop Server', lambda: stop_server(icon), enabled=is_running)
    yield item('Exit', lambda: on_exit(icon))

def update_menu(icon):
    icon.menu = pystray.Menu(get_menu)
    
def setup_tray(icon):
    icon.visible = True
    start_server(icon)

# 主程序入口
icon_image = create_image("🤖")
# 为了兼容性，先保存再加载
icon_image.save("icon.png")
icon = pystray.Icon("Edge LLM Base", Image.open("icon.png"), "Edge LLM Base")
update_menu(icon)
icon.run(setup_tray)