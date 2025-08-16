# CLAUDE.md - プロジェクト固有の指示

## 重要：毎回必ずコンテキストに含めること
**デバッグ手順.mdを毎回必ずコンテキストに含めてください！**
このファイルには現在のデバッグ状況、問題点、対策、ワークフローが記載されています。

## プロジェクト概要
twitchTransFreeNeo - Twitchチャット翻訳ツール（GUI版）
- Python/tkinter製のデスクトップアプリケーション
- macOS/Windows対応
- PyInstallerでバイナリビルド

## 開発ルール
1. **バイナリビルドはGitHub Actionsで実行**（ローカルでbuild_mac.shを実行しない）
2. **デバッグ中はバージョン番号を変更しない**
3. **コミット後は必ずgit pushしてGitHub Actionsでビルド**
4. **macOS固有の問題に注意**（特にtkinter関連）

## ファイル構成
- run.py: エントリーポイント
- twitchTransFreeNeo/: メインパッケージ
  - gui/: GUI関連
    - main_window.py: メインウィンドウ
    - settings_window.py: 設定画面
    - chat_display.py: チャット表示
  - core/: コア機能
    - chat_monitor.py: チャット監視
    - translator.py: 翻訳エンジン
    - tts.py: 音声合成
  - utils/: ユーティリティ
    - config_manager.py: 設定管理

## 現在の状況
デバッグ手順.mdを参照してください。