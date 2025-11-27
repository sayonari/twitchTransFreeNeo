#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyInstallerビルドスクリプト
twitchTransFreeNeoをPyInstallerでビルドします
Nuitkaより高速にビルドできます
"""

import sys
import os
import platform
import subprocess
from pathlib import Path

# Windows環境でのUTF-8出力を確保
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_version():
    """バージョンを取得"""
    try:
        with open('twitchTransFreeNeo/__init__.py', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('"')[1]
    except:
        return "Unknown"
    return "Unknown"

def build_macos(arch=None):
    """macOS用ビルド"""
    print(f"🍎 macOS用ビルドを開始します（アーキテクチャ: {arch or 'デフォルト'}）")

    # distディレクトリを作成
    Path("dist").mkdir(exist_ok=True)

    version = get_version()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=twitchTransFreeNeo",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data=twitchTransFreeNeo:twitchTransFreeNeo",
        "--collect-data=certifi",  # SSL証明書をバンドル
        "run.py",
    ]

    # アーキテクチャ指定（M1/Intel）
    if arch == "arm64":
        cmd.insert(3, "--target-arch=arm64")
    elif arch == "x86_64":
        cmd.insert(3, "--target-arch=x86_64")

    print(f"実行コマンド: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"✅ ビルド成功: dist/twitchTransFreeNeo.app")
    else:
        print(f"❌ ビルド失敗")
        sys.exit(1)

def build_windows():
    """Windows用ビルド"""
    print("🪟 Windows用ビルドを開始します（単体.exeモード）")

    # distディレクトリを作成
    Path("dist").mkdir(exist_ok=True)

    version = get_version()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=twitchTransFreeNeo",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data=twitchTransFreeNeo;twitchTransFreeNeo",
        "--collect-data=certifi",  # SSL証明書をバンドル
        "run.py",
    ]

    print(f"実行コマンド: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"✅ ビルド成功: dist/twitchTransFreeNeo.exe")
    else:
        print(f"❌ ビルド失敗")
        sys.exit(1)

def build_linux():
    """Linux用ビルド"""
    print("🐧 Linux用ビルドを開始します")

    # distディレクトリを作成
    Path("dist").mkdir(exist_ok=True)

    version = get_version()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=twitchTransFreeNeo",
        "--onefile",
        "--noconfirm",
        "--clean",
        "--add-data=twitchTransFreeNeo:twitchTransFreeNeo",
        "--collect-data=certifi",  # SSL証明書をバンドル
        "run.py",
    ]

    print(f"実行コマンド: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"✅ ビルド成功: dist/twitchTransFreeNeo")
    else:
        print(f"❌ ビルド失敗")
        sys.exit(1)

def main():
    """メイン処理"""
    print("=" * 60)
    print("twitchTransFreeNeo PyInstallerビルドスクリプト")
    print("=" * 60)

    # 引数処理
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
    else:
        # OSを自動検出
        system = platform.system()
        if system == "Darwin":
            target = "macos"
        elif system == "Windows":
            target = "windows"
        elif system == "Linux":
            target = "linux"
        else:
            print(f"❌ サポートされていないOS: {system}")
            sys.exit(1)

    print(f"ターゲット: {target}")
    print(f"バージョン: {get_version()}")
    print()

    # ビルド実行
    if target in ["macos", "macos_m1", "macos_arm64"]:
        build_macos(arch="arm64")
    elif target in ["macos_intel", "macos_x86_64"]:
        build_macos(arch="x86_64")
    elif target == "windows":
        build_windows()
    elif target == "linux":
        build_linux()
    else:
        print(f"❌ 不明なターゲット: {target}")
        print("使用可能なターゲット: macos, macos_m1, macos_intel, windows, linux")
        sys.exit(1)

    print()
    print("=" * 60)
    print("✅ ビルド完了")
    print("=" * 60)

if __name__ == "__main__":
    main()
