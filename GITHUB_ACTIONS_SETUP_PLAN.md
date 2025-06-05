# GitHub Actions自動ビルド環境構築計画

## 概要
twitchTransFreeNeoをGitHub Actionsを使用してWindows、macOS、Linux向けに自動ビルドし、リリース配布する環境を構築する。

## 参考資料
- twitchTransFreeNext/build.py: PyInstallerビルドスクリプト
- twitchTransFreeNext/.github/workflows/build.yml: GitHub Actionsワークフロー
- twitchTransFreeNext/.gitignore: 無視ファイル設定

## 実装計画

### 1. ファイル構成の整理

#### 1.1 バージョン管理
- **現状**: `twitchTransFreeNeo/__init__.py`に`__version__ = "1.0.0"`で定義済み
- **対応**: build.pyでこのバージョン情報を読み取る仕組みを実装

#### 1.2 エントリーポイントの確認
- **現状**: `run.py`がメインエントリーポイント
- **対応**: build.pyで`run.py`をビルド対象に設定

#### 1.3 アイコンファイル
- **現状**: `twitchTransFreeNext/icon.ico`を参照
- **対応**: アイコンファイルをプロジェクトルートにコピーまたは作成

### 2. 必要ファイルの作成

#### 2.1 build.py
```python
# 以下の機能を実装
- バージョン情報取得（twitchTransFreeNeo/__init__.py）
- OS別ビルド処理（Windows/Linux/macOS）
- PyInstallerオプション設定
- アイコン設定
- 出力ファイル名の統一
```

#### 2.2 .github/workflows/build.yml
```yaml
# 以下の機能を実装
- タグプッシュ時の自動実行（v*パターン）
- マトリックスビルド（windows/linux/macos）
- Python環境のセットアップ
- 依存関係のインストール
- ビルド実行
- アーカイブ作成
- リリースへの自動アップロード
```

#### 2.3 .gitignore
```
# macOS対応の無視設定
- .DS_Store
- ._*
- .AppleDouble
- .LSOverride
# ビルド関連
- dist/
- build/
- *.spec
# 仮想環境
- env_neo/
# その他
```

### 3. 実装手順

#### ステップ1: .gitignoreの整備
- [x] macOS固有ファイルの無視設定
- [x] Python関連の無視設定
- [x] ビルド成果物の無視設定

#### ステップ2: アイコンファイルの準備
- [ ] icon.icoファイルをプロジェクトルートに配置
- [ ] アイコンファイルの存在確認

#### ステップ3: build.pyの作成
- [ ] twitchTransFreeNext/build.pyを参考に作成
- [ ] バージョン情報読み取り機能
- [ ] OS別ビルド設定
- [ ] エントリーポイントをrun.pyに設定

#### ステップ4: GitHub Actionsワークフローの作成
- [ ] .github/workflows/ディレクトリ作成
- [ ] build.ymlファイル作成
- [ ] マトリックスビルド設定
- [ ] 依存関係インストール設定

#### ステップ5: GitHubリポジトリの準備
- [ ] GitHubリポジトリの作成
- [ ] ローカルgitリポジトリの初期化
- [ ] 初回コミット・プッシュ

#### ステップ6: テスト・デバッグ
- [ ] タグ作成によるビルドテスト
- [ ] 各OS向けバイナリの動作確認
- [ ] リリース自動作成の確認

### 4. 注意事項

#### 4.1 PyInstaller関連
- **Windows**: ブートローダー再ビルドが必要な場合がある
- **macOS**: M1/Intel両対応、.commandファイル形式
- **Linux**: 静的リンク対応

#### 4.2 依存関係
- requirements.txtの整備
- プラットフォーム固有の依存関係の処理
- cacert.pemファイルの自動ダウンロード

#### 4.3 設定ファイル
- config.jsonのサンプル作成
- ビルド後のファイル配置

### 5. 期待される成果物

#### 5.1 ビルド成果物
- `twitchTransFreeNeo_v1.0.0_windows.zip`
- `twitchTransFreeNeo_v1.0.0_linux.tar.gz`
- `twitchTransFreeNeo_v1.0.0_macos_M1.tar.gz`
- `twitchTransFreeNeo_v1.0.0_macos_Intel.tar.gz`

#### 5.2 各アーカイブ内容
- メイン実行ファイル
- config.jsonサンプル
- README（使用方法）

## 実装開始

以下の順序で実装を開始する：
1. .gitignoreの整備
2. アイコンファイルの準備  
3. build.pyの作成
4. GitHub Actionsワークフローの作成
5. GitHubリポジトリのセットアップ