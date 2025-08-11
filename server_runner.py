# 文件名: server_runner.py
# 这个脚本不需要做任何事，只需要调用 runpy 即可。
# 所有参数都会由 sys.argv 自动传递给 llama_cpp.server。
import runpy
import sys

if __name__ == '__main__':
    try:
        runpy.run_module("llama_cpp.server", run_name="__main__")
    except Exception as e:
        print(f"Error running llama_cpp.server: {e}", file=sys.stderr)
        sys.exit(1)