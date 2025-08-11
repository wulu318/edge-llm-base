# 文件名: server_runner.py
import runpy
import sys

if __name__ == '__main__':
    try:
        # 这个脚本的唯一任务就是忠实地模拟 `python -m llama_cpp.server`
        runpy.run_module("llama_cpp.server", run_name="__main__")
    except Exception as e:
        print(f"Error running llama_cpp.server: {e}", file=sys.stderr)
        sys.exit(1)