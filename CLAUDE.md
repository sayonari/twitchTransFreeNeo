# CLAUDE.md - プロジェクト固有の指示

## プロジェクト概要
twitchTransFreeNeo - Twitchチャット翻訳ツール（GUI版）
- Python/Flet製のデスクトップアプリケーション（Flutter/Dartベース）
- macOS/Windows/Linux対応
- Nuitkaでバイナリビルド
- uvでパッケージ管理

## 技術スタック（2025年最新）
- **GUI**: Flet（Flutter/Dartベース、Material Design）
- **バイナリ化**: Nuitka（本番用）/ PyInstaller（開発用・高速）
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
- build_nuitka.py: Nuitkaビルドスクリプト（本番用）
- build_pyinstaller.py: PyInstallerビルドスクリプト（開発用・高速）
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

## タグ発行ルール（重要・必ず確認）

**タグを発行する前に、必ずユーザーに以下を確認すること：**

| タグ形式 | ビルドツール | 用途 | ビルド時間 |
|----------|--------------|------|------------|
| `v0.2.5_Beta` | Nuitka | **本番リリース** | 約30-60分 |
| `dev-v0.2.5_Beta` | PyInstaller | **開発/デバッグ用** | 約5-15分 |
| `test-v0.2.5_Beta` | PyInstaller | **テスト用** | 約5-15分 |

### タグ発行の判断基準
- **本番リリース (`v*`)**: ユーザーに配布する正式版。最適化されたNuitkaビルド。
- **開発版 (`dev-v*`)**: 開発中の動作確認用。高速ビルドで素早く確認。
- **テスト版 (`test-v*`)**: 特定機能のテスト用。高速ビルドで素早く確認。

### タグ発行コマンド例
```bash
# 本番リリース（Nuitka・時間がかかる）
git tag -a v0.2.5_Beta -m "リリース版" && git push origin v0.2.5_Beta

# 開発版（PyInstaller・高速）
git tag -a dev-v0.2.5_Beta -m "開発テスト版" && git push origin dev-v0.2.5_Beta

# テスト版（PyInstaller・高速）
git tag -a test-v0.2.5_Beta -m "テスト版" && git push origin test-v0.2.5_Beta
```

## リリース手順（重要）
1. コードをコミット・プッシュ
2. **【確認】上記タグ発行ルールを確認し、適切なタグ形式を選択**
3. タグを作成してプッシュ
4. GitHub Actionsでビルドが完了するのを待つ
5. **【必須確認】リリースページでPre-releaseになっているか確認**
   - https://github.com/sayonari/twitchTransFreeNeo/releases
   - ✅ 「Pre-release」ラベルが付いている
   - ✅ 「Latest」になっていない
   - ❌ なっていない場合: 手動で「Edit release」→「Set as a pre-release」にチェック
6. ワークフロー設定: `.github/workflows/build_nuitka.yml`
   - `prerelease: true` - Pre-releaseに設定
   - `make_latest: false` - Latestにしない

## 既知の改善点
- Fletへの移行により、macOS固有のtkinter問題から解放
- deep-translatorによる最新のGoogle翻訳API対応
- Nuitkaによる高速起動（2-3倍高速化）