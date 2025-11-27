#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
twitchTransFreeNeo 起動スクリプト
PyInstaller対応のエントリーポイント
"""

import sys
import os

# 実行ファイルのディレクトリを取得（Nuitka/PyInstaller対応）
if getattr(sys, 'frozen', False) or hasattr(sys, '__compiled__'):
    # Nuitkaまたはその他のバイナリ実行時
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    # PyInstallerの場合のMEIPASS対応
    if hasattr(sys, '_MEIPASS'):
        internal_path = sys._MEIPASS
    else:
        internal_path = base_path

    # SSL証明書のパスを設定
    cert_path = None

    # 1. certifiパッケージから取得を試みる（PyInstaller --collect-data=certifi 対応）
    try:
        import certifi
        cert_path = certifi.where()
        if os.path.exists(cert_path):
            print(f"SSL証明書を設定 (certifi): {cert_path}")
        else:
            cert_path = None
    except ImportError:
        pass

    # 2. バンドルされたcacert.pemを探す
    if not cert_path:
        # PyInstallerのMEIPASS内のcertifiフォルダを探す
        possible_paths = [
            os.path.join(internal_path, 'certifi', 'cacert.pem'),
            os.path.join(internal_path, 'cacert.pem'),
            os.path.join(base_path, 'cacert.pem'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                cert_path = path
                print(f"SSL証明書を設定 (bundled): {cert_path}")
                break

    # SSL証明書のパスを環境変数に設定
    if cert_path and os.path.exists(cert_path):
        os.environ['SSL_CERT_FILE'] = cert_path
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
        os.environ['CURL_CA_BUNDLE'] = cert_path
    else:
        print("警告: SSL証明書ファイルが見つかりません")
else:
    # 通常のPythonスクリプト実行時
    base_path = os.path.dirname(os.path.abspath(__file__))

# パスを追加
sys.path.insert(0, base_path)

# PyInstallerの場合、標準出力/エラー出力を設定
# 注: デバッグのためコメントアウト（必要に応じて有効化）
# if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
#     sys.stdout = sys.stderr = open(os.devnull, 'w')

# メインアプリケーションを起動
from twitchTransFreeNeo.gui.main_window_flet import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.run()