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
    # PyInstallerでビルドされた場合、cacert.pemのパスを設定
    # 実行ファイルと同じディレクトリにcacert.pemがある場合
    cert_path = os.path.join(os.path.dirname(sys.executable), 'cacert.pem')
    if not os.path.exists(cert_path):
        # MEIPASSディレクトリ内のcacert.pemを探す
        cert_path = os.path.join(base_path, 'cacert.pem')
    
    if os.path.exists(cert_path):
        # SSL証明書のパスを環境変数に設定
        os.environ['SSL_CERT_FILE'] = cert_path
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
        os.environ['CURL_CA_BUNDLE'] = cert_path
        print(f"SSL証明書を設定: {cert_path}")
    else:
        print(f"警告: SSL証明書ファイルが見つかりません")
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# パスを追加
sys.path.insert(0, base_path)

# PyInstallerの場合、標準出力/エラー出力を設定
# 注: デバッグのためコメントアウト（必要に応じて有効化）
# if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
#     sys.stdout = sys.stderr = open(os.devnull, 'w')

# メインアプリケーションを起動
from twitchTransFreeNeo.gui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.run()