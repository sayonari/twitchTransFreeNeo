#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
twitchTransFreeNeo 起動スクリプト
PyInstaller対応のエントリーポイント
"""

import sys
import os

def setup_environment():
    """実行環境をセットアップ"""
    # PyInstallerの実行時パスを取得
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた実行ファイルの場合
        application_path = os.path.dirname(sys.executable)
        bundle_dir = sys._MEIPASS
    else:
        # 通常のPythonスクリプトの場合
        application_path = os.path.dirname(os.path.abspath(__file__))
        bundle_dir = application_path
    
    # プロジェクトルートパスを追加
    sys.path.insert(0, bundle_dir)
    sys.path.insert(0, application_path)
    
    return application_path

def main():
    """メイン実行関数"""
    try:
        # 環境セットアップ
        app_path = setup_environment()
        
        # SimpleMainWindowを直接インポートして実行
        from twitchTransFreeNeo.gui.simple_main_window import SimpleMainWindow
        
        from twitchTransFreeNeo import __version__
        print(f"twitchTransFreeNeo v{__version__} 起動中...")
        print("==================================================")
        
        # アプリケーション実行
        app = SimpleMainWindow()
        app.run()
        
        return 0
        
    except ImportError as e:
        print(f"インポートエラー: {e}")
        print("モジュールが見つかりません。")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())