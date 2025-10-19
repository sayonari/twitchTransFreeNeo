# リリースチェックリスト

## 📋 リリース前の確認事項

### コード品質
- [ ] ローカルでテスト実行が正常に動作する
- [ ] バージョン番号が更新されている
  - [ ] `twitchTransFreeNeo/__init__.py`
  - [ ] `pyproject.toml`
- [ ] コミットメッセージが適切である

### GitHub Actions設定の確認
- [ ] `.github/workflows/build_nuitka.yml`の設定を確認
  - [ ] `prerelease: true` が設定されている
  - [ ] `make_latest: false` が設定されている
  - [ ] アーカイブに実行バイナリのみが含まれる設定になっている

### リリース実行
1. [ ] コードをコミット
   ```bash
   git add -A
   git commit -m "適切なコミットメッセージ"
   ```

2. [ ] GitHubにプッシュ
   ```bash
   git push origin main
   ```

3. [ ] タグを作成してプッシュ
   ```bash
   git tag -a vX.X.X_Beta -m "バージョンX.X.X Beta"
   git push origin vX.X.X_Beta
   ```

4. [ ] GitHub Actionsでビルドが開始されたことを確認
   - https://github.com/sayonari/twitchTransFreeNeo/actions

5. [ ] ビルドが完了するのを待つ（約30-60分）

## ⚠️ 【最重要】リリース後の確認

### Pre-releaseの確認（必須）
- [ ] リリースページを開く
  - https://github.com/sayonari/twitchTransFreeNeo/releases

- [ ] 新しいリリースが以下の状態になっているか確認
  - [ ] ✅ 「Pre-release」ラベルが付いている
  - [ ] ✅ 「Latest」になっていない
  - [ ] ✅ リリース名に「Beta」が含まれている

- [ ] ❌ Pre-releaseになっていない場合
  1. 「Edit release」ボタンをクリック
  2. 「Set as a pre-release」にチェックを入れる
  3. 「Update release」をクリック

### アーカイブ内容の確認
- [ ] 各プラットフォームのアーカイブをダウンロード
  - [ ] macOS (arm64)
  - [ ] macOS (x86_64)
  - [ ] Windows
  - [ ] Linux

- [ ] アーカイブに実行バイナリのみが含まれている
  - [ ] ❌ 余分なファイル（.pyファイル、__pycache__等）が含まれていない
  - [ ] ✅ 実行バイナリのみが含まれている

### 動作確認
- [ ] 少なくとも1つのプラットフォームで動作確認
- [ ] 設定ファイルが実行バイナリと同じディレクトリに作成される
- [ ] 基本的な機能が動作する

## 🔍 問題が発生した場合

### Pre-releaseになっていない
→ 手動で「Edit release」→「Set as a pre-release」にチェック

### アーカイブに余分なファイルが含まれている
→ `.github/workflows/build_nuitka.yml`の「Create Archive」セクションを確認

### ビルドが失敗する
→ GitHub Actionsのログを確認
→ Iconファイル等の無効なファイル名がないか確認

## 📝 記録

今回のリリース: v________________

確認者: ________________

確認日時: ________________

Pre-release設定: [ ] 確認済み

備考:
