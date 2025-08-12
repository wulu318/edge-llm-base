# 文件名: create_spec.py
# 这个脚本用于生成一个基础的 .spec 配置文件。
# 解释器 (python.exe) 和它的依赖库将由 GitHub Actions 工作流手动复制。

import sys

# 定义 .spec 文件的内容模板。
spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-
# 这个 .spec 文件是由 create_spec.py 自动生成的。

a = Analysis(
    ['edge_llm_base.py'],
    pathex=[],
    # binaries 留空，我们将手动处理。
    binaries=[],
    # datas 包含模型和我们的启动器脚本。
    datas=[
        ('server_runner.py', '.'),
        ('qwen3-0.6b-q4.gguf', '.')
    ],
    # hiddenimports 强制包含 PyInstaller 可能找不到的库。
    hiddenimports=['llama_cpp.server'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data)

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
    console=False, # 对应 --windowed
    icon=None
)

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
    print("build.spec file created successfully (manual binary copy required).")
except IOError as e:
    print(f"Error writing build.spec file: {e}")
    sys.exit(1)
