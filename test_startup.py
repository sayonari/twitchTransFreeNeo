#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
twitchTransFreeNeo 起動テスト
依存関係と基本機能のテスト
"""

def test_imports():
    """依存関係のテスト"""
    try:
        import tkinter
        print("✓ tkinter OK")
    except ImportError as e:
        print(f"✗ tkinter エラー: {e}")
        return False
    
    try:
        from twitchTransFreeNeo.utils.config_manager import ConfigManager
        print("✓ ConfigManager OK")
    except ImportError as e:
        print(f"✗ ConfigManager エラー: {e}")
        return False
    
    try:
        from twitchTransFreeNeo.core.database import TranslationDatabase
        print("✓ TranslationDatabase OK")
    except ImportError as e:
        print(f"✗ TranslationDatabase エラー: {e}")
        return False
    
    try:
        from twitchTransFreeNeo.core.translator import TranslationEngine
        print("✓ TranslationEngine OK")
    except ImportError as e:
        print(f"✗ TranslationEngine エラー: {e}")
        return False
    
    return True

def test_config():
    """設定システムのテスト"""
    try:
        from twitchTransFreeNeo.utils.config_manager import ConfigManager
        
        config = ConfigManager("test_config.json")
        print("✓ ConfigManager インスタンス作成 OK")
        
        # 設定値テスト
        config.set("test_key", "test_value")
        value = config.get("test_key")
        assert value == "test_value"
        print("✓ 設定値の設定・取得 OK")
        
        # 保存・読み込みテスト
        config.save_config()
        print("✓ 設定保存 OK")
        
        config2 = ConfigManager("test_config.json")
        value2 = config2.get("test_key")
        assert value2 == "test_value"
        print("✓ 設定読み込み OK")
        
        return True
        
    except Exception as e:
        print(f"✗ 設定システムエラー: {e}")
        return False

def test_database():
    """データベースのテスト"""
    try:
        from twitchTransFreeNeo.core.database import TranslationDatabase
        
        db = TranslationDatabase("test_translations.db")
        print("✓ TranslationDatabase インスタンス作成 OK")
        
        return True
        
    except Exception as e:
        print(f"✗ データベースエラー: {e}")
        return False

def test_basic_gui():
    """基本GUI機能のテスト"""
    try:
        import tkinter as tk
        
        # 基本ウィンドウ作成テスト
        root = tk.Tk()
        root.title("テストウィンドウ")
        root.geometry("300x200")
        
        label = tk.Label(root, text="twitchTransFreeNeo テスト")
        label.pack(pady=20)
        
        button = tk.Button(root, text="閉じる", command=root.destroy)
        button.pack(pady=10)
        
        print("✓ 基本GUI作成 OK")
        print("  (テストウィンドウが表示されたら正常です)")
        
        # 1秒後に自動で閉じる
        root.after(1000, root.destroy)
        root.mainloop()
        
        print("✓ GUIイベントループ OK")
        return True
        
    except Exception as e:
        print(f"✗ GUI作成エラー: {e}")
        return False

def main():
    """メインテスト"""
    print("=" * 50)
    print("twitchTransFreeNeo 起動テスト")
    print("=" * 50)
    
    all_passed = True
    
    print("\n1. 依存関係テスト")
    print("-" * 30)
    if not test_imports():
        all_passed = False
    
    print("\n2. 設定システムテスト")
    print("-" * 30)
    if not test_config():
        all_passed = False
    
    print("\n3. データベーステスト")
    print("-" * 30)
    if not test_database():
        all_passed = False
    
    print("\n4. 基本GUIテスト")
    print("-" * 30)
    if not test_basic_gui():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ 全てのテストが成功しました")
        print("twitchTransFreeNeo を起動する準備ができています")
        print("\n起動方法:")
        print("cd twitchTransFreeNeo")
        print("python main.py")
    else:
        print("✗ 一部のテストが失敗しました")
        print("依存関係を確認してください:")
        print("pip install -r requirements.txt")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())