# CLAUDE.md - プロジェクト固有の指示

## プロジェクト概要
twitchTransFreeNeo - Twitchチャット翻訳ツール（GUI版）
- Python/Flet製のデスクトップアプリケーション（Flutter/Dartベース）
- macOS/Windows/Linux対応
- PyInstallerでバイナリビルド
- uvでパッケージ管理

## 技術スタック
- **GUI**: Flet（Flutter/Dartベース、Material Design）
- **バイナリ化**: PyInstaller
- **パッケージ管理**: uv（高速、Rustベース）
- **翻訳エンジン**: deep-translator（Google翻訳、DeepL対応）
- **非同期処理**: asyncio, aiohttp

---

## チェックリスト（毎回確認）

### コミット前チェック
- [ ] `__version__` が適切に更新されているか（`twitchTransFreeNeo/__init__.py`）
- [ ] 構文エラーがないか（`python -m py_compile` で確認）

### タグ発行前チェック
- [ ] **ユーザーにタグ発行の確認を取ったか**
- [ ] バージョン番号がタグと一致しているか
- [ ] コミット・プッシュが完了しているか

### リリース後チェック
- [ ] GitHub Actionsのビルドが成功したか
- [ ] リリースページで「Pre-release」になっているか
- [ ] 生成されたファイル名のバージョンが正しいか

---

## タグ発行ルール

| タグ形式 | 用途 | ビルド時間 |
|----------|------|------------|
| `v0.2.8_Beta` | 本番リリース | 約5-10分 |

```bash
# タグ発行コマンド
git tag -a v0.2.8_Beta -m "リリース説明" && git push origin v0.2.8_Beta
```

---

## ファイル構成
- `run.py`: エントリーポイント
- `build_pyinstaller.py`: PyInstallerビルドスクリプト
- `pyproject.toml`: プロジェクト設定（uv管理）
- `twitchTransFreeNeo/`: メインパッケージ
  - `__init__.py`: バージョン情報（**タグ発行前に必ず更新**）
  - `gui/`: GUI関連（Flet）
  - `core/`: コア機能（chat_monitor, translator, tts）
  - `utils/`: ユーティリティ（config_manager）

---

## 開発ワークフロー
1. `uv add <パッケージ名>` - パッケージ追加
2. `uv sync` - 依存関係同期
3. `uv run python run.py` - ローカル実行
4. `uv run python build_pyinstaller.py` - ローカルビルド（テスト用）
5. GitHub Actionsで本番ビルド（タグpush時）

---

## 開発経緯・技術的判断の記録

### 2025年11月 - Nuitka廃止、PyInstaller採用

**経緯**: Nuitkaでビルドした際に以下の問題が発生
1. **SSL証明書エラー**: Google翻訳に接続できない（`--include-package-data=certifi`でも解決せず）
2. **設定ファイル消失**: Windowsで設定が再起動時に消える
3. **ビルド時間**: 30-60分かかる

**決定**: PyInstallerに完全移行
- SSL証明書: `--collect-data=certifi` で解決
- 設定保存: 正常に動作
- ビルド時間: 約5-10分

### GUI移行: tkinter → Flet

**経緯**: tkinterはmacOSでの問題が多かった
- macOS App Translocation問題
- 日本語入力の問題

**決定**: Fletに移行（Flutter/Dartベース、クロスプラットフォーム対応）

### 設定ファイルの保存先

**問題**: Windowsバイナリ実行時に設定が消える

**解決策** (`config_manager.py`):
1. 実行ファイルと同じディレクトリに保存を試みる
2. 書き込み不可の場合はユーザーデータディレクトリにフォールバック
   - Windows: `%APPDATA%\twitchTransFreeNeo`
   - macOS: `~/Library/Application Support/twitchTransFreeNeo`
   - Linux: `~/.config/twitchTransFreeNeo`

---

## 既知の注意点

1. **SSL証明書**: PyInstallerビルド時に `--collect-data=certifi` が必須
2. **バージョン番号**: タグ発行前に `__init__.py` の `__version__` を必ず更新
3. **Pre-release設定**: リリースページで必ず確認（自動設定されるはずだが要確認）

---

## リンク
- **リポジトリ**: https://github.com/sayonari/twitchTransFreeNeo
- **リリースページ**: https://github.com/sayonari/twitchTransFreeNeo/releases
- **GitHub Actions**: https://github.com/sayonari/twitchTransFreeNeo/actions
