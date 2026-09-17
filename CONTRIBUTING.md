# 共同開発ガイド

このリポジトリでは、iOS・Android向けExpoアプリ、FastAPI、PostgreSQLを共同開発する。製品Webは初期対象ではなく、ルートNext.jsはAPI表示の技術検証だけに使う。

## 作業前

1. `AGENTS.md` と対象に関係する `docs/` を読む。
2. 要件はNotionの「第1回要件定義議事録」と要件DBで、承認状態を確認する。
3. `git status --short --branch` を確認し、他の人の未コミット変更を上書きしない。
4. `main`から作業用branchを作る。同じbranchを複数人で直接編集しない。
5. 不明なプロダクト判断は実装せず、NotionまたはGitHub Issueで要確認にする。

## 変更とレビュー

- 1つのPull Requestには、レビュー可能な1つの目的を持たせる。
- Pull Requestに根拠となる要件ID、Notionページ、設計文書、GitHub Issueを記載する。
- AuthenticationとAuthorizationを分け、Google login成功だけでcircle manager権限を付与しない。
- `.env`、access token、PAT、SSH秘密鍵、Supabase service role key、署名鍵をcommitしない。
- 仕様・構成・手順を変えた場合は、関係する文書とdecision historyも更新する。

## ローカル確認

モバイル:

```bash
cd mobile
npm ci
cp .env.example .env.local
npm run check
```

APIとPostgreSQL:

```bash
cd backend
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r requirements-dev.lock
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
.venv/bin/alembic history
docker compose up -d --build
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/api/circles
curl --fail http://localhost:8000/api/events
docker compose down
```

`requirements.txt`または`requirements-dev.txt`を変更した場合は、uvで対応するlockを再生成し、入力とlockを同じPull Requestに含める。正式schemaは既存の初回Alembic revisionを基準に追加revisionで変更し、現在のtechnical-verification tableを正式schemaへ自動移行しない。

Next.js技術検証を変更した場合だけ:

```bash
npm ci
npm run lint
npm run build
```

Pull Requestでは同じ基礎検査をGitHub Actionsが実行する。iOS・Android固有のUIやnative挙動は、CIだけで完了扱いにせずSimulator / Emulatorまたは実機で確認する。
