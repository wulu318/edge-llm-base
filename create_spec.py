# 文件名: create_spec.py
# 这个脚本用于生成 PyInstaller 的 .spec 配置文件，以确保打包过程的稳定性和可重复性。

import sys
import os

# 获取当前 Python 环境中解释器的绝对路径。
# 这是最可靠的方法，可以避免在不同操作系统或 shell 中进行复杂的路径转换。
python_executable_path = sys.executable

# 在 Windows 系统上，路径中的反斜杠在 .spec 文件中需要被转义。
if sys.platform == "win32":
    python_executable_path = python_executable_path.replace('\\', '\\\\')

# 使用 f-string 定义 .spec 文件的内容模板。
# 这样做比用 echo 或 cat 命令更清晰、更不容易出错。
spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-
#
# 这个 .spec 文件是由 create_spec.py 自动生成的。

# Analysis 块负责分析所有依赖项。
a = Analysis(
    ['edge_llm_base.py'],
    pathex=[],
    # binaries: 强制包含二进制文件，如 python.exe。
    # 格式为 (源路径, 在输出文件夹中的目标位置)
    binaries=[('{python_executable_path}', '.')],
    # datas: 包含非二进制的数据文件，如模型和我们的启动器脚本。
    datas=[
        ('server_runner.py', '.'),
        ('qwen3-0.6b-q4.gguf', '.')
    ],
    # hiddenimports: 强制包含 PyInstaller 可能因静态分析而遗漏的库。
    hiddenimports=['llama_cpp.server'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data)

# EXE 块定义了最终生成的可执行文件的属性。
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='edge_llm_base',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # 对应 --windowed，不显示控制台窗口
    icon=None
)

# COLLECT 块负责将所有分析出的文件收集到一个文件夹中（onedir 模式）。
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='edge_llm_base'
)
"""

# 将生成的内容写入 build.spec 文件。
try:
    with open('build.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("build.spec file created successfully.")
except IOError as e:
    print(f"Error writing build.spec file: {e}")
    sys.exit(1)
