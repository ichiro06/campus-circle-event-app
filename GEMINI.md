# GEMINI.md

このリポジトリの開発ルールの正本は `AGENTS.md` と `docs/` である。本ファイルは Gemini CLI の入口と補足であり、`AGENTS.md` と矛盾する場合は `AGENTS.md` を優先する。`AGENTS.md` 冒頭は「Codex向け」と記載しているが、Gemini も同じルールに従う。AI agent間の役割分担は `docs/development-workflow.md` の「14. AI coding agentの役割分担」に従う。

@AGENTS.md

## Gemini 固有の注意

- 既定の作業は調査・review である。明示的に実装を依頼された場合だけ、file を作成・編集・削除し、git の書き込み操作をする。
- 実装する場合は `main` から `gemini/<topic>` branch を作り、対象 path を明示して stage する。merge、force push、rebase、amend、`reset --hard`、`main` への push はしない。
- Notion は読めない前提で作業し、`docs/requirements.md` を要件の追加・変更の根拠にしない。
- 外部サービスの料金・仕様・policy を述べる場合は、公式文書の URL と確認日を付ける。確認できない情報は未確認と明記する。
- 情報の状態を「確定（現在有効）」「過去（置き換え済み）」「未確認（要確認・未決定）」で区別して報告する。
