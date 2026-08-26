#!/bin/bash
# twitchTransFreeNeo — 整理済みデータを Google Drive（正本・アーカイブ）へ同期する
#
# 保存先: マイドライブ/nishimura/program/twitchTransFreeNeo/
#   01_受領書類・メール/ ← .references/（利用者からの不具合報告・スクリーンショット）
#   02_成果物/           ← .output/（修正報告 HTML・返信文案など）
#   03_記録/             ← .spec/ .agent/（設計・メモリ・ハンドオフ）
#
# ソースコードは GitHub（github.com/sayonari/twitchTransFreeNeo）が正本のため同期しない．
# .venv/ dist/ translations.db config.json（OAuthトークンを含む）も同期しない．
# 作業の区切り（成果物完成・push・タグ発行・セッション終了）ごとに実行する．
set -u
SRC="$(cd "$(dirname "$0")/../.." && pwd)"
DST="$HOME/Library/CloudStorage/GoogleDrive-sayonari@gmail.com/マイドライブ/nishimura/program/twitchTransFreeNeo"

mkdir -p "$DST/01_受領書類・メール" "$DST/02_成果物" "$DST/03_記録"

RSYNC=(rsync -a --delete --exclude '.DS_Store')

# .references/ は存在する場合のみ同期する
if [ -d "$SRC/.references" ]; then
  "${RSYNC[@]}" "$SRC/.references/" "$DST/01_受領書類・メール/"
fi

"${RSYNC[@]}" "$SRC/.output/" "$DST/02_成果物/"
"${RSYNC[@]}" "$SRC/.spec/"   "$DST/03_記録/spec/"
"${RSYNC[@]}" --exclude 'scripts/' "$SRC/.agent/" "$DST/03_記録/agent/"

# 変更履歴だけはソースから例外的に持っていく（何をいつ直したかの記録として）
cp "$SRC/CHANGELOG.md" "$DST/03_記録/CHANGELOG.md" 2>/dev/null || true

echo "同期しました → $DST"
du -sh "$DST" 2>/dev/null
