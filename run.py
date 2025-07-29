#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
twitchTransFreeNeo 起動スクリプト
PyInstaller対応のエントリーポイント
"""

import sys
import os

# 実行ファイルの場合のパス処理
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# パスを追加
sys.path.insert(0, base_path)

# PyInstallerの場合、標準出力/エラー出力を設定
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.stdout = sys.stderr = open(os.devnull, 'w')

# メインアプリケーションを起動
from twitchTransFreeNeo.gui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.run()