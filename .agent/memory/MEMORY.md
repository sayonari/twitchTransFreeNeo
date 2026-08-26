# MEMORY

## プロジェクト概要
twitchTransFreeNeo は Python/Flet 製の Twitch/YouTube チャット翻訳ツール。Twitch向けに開発され、YouTube対応は後追いで追加されたためテスト不十分な箇所がある。

## 学習した知識・教訓

### sayonari.com のツール紹介ページ デザイン規約（OAuth設定ガイドなど）
参考: `https://www.sayonari.com/trans_asr/OAuth/YouTube/`（ユーザーが整備した正典）

**使用する共通CSS/JS（相対パスで読み込み）:**
- `../../css/modern.css` — CSS変数・ベーススタイル
- `../../css/components.css` — UIコンポーネント
- `../../js/i18n.js` — 国際化
- `../../js/common.js` — 共通（`.reveal` のスクロールアニメーション等）
- `<link rel="shortcut icon" href="../../img/favicon.ico">`

**使うCSS変数（`--` プレフィックス）:**
- スペーシング: `--space-xs`/`sm`/`md`/`lg`/`xl`/`2xl`/`3xl`
- 色: `--color-primary`, `--color-text-secondary`

**主要コンポーネントクラス:**
- `page-hero` + 内側 `.container` — ページ冒頭のヒーロー
- `main.container` — コンテンツラッパー（`max-width:900px;` 指定で読みやすく）
- `card` — カード型のコンテナ
- `notice notice-tip | notice-warning | notice-info | notice-success` — 情報ボックス
  - 中に `<span class="notice-icon">絵文字</span>` と `<div>...</div>` を並べる
- `ol.steps` → `li.step-item` → `.step-number`（空div、CSSで番号生成）＋`.step-body`（本文）
- ボタン: `btn btn-primary` / `btn-secondary` / `btn-ghost`、サイズは `btn-sm`
- 矢印の慣習: 外部リンク ボタン文末に「→」（例: "Google Cloud Console を開く →"）
- FAQ: `div.card` の中に `div.faq-item`（中身は `.faq-q` と `.faq-a`）
- スクロールアニメーション用に各セクションへ `reveal` クラスを付ける
- ユーティリティ: `mb-md/lg/xl`, `mt-md/lg`, `text-sm`, `text-muted`

**絵文字アイコン慣習（`notice-icon` 内）:**
- 📖 情報・導入
- 💡 ヒント・TIP
- ⚠️ 注意
- 🚨 最重要警告
- 🆕 新機能・新UI
- ✅ 完了・成功

**テーマ:** ライトテーマ、Google系カラー準拠、サンセリフ、読みやすさ重視の1カラム。

**How to apply:** sayonari.com 配下のツール紹介・設定ガイドHTMLを新規作成/修正する場合は、上記の外部CSS/JSを参照し、`notice`・`card`・`steps`・`btn` を使う。独自 `<style>` ブロックは最小限（ページ固有の微調整のみ）。
