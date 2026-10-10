# CLAUDE.md

このリポジトリの開発ルールの正本は `AGENTS.md` と `docs/` である。本ファイルは Claude Code（ローカル・クラウド共通）の入口と補足であり、`AGENTS.md` と矛盾する場合は `AGENTS.md` を優先する。`AGENTS.md` 冒頭は「Codex向け」と記載しているが、Claude Code も同じルールに従う。

@AGENTS.md

## 情報源の優先順位（AGENTS.md / docs/development-workflow.md より）

1. 製品要件・タスク・承認状態: Notion「第1回要件定義議事録」
2. 技術仕様・アーキテクチャ・認証認可・開発ルール: `AGENTS.md` と `docs/`
3. 実装事実: Git 管理されたコード、`backend/openapi.json`
4. Slack・AI の回答: 正式情報ではない

Notion を読めない環境（クラウドセッションで Notion connector が未接続の場合等）では、`docs/requirements.md` を読み取り・診断の範囲でのみ使い、要件変更や実装の根拠にしない。

## コマンド早見表

| 対象 | 検証 |
| --- | --- |
| mobile/（製品client） | `npm ci` → `npm run api:check` → `npm run check`（lint + `tsc --noEmit` + jest）。ローカルでは `npx expo-doctor@latest` も |
| backend/（製品API） | `.venv/bin/ruff check .` / `.venv/bin/ruff format --check .` / `.venv/bin/pytest` / `.venv/bin/python generate_openapi.py --check openapi.json` / `.venv/bin/alembic history` |
| ルート Next.js（技術検証のみ） | 変更時のみ `npm ci` → `npm run lint` → `npm run build` |

- backend の初回: `uv venv .venv --python 3.13` → `uv pip install --python .venv/bin/python -r requirements-dev.lock`。ホストの `python3` は使わない。
- 正式 Circle API のテスト・起動には 32 bytes 以上の `CURSOR_SIGNING_SECRET` が必要（実値は Git に置かない。テストでは CI と同じ test 専用値を使う）。
- PostgreSQL integration test は `RUN_POSTGRES_INTEGRATION=1` と隔離された `*_test` DB が必要。未設定だと skip される。
- 正式 endpoint を変えたら `backend/` で `.venv/bin/python generate_openapi.py --output openapi.json` → `cd ../mobile && npm run api:generate` で生成物を更新し差分を review する（docs/development-setup.md）。

## コーディング規約

- `.editorconfig`（LF、TS/JS/MD/YAML は 2 space、Python は 4 space）、ruff（line-length 100、py313）、ESLint（root: next、mobile: expo）に従う。
- 文書は日本語＋技術用語は英語表記の既存スタイルに合わせる。
- commit メッセージの規則は文書化されていない（未確認）。既存履歴は `type(scope): summary` 形式。
- branch 名は `docs/development-workflow.md`「14. AI coding agentの役割分担」に従い、Claude Code は `claude/<topic>` を使う。

## Git 運用（Claude Code）

- 変更前に `git status --short --branch`、HEAD、origin との ahead/behind を確認する。
- `main` へ直接 commit / push しない。作業用 branch で行う。
- stage は対象パスを明示し、`git add -A` / `git add .` を使わない。
- ユーザーの未コミット変更・未追跡ファイルを破棄・上書きしない。
- force push、`reset --hard`、`git clean`、履歴書き換えは明示的な許可なしに行わない。
- merge はユーザーの明示的な指示なしに行わない。merge 方式・auto-merge は AGENTS.md に従う。
- Codex と同じ worktree・同じ変更を同時に編集しない。
- クラウドセッションの commit author email が AGENTS.md の noreply 規則を満たすかは未確認。

## 禁止事項（AGENTS.md・docs/coding-readiness.md・README より）

- 秘密情報（`.env*`、token、PAT、秘密鍵、Supabase service role key、署名鍵）の commit・文書掲載
- 非公開 Notion URL / page ID、ローカル絶対パスの追跡対象ファイルへの記録（公開 repository）
- `.git/info/exclude` でローカル専用にしているファイルの commit
- `docker compose down -v`、共有・本番 DB での `alembic downgrade`
- `npm audit fix --force`、検証なしの Expo major update
- Supabase / Render / EAS / store への仮 owner・仮 identifier・推測した secret の登録
- 不明な仕様の推測実装、テストを通すためだけの仕様変更

## 完了条件

- 変更範囲に対応する上記の検証を実行し、結果を報告する。実行できなかった検証は「未実施」とし理由を書く。
- iOS / Android の UI・native 挙動は CI だけで完了扱いにせず、Simulator / Emulator / 実機確認が必要（CONTRIBUTING.md）。対象環境で実行できない場合は、理由とともに「未実施」として報告し、実行可能な環境へ引き継ぐ。
- 仕様・構成・手順を変えた場合は関連 docs と `docs/decisions.md` を更新する。
- 報告は「確認した事実 / 変更内容 / 検証結果 / 未確認・未実施 / 人間の判断が必要な事項」を分ける。

## ローカルとクラウドの違い

- ローカルの untracked / ignored file（`.codex/`、`backend/.env`、`mobile/.env.local` 等）、user settings、memory がクラウドへ自動的に引き継がれるとは仮定しない。必要な file・environment variable・authentication は、secret value を表示せず、対象環境で存在を確認する。
- Docker Compose、iOS Simulator、Android Emulator、`expo-doctor` 等は、クラウドという理由だけで実行不能と決めない。対象環境の能力・設定を確認して実行可能な検証は実行し、未実施の検証と GitHub Actions CI の検証結果を区別して報告する。
- ローカル Codex の Notion MCP 設定・認証が Claude Code のクラウドセッションへ自動的に引き継がれるとは仮定しない。対象 Claude Code session で connector / MCP 接続と対象 Notion page へのアクセス可否を確認する。
