# Campus Circle Event App

大学生向けのサークル検索・情報発信サービスです。初期製品はWebアプリケーションではなく、iOS・Android向けモバイルアプリケーションとして開発します。

## 正式構成

- Product client: React Native / Expo / TypeScript / Expo Router
- Product API: FastAPI / Python / SQLAlchemy / psycopg
- Local database: Docker Compose PostgreSQL 16
- Production database: Supabase PostgreSQL
- Authentication: Supabase Authの一般Google login、email/password、iOS版Sign in with Apple
- Image storage: Supabase Storage
- Authorization: FastAPI server checksとPostgreSQL上のcircle membership
- API hosting: Render
- Build / submit: EAS Build / EAS Submit
- Distribution: App Store / Google Play
- Source / CI: GitHub

大学Google accountを必須にせず、university domain restrictionとuniversity SSOは使いません。一般Google accountによるGoogle OAuthはinitial loginに含みます。

正式構成の詳細は `docs/architecture.md`、実装確認用の要件スナップショットは `docs/requirements.md` を参照してください。要件の一次情報はNotionの指定ページです。

## 現在の状態

正式構成は文書上で確定した段階で、製品機能はまだ実装していません。

- `mobile/`: React Native / Expoの正式製品client。現在はstatic initial screen
- `backend/`: 正式なFastAPI API基盤。現在はDocker Compose PostgreSQL 16に接続したread技術検証
- root Next.js: FastAPIのcircle / event read APIを表示するtechnical verification。製品機能は追加しない
- Supabase Auth / PostgreSQL / Storage: 未接続
- Google / email login: 未実装
- home recommendation、formal search、favorite、my page、circle management、report: 未実装
- ExpoからFastAPIへの接続: 未実装
- Render / EAS / App Store / Google Playのproject・配布設定: 未構築

正式な製品経路は `iOS / Android Expo app -> FastAPI -> PostgreSQL` です。Supabaseは本番PostgreSQL、Auth、Storageに使用し、FastAPIをRender、モバイルbuild・提出をEAS、配布をApp Store / Google Playで行います。

現在動作する `Next.js -> FastAPI -> PostgreSQL` のNext.js部分は表示確認用です。Next.jsとVercelは初期製品の構成に使用しません。

## 要件の参照先

今後の正式な要件定義は、Notionの「アプリ開発プロジェクトWiki」内にある「議事録」データベースの「第1回要件定義議事録」ページを参照します。`docs/requirements.md` は、そのNotionページをGitでレビューできるように同期したリポジトリスナップショットです。Notionページとリポジトリ文書に差異がある場合は、差異を確認・報告してから同期し、未確定のまま実装しません。

2026年8月に参照したCloud上のMarkdownは、同期時点を識別する履歴スナップショットであり、今後の要件更新の一次情報ではありません。

## ドキュメント

- Development rules: `AGENTS.md`
- Workflow / Slack / Notion / Codex: `docs/development-workflow.md`
- Actual macOS setup: `docs/development-setup.md`
- Requirements snapshot (synced from Notion): `docs/requirements.md`
- Requirements progress: `docs/requirements-progress.md`
- Requirements review / non-functional items: `docs/requirements-review-2026-08-21.md`
- 2026-09-15 decision report: `docs/requirements-decision-report-2026-09-15.md`
- Coding readiness / blockers: `docs/coding-readiness.md`
- Formal architecture: `docs/architecture.md`
- Screen flow / loading / offline: `docs/screen-flow.md`
- API contract: `docs/api-contract.md`
- Data dictionary / initial schema: `docs/data-dictionary.md`
- Non-functional requirements: `docs/non-functional-requirements.md`
- Authentication / authorization: `docs/authentication.md`
- Decision history: `docs/decisions.md`
- Mobile product client: `mobile/README.md`
- Collaboration guide: `CONTRIBUTING.md`

## 開発環境の起動

現在のcircle / event画面はFastAPIへ接続するため、先にDocker Desktopを起動し、FastAPIとPostgreSQLを起動します。

```bash
cd ~/Developer/campus-circle-event-app/backend
docker compose up -d --build
docker compose exec api alembic upgrade head
```

接続状態を確認します。

```bash
curl http://localhost:8000/health
```

`{"status":"ok","database":"connected"}` が返ったら、別のTerminalでExpoを起動します。

```bash
cd ~/Developer/campus-circle-event-app/mobile
npm ci
cp .env.example .env.local
npm start
```

実行先:

- iOS Simulator: `npm run ios`
- Android Emulator: `npm run android`
- FastAPI: http://localhost:8000
- FastAPI docs: http://localhost:8000/docs

ExpoからFastAPIへの通信はまだ実装していないため、現時点ではExpo画面とAPIを個別に確認します。Next.js技術検証を確認する場合だけ、ルートで`npm run dev`を実行します。

## 検査

モバイル:

```bash
cd mobile
npm run check
npx expo-doctor@latest
```

バックエンド（初回はuvで`.venv`を作成）:

```bash
cd backend
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r requirements-dev.lock
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
.venv/bin/alembic history
```

`alembic upgrade head`は正式な`app_private` schemaを作る。既存のread技術検証用`public.circles` / `public.events`は変更しない。共有・本番DBで`alembic downgrade`を実行しない。

`npm run check`はLint、TypeScript型検査、Jest testを実行します。Pull RequestではGitHub Actionsがmobile、FastAPIのLint・unit test、FastAPI / PostgreSQLの疎通、Next.js技術検証を分けて確認します。CIは現在の変更をcommit・pushした後に有効になります。

正式なSupabase Auth、本番DB、Storage、Render、EAS、store配布の手順はまだ未整備です。実装可能範囲と決定待ちの項目は`docs/coding-readiness.md`を確認し、external projectの値を推測で登録しないでください。

## 終了

ExpoのTerminalで`Control + C`を押した後、FastAPIとPostgreSQLのcontainerを停止します。

```bash
cd ~/Developer/campus-circle-event-app/backend
docker compose down
```

通常の `docker compose down` はPostgreSQL volumeを削除しません。`docker compose down -v` は明示的なdata削除依頼なしに実行しないでください。
