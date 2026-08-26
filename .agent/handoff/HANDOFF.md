# HANDOFF - 2026-08-26

## 使用ツール
Claude Code (Opus 5)

## このセッションでやったこと

### プロジェクト移設
- Drive 内 `_Legacy/twitch/twitchTransFreeNeo_beta` → `~/_data/work/デモ・配信/twitchTransFreeNeo/` へ移動
- Claude Code の対話履歴150件も移行（`work/.agent/scripts/migrate_claude_history_2026-08-26_ttfn.py`）
- Drive アーカイブ先を新設: `マイドライブ/nishimura/program/twitchTransFreeNeo/`

### v0.2.28_Beta リリース（利用者2名のバグ報告への対応）
報告内容: チャットに翻訳結果ではなく `Error 500 (Server Error)...` が投稿される

**原因は3層**
1. Google 側の間欠障害 — `deep-translator` が使う `translate.google.com/m` が
   2026-08-24 頃からエラーページを返すようになった（実測10回中5回失敗）
2. アプリがその本文を検査せず翻訳結果として投稿
3. **それを translations.db にキャッシュ** → Google 復旧後も永久に再生
   （「27版にしても直らない」の正体はこれ）

**調査中に見つかった別の重大バグ**
- **言語検出が一度も機能していなかった** — `single_detection(text, api_key=None)` は
  APIキー必須で必ず例外を投げ、常に簡易ヒューリスティクスへ落ちていた。
  結果 es/pt/fr などラテン文字の言語がすべて `en` と誤判定されていた
- **翻訳キャッシュが保存されていなかった** — DB が相対パスで cwd 依存。
  実際 `Application Support/` に `config.json` はあるのに `translations.db` が無かった
- **システム診断が翻訳障害を検出できない** — 実翻訳せず、
  `translate.google.co.jp` に200が返るかだけ見ていた（利用者の「診断は全て正常」の理由）

## 現在の状態
- v0.2.28_Beta 公開済み（3OS ビルド成功・Pre-release）
  https://github.com/sayonari/twitchTransFreeNeo/releases/tag/v0.2.28_Beta
- 報告者2名（しらたまさん / Meruruさん）へ X で返信済み
- リポジトリ・作業ツリーともクリーン、Drive 同期済み

## 次にやること
1. **報告者からの反応を確認**（直ったかどうか）
2. **実機での接続テスト** — 起動確認のみで、実際の Twitch 接続は未検証。
   今回は接続処理にも手を入れているため配信前に一度確認したい
3. 未着手の監査対象: `gui/settings_dialog.py`(1580行) / `gui/diagnostics_dialog.py` /
   `core/youtube_auth.py` は今回ざっとしか見ていない

## 注意点・知見
- **翻訳エンドポイントは3段**: `clients5.google.com`（訳文＋検出言語を1回で取得・最も安定）
  → `translate.googleapis.com`(gtx) → `deep-translator`(/m)。各段でエラーページを検査
- **エラーページ判定は厳しめに** — `That's an error` 単体で弾くと
  「それはエラーです」の英訳など正当な翻訳まで消える。
  `Error 5xx (Server Error)` 形式か、`That's an error` + `That's all we know` の同時出現に限定
- **短時間に翻訳APIを連射すると 429** を食らう（テスト時に実際に発生）。
  検証は間隔を空けるか、別ホスト（clients5）を使う
- **`git add -A` に注意** — 未追跡の残骸ファイルを巻き込む。
  今回 `build_nuitka.py` が一度紛れ込んで push された（後で削除済み）
- **画面収録権限が無く `screencapture` が使えない** — GUI のスクショ検証は不可。
  起動の生存確認は `osascript` でプロセス名 "Flet" を見る方法で代替した
- コード監査では Codex(GPT-5.6 Sol) の査読も取った（7件中6件を反映、
  1件は応答形式についての誤指摘で実測により不採用）
