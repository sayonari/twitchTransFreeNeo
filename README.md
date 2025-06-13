# twitchTransFreeNeo

Next Generation Twitch Chat Translator with GUI

## 概要

twitchTransFreeNeoは、Twitchのチャット翻訳を行うGUIアプリケーションです。従来のCUI版「twitchTransFreeNext」をベースに、使いやすいGUIインターフェースを提供します。

## 主な機能

### 核心機能
- **リアルタイム翻訳**: Twitchチャットメッセージの自動翻訳
- **複数翻訳エンジン対応**: Google翻訳、DeepL翻訳
- **言語自動検出**: メッセージの言語を自動判定
- **翻訳履歴保存**: SQLiteデータベースによる効率的な翻訳キャッシュ

### GUI機能
- **直感的な設定画面**: 全設定をGUIで簡単設定
- **リアルタイムチャット表示**: 原文と翻訳文の並列表示
- **検索・フィルタ機能**: 言語別フィルタ、キーワード検索
- **統計情報表示**: 翻訳数、言語別統計
- **テーマ切り替え**: ライト/ダークモード対応

### 高度な機能
- **フィルタリング**: ユーザー、言語、テキストパターンによる無視設定
- **エモート除去**: Twitchエモート、Unicode絵文字の自動除去
- **TTS対応**: 入力・出力テキストの音声読み上げ（gTTS、CeVIO対応）
- **設定の即座反映**: 再起動不要で設定変更が適用

## インストール

### バイナリ版（推奨）

1. [Releases](https://github.com/sayonari/twitchTransFreeNeo/releases)から最新版をダウンロード
2. お使いのOSに対応したファイルを選択：
   - Windows: `twitchTransFreeNeo_vX.X.X_windows.zip`
   - macOS (Apple Silicon): `twitchTransFreeNeo_vX.X.X_macos_M1.tar.gz`
   - macOS (Intel): `twitchTransFreeNeo_vX.X.X_macos_Intel.tar.gz`
   - Linux: `twitchTransFreeNeo_vX.X.X_linux.tar.gz`
3. ダウンロードしたファイルを展開
4. 実行ファイルを起動

### ソースコードから実行

#### 必要環境
- Python 3.8以上
- tkinter（通常Pythonに含まれています）

#### 手順

1. **リポジトリのクローン**
```bash
git clone https://github.com/sayonari/twitchTransFreeNeo.git
cd twitchTransFreeNeo
```

2. **依存関係のインストール**
```bash
pip install -r requirements.txt
```

3. **アプリケーションの起動**
```bash
python run.py
```

## 使用方法

### 初期設定

1. **OAuthトークンの取得**
   - https://www.sayonari.com/trans_asr/ttfn_oauth.html でOAuthトークンを取得

2. **基本設定**
   - 「設定」ボタンから設定画面を開く
   - 必須項目を入力：
     - Twitchチャンネル名
     - 翻訳bot用ユーザー名
     - OAuthトークン

3. **翻訳設定**
   - ホーム言語（通常は日本語 'ja'）
   - 外国語（通常は英語 'en'）
   - 翻訳エンジン（Google または DeepL）

### 基本操作

1. **接続開始**
   - 「接続開始」ボタンでTwitchチャンネルに接続
   - 接続状態がステータスバーに表示されます

2. **チャット監視**
   - チャットメッセージがリアルタイムで表示
   - 翻訳結果も自動的に表示されます

3. **フィルタリング**
   - 言語フィルター、検索機能で表示を絞り込み可能
   - 設定画面で無視ユーザー、無視言語を設定可能

## 設定項目詳細

### 必須設定
- **Twitchチャンネル名**: 監視対象のチャンネル
- **翻訳bot用ユーザー名**: 翻訳結果投稿用のユーザー名
- **OAuthトークン**: Twitch API認証用トークン

### 翻訳設定
- **ホーム言語**: メイン言語（翻訳先言語）
- **外国語**: サブ言語（ホーム言語以外の翻訳先）
- **翻訳エンジン**: Google翻訳 または DeepL
- **Google翻訳サーバー**: translate.google.co.jp など
- **DeepL APIキー**: DeepL使用時に必要

### フィルタリング設定
- **無視する言語**: 翻訳しない言語リスト
- **無視するユーザー**: 無視するユーザーリスト
- **無視するテキスト**: 無視するテキストパターン
- **削除する単語**: メッセージから削除する単語

### TTS設定
- **入力/出力TTS**: 音声読み上げの有効/無効
- **TTS種類**: gTTS（Google） または CeVIO
- **読み上げ文字数制限**: 長文の省略設定
- **読み上げ言語制限**: 特定言語のみ読み上げ

### GUI設定
- **テーマ**: ライト/ダークモード
- **フォントサイズ**: 表示フォントサイズ
- **ウィンドウサイズ**: 初期ウィンドウサイズ

## 技術仕様

### アーキテクチャ
- **GUI**: tkinter
- **非同期処理**: asyncio
- **翻訳API**: aiohttp + async-google-trans-new / deepl-translate
- **チャット接続**: TwitchIO
- **データベース**: SQLite (aiosqlite)

### ファイル構成
```
twitchTransFreeNeo/
├── main.py                 # メインエントリーポイント
├── core/                   # 核心機能
│   ├── translator.py       # 翻訳エンジン
│   ├── chat_monitor.py     # チャット監視
│   └── database.py         # データベース管理
├── gui/                    # GUI関連
│   ├── main_window.py      # メインウィンドウ
│   ├── settings_window.py  # 設定画面
│   └── chat_display.py     # チャット表示
└── utils/                  # ユーティリティ
    └── config_manager.py   # 設定管理
```

## トラブルシューティング

### 接続できない場合
1. OAuthトークンが正しいか確認
2. チャンネル名にスペースや特殊文字がないか確認
3. インターネット接続を確認
4. デバッグモードを有効にしてログを確認

### 翻訳されない場合
1. 翻訳エンジンの設定を確認
2. 無視言語設定を確認
3. フィルタリング設定を確認
4. DeepL使用時はAPIキーを確認

### パフォーマンスの問題
1. 翻訳履歴データベースが大きくなりすぎた場合は自動削除される
2. 表示メッセージ数は1000件に制限される
3. TTS使用時は読み上げ文字数制限を調整

## ライセンス

このソフトウェアは、元のtwitchTransFreeNextと同様のライセンスで提供されます。

## 開発者情報

- **開発者**: sayonari (@husband_sayonari_omega)
- **ベース**: twitchTransFreeNext（CUI版）も私が開発したもので、それをGUI化したものです
- **協力者**: さぁたん（私の妻）
- **バージョン**: 0.1.2_Beta

## 謝辞

- TwitchIO、Google翻訳API、DeepL APIの開発者の皆様
- テスト・フィードバックをいただいた皆様
- 妻のさぁたんのサポートに感謝