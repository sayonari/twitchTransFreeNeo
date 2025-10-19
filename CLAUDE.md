# CLAUDE.md - プロジェクト固有の指示

## プロジェクト概要
twitchTransFreeNeo - Twitchチャット翻訳ツール（GUI版）
- Python/Flet製のデスクトップアプリケーション（Flutter/Dartベース）
- macOS/Windows/Linux対応
- Nuitkaでバイナリビルド
- uvでパッケージ管理

## 技術スタック（2025年最新）
- **GUI**: Flet（Flutter/Dartベース、Material Design）
- **バイナリ化**: Nuitka（高速起動、ソースコード保護）
- **パッケージ管理**: uv（高速、Rustベース）
- **翻訳エンジン**: deep-translator（Google翻訳、DeepL対応）
- **非同期処理**: asyncio, aiohttp

## 開発ルール
1. **バイナリビルドはGitHub Actionsで実行**（ローカルビルドは不要）
2. **デバッグ中はバージョン番号を変更しない**
3. **コミット後は必ずgit pushしてGitHub Actionsでビルド**
4. **tkinterの問題から解放**（Fletを使用しているため）

## ファイル構成
- run.py: エントリーポイント
- build_nuitka.py: Nuitkaビルドスクリプト
- pyproject.toml: プロジェクト設定（uv管理）
- twitchTransFreeNeo/: メインパッケージ
  - gui/: GUI関連（Flet）
    - main_window_flet.py: メインウィンドウ（Flet版）
    - settings_dialog.py: 設定ダイアログ（Flet版）
    - ※ 旧tkinter版（main_window.py等）は保持されていますが非推奨
  - core/: コア機能
    - chat_monitor.py: チャット監視
    - translator.py: 翻訳エンジン（deep-translator使用）
    - tts.py: 音声合成
  - utils/: ユーティリティ
    - config_manager.py: 設定管理

## 開発ワークフロー
1. **パッケージ追加**: `uv add <パッケージ名>`
2. **依存関係同期**: `uv sync`
3. **ローカル実行**: `uv run python run.py`
4. **ローカルビルド（テスト用）**: `uv run python build_nuitka.py`
5. **本番ビルド**: GitHub Actionsで自動実行（タグpush時）

## リリース手順（重要）
1. コードをコミット・プッシュ
2. タグを作成してプッシュ: `git tag -a vX.X.X_Beta -m "説明" && git push origin vX.X.X_Beta`
3. GitHub Actionsでビルドが完了するのを待つ
4. **【必須確認】リリースページでPre-releaseになっているか確認**
   - https://github.com/sayonari/twitchTransFreeNeo/releases
   - ✅ 「Pre-release」ラベルが付いている
   - ✅ 「Latest」になっていない
   - ❌ なっていない場合: 手動で「Edit release」→「Set as a pre-release」にチェック
5. ワークフロー設定: `.github/workflows/build_nuitka.yml`
   - `prerelease: true` - Pre-releaseに設定
   - `make_latest: false` - Latestにしない

## 既知の改善点
- Fletへの移行により、macOS固有のtkinter問題から解放
- deep-translatorによる最新のGoogle翻訳API対応
- Nuitkaによる高速起動（2-3倍高速化）