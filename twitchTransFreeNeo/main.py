#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
twitchTransFreeNeo - Next Generation Twitch Chat Translator
GUI版Twitchチャット翻訳ツール

メインエントリーポイント
"""

import sys
import os
import traceback
from typing import Optional

# パス設定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies() -> tuple[bool, list[str]]:
    """依存関係チェック"""
    missing_packages = []
    
    try:
        import tkinter
    except ImportError:
        missing_packages.append("tkinter (通常Pythonに含まれています)")
    
    try:
        import asyncio
    except ImportError:
        missing_packages.append("asyncio")
    
    try:
        import aiohttp
    except ImportError:
        missing_packages.append("aiohttp")
    
    try:
        import twitchio
    except ImportError:
        missing_packages.append("twitchio")
    
    try:
        import async_google_trans_new
    except ImportError:
        missing_packages.append("async_google_trans_new")
    
    try:
        import emoji
    except ImportError:
        missing_packages.append("emoji")
    
    try:
        import aiosqlite
    except ImportError:
        missing_packages.append("aiosqlite")
    
    # オプション依存関係
    optional_missing = []
    
    try:
        import deepl
    except ImportError:
        optional_missing.append("deepl-translate (DeepL翻訳を使用する場合)")
    
    if missing_packages:
        return False, missing_packages
    
    if optional_missing:
        print("オプション依存関係が不足しています:")
        for pkg in optional_missing:
            print(f"  - {pkg}")
        print()
    
    return True, []

def create_requirements_file():
    """requirements.txtを作成"""
    requirements = [
        "aiohttp>=3.8.0",
        "twitchio>=2.3.0", 
        "async-google-trans-new>=1.4.5",
        "emoji>=2.2.0",
        "aiosqlite>=0.17.0",
        "deepl-translate>=1.2.0"
    ]
    
    try:
        with open("requirements.txt", "w", encoding="utf-8") as f:
            for req in requirements:
                f.write(f"{req}\n")
        print("requirements.txt を作成しました")
        return True
    except Exception as e:
        print(f"requirements.txt 作成エラー: {e}")
        return False

def setup_error_handling():
    """エラーハンドリング設定"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"未処理例外が発生しました:\n{error_msg}")
        
        # GUIエラーダイアログ表示
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()  # メインウィンドウを隠す
            
            messagebox.showerror(
                "エラー", 
                f"予期しないエラーが発生しました:\n\n{exc_value}\n\nプログラムを終了します。"
            )
            root.destroy()
        except:
            pass
    
    sys.excepthook = handle_exception

def main():
    """メイン関数"""
    print("twitchTransFreeNeo v1.0.0 起動中...")
    print("=" * 50)
    
    # エラーハンドリング設定
    setup_error_handling()
    
    # 依存関係チェック
    print("依存関係をチェック中...")
    deps_ok, missing = check_dependencies()
    
    if not deps_ok:
        print("エラー: 必要なパッケージが不足しています:")
        for pkg in missing:
            print(f"  - {pkg}")
        print()
        print("必要なパッケージをインストールしてください:")
        print("pip install -r requirements.txt")
        
        # requirements.txt作成を提案
        if input("requirements.txt を作成しますか? (y/N): ").lower() == 'y':
            create_requirements_file()
        
        return 1
    
    print("依存関係OK")
    
    try:
        # メインアプリケーション起動
        print("アプリケーションを起動中...")
        
        # パッケージのパスを正しく設定
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from gui.simple_main_window import SimpleMainWindow
        
        app = SimpleMainWindow()
        print("GUI初期化完了")
        print("=" * 50)
        
        # アプリケーション実行
        app.run()
        
    except ImportError as e:
        print(f"インポートエラー: {e}")
        print("モジュールパスを確認してください")
        return 1
    
    except Exception as e:
        print(f"起動エラー: {e}")
        traceback.print_exc()
        return 1
    
    print("アプリケーションを終了しました")
    return 0

if __name__ == "__main__":
    sys.exit(main())