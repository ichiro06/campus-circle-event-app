# GitHub Copilot instructions

このリポジトリの開発ルールの正本は `AGENTS.md` と `docs/` である。本ファイルは GitHub Copilot（Chat、cloud agent、code review）の入口と補足であり、`AGENTS.md` と矛盾する場合は `AGENTS.md` を優先する。`AGENTS.md` 冒頭は「Codex向け」と記載しているが、GitHub Copilot も同じルールに従う。AI agent間の役割分担は `docs/development-workflow.md` の「14. AI coding agentの役割分担」に従う。

## 作業開始時

- `AGENTS.md` と、作業に関係する `docs/` を読んでから変更する。
- Notion は読めない前提で作業する。`docs/requirements.md` は Notion 要件の同期スナップショットであり、要件の追加・変更の根拠にしない。
- Issue に根拠（要件ID、docs の章）と完了条件がない場合は実装を始めず、不足を Issue または Pull Request に書いて止まる。
- 文書同士、または文書とコードが矛盾する場合は、片方に合わせて直さず、差異・根拠・影響を報告する。

## 変更範囲

- Issue で指定された範囲だけを変更する。依頼外のリファクタリング、依存の追加・更新、`.github/workflows/` の変更をしない。
- Authentication / Authorization、DB migration、API契約変更（`backend/openapi.json`）、依存更新は担当しない（`docs/development-workflow.md`「14. AI coding agentの役割分担」）。Issue でこれらが求められている場合も実装せず、Codex または Claude Code への引き継ぎが必要だと報告して止まる。
- Google / Apple / email のログイン成功だけで circle manager 権限を与える実装をしない。権限は `user_id` と `circle_id` の membership で判定する。
- テストを skip・削除して CI を通さない。テストを通すためだけに仕様を変えない。
- 秘密情報（`.env*`、token、PAT、秘密鍵、Supabase service role key、`CURSOR_SIGNING_SECRET` の実値）、非公開 Notion URL、ローカル絶対パスを commit しない。

## 検証

- `mobile/` を変更した場合: `cd mobile && npm ci && npm run api:check && npm run check`
- `backend/` を変更した場合: `AGENTS.md` と `CLAUDE.md` の FastAPI 検証手順に従う。
- iOS / Android の UI・native 挙動は CI だけで完了扱いにしない。Simulator / Emulator で確認できない場合は「未実施」と理由を書く。

## Pull Request

- Pull Request 本文は `.github/pull_request_template.md` に従う。
- merge しない。CI 成功や AI review を merge 承認とみなさない。

## Code review

- 指摘は「`AGENTS.md`・`docs/` との矛盾」「Authentication と Authorization の混同」「秘密情報の混入」「テスト不足」を優先する。
- 好みだけの指摘は避ける。
