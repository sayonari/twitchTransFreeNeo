# 変更履歴

## v0.1.2_Beta - 2025-01-13

### 変更内容
- プロジェクト構造の整理
  - twitchTransFreeNextフォルダとその内容を削除（参照用のコピーだったため不要）
  - 開発ドキュメントをdocs/フォルダに移動
    - CLAUDE.md
    - GITHUB_ACTIONS_SETUP_PLAN.md
    - setup_instructions.md
    - twitchTransFreeNext_詳細分析レポート.md
  - tmpフォルダと古い音声ファイルを削除
- ルートフォルダをクリーンアップして見通しを改善

## v0.1.1_Beta - 2025-01-13

### 変更内容
- テスト用ファイルの削除
  - minimal_test.py, simple_gui.py, standalone_gui.py, test_gui.py, test_startup.py
  - test_config.json, test_translations.db
  - GUI内のテスト関連ファイル（simple_chat_display.py, simple_main_window.py, simple_settings.py, main_window_backup.py）
- README.mdの開発者情報を修正
  - 開発者がsayonari (@husband_sayonari_omega)であることを明記
  - twitchTransFreeNextも同一開発者によるものであることを明記
  - 協力者として妻のさぁたんを記載

## v0.1.0_Beta - 2025-01-12

### 初回リリース
- twitchTransFreeNeoの初回ベータ版リリース
- CUI版twitchTransFreeNextをGUI化
- tkinterによる直感的なインターフェース
- リアルタイム翻訳機能
- 設定画面の実装
- 翻訳履歴の保存機能