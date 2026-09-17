# Campus Circle Event App: Agent Guide

このファイルは、リポジトリ全体で作業するCodex向けの共通ルールです。

## 作業開始時

1. 最初にこの `AGENTS.md` を読む。
2. タスクに関連する `docs/` 内の文書を読む。
   - 開発運用とツール連携: `docs/development-workflow.md`
   - 実際に構築・確認した開発環境: `docs/development-setup.md`
   - 正式要件の同期スナップショット: `docs/requirements.md`（一次情報はNotion）
   - 正式構成: `docs/architecture.md`
   - 認証・認可: `docs/authentication.md`
   - 画面・通信状態: `docs/screen-flow.md`
   - API契約: `docs/api-contract.md`
   - データ辞書・初期schema: `docs/data-dictionary.md`
   - 非機能要件: `docs/non-functional-requirements.md`
   - 技術・設計上の決定: `docs/decisions.md`
   - 要件定義の進捗: `docs/requirements-progress.md`
   - 要件レビュー: `docs/requirements-review-2026-08-21.md`
   - 詳細決定報告: `docs/requirements-decision-report-2026-09-15.md`
   - コーディング開始準備: `docs/coding-readiness.md`
3. `git status`、対象ファイル、設定ファイル、既存テストを確認してから変更する。
4. 会話履歴より、現在のコード、設定、リポジトリ内文書を優先する。
5. 開発端末、導入済みツール、起動・接続確認の実績は `docs/development-setup.md` を基準にする。

## 開発情報源

- 詳細な情報源、承認フロー、Slack・Notion・Codex連携は `docs/development-workflow.md` を基準にする。
- プロダクト要件、タスク、担当、進捗はNotionを正式情報とする。
- 今後の正式な要件定義の参照先は、Notionの「アプリ開発プロジェクトWiki」内にある「議事録」データベースの「第1回要件定義議事録」ページである。Notionページの内容と承認状態を、過去の議事録・過去版Markdown・会話より優先する。
- `docs/requirements.md` は、上記Notionページをリポジトリでレビュー・実装確認するために同期したスナップショットである。Notionページと差異がある場合は、差異を報告し、同期と承認が済むまで不明な要件を実装しない。
- 2026-08-20更新のCloud上Markdown（SHA-256 `0768944180a8db8cea9393df6a7c0606190ec067fdb088eeba7cfee4f7597d84`）は今回反映したローカルexportの参照履歴であり、今後の要件更新の一次情報として扱わない。Notionが一時的に読めない場合は、最後に同期済みのリポジトリ文書を読み取り・診断の範囲で使い、要件変更や実装の根拠にはしない。
- 技術仕様、アーキテクチャ、認証・認可、開発ルールはリポジトリの `AGENTS.md` と `docs/` を正式情報とする。
- 実装内容はGit管理されたコードを正式情報とする。
- Slackは議論・相談に使い、Slack上の発言だけで正式仕様を変更しない。
- Notionとリポジトリの文書が矛盾する場合は、推測で実装・同期せず、差異と影響を報告する。

## 変更ルール

- 既存コードと現在の構成を理解してから変更する。
- 既存機能を不用意に破壊しない。要求と無関係なリファクタリングを混ぜない。
- 不明な仕様を推測して実装しない。判断が必要な点は未確定事項として明示する。
- 既存の命名規則、ディレクトリ構成、利用中のフレームワークを尊重する。
- 仕様、設計、環境構成、運用手順を変更した場合は、関連する文書も更新する。
- 単なる実装変更で仕様や手順に変化がない場合は、不要な文書変更を行わない。
- 文書とコード・設定が矛盾する場合は、勝手に片方へ合わせない。矛盾、根拠、影響を報告する。
- 秘密情報、個人用トークン、秘密鍵、本番認証情報をコミットしない。
- ユーザーの既存変更を勝手に取り消さない。

## Git / Pull Request運用

- Pull Requestの標準merge方式はGitHubの `Create a merge commit` とする。review済みcommitの境界とSHAを保持し、変更理由、切り戻し、原因調査を追跡できる状態を優先する。
- `Squash and merge` または `Rebase and merge` を使う場合は、対象Pull Requestごとに人間の明示承認を得る。履歴を整える目的だけで自動選択しない。
- CI成功やAI reviewだけをmerge承認としない。人間が `Files changed` と検証結果を確認し、明示的に承認してからmergeする。auto-mergeは使用しない。
- 今後のcommit author emailには、このrepositoryのlocal Git設定に登録したGitHub提供のnoreply emailを使う。実際のemail addressは追跡対象文書へ記載せず、email変更だけを目的とした既存commitの履歴書換えは行わない。

## プロジェクト固有の前提

- 初期製品はWebアプリケーションではなく、iOS・Android向けモバイルアプリケーションである。PC browser版と管理Webは初期実装に含めない。
- `mobile/` のReact Native / Expo / TypeScript / Expo Router projectが正式な製品clientである。
- `backend/` のFastAPI / Python / SQLAlchemy / psycopgが正式な製品APIである。現在はhealth、circle list、event listのread技術検証まで実装済みである。
- 開発DBはDocker Compose PostgreSQL 16、本番DB・Auth・StorageはSupabase、FastAPIの配備先はRender、build・提出はEAS、配布先はApp Store / Google Playとする。ただし、外部projectと正式接続はまだ未構築である。
- ルートのNext.js App Router projectはFastAPI read APIを表示する技術検証としてのみ保持する。製品機能を追加せず、Vercelを初期製品に使用しない。
- ストア必須のPrivacy Policy、Support URL、Universal Links / App Links検証ファイル等の最小限の静的ページは、製品Webアプリとは別の公開物として扱う。
- 初期認証はSupabase Authの一般Google OAuth、email/password、iOS版Sign in with Appleとする。大学Google account必須、university domain restriction、university SSOは実装しない。Android版Apple loginは初期必須としない。
- iOSで一般Google loginを提供するため、App Store Guideline 4.8対応としてSign in with Appleをrelease gateとする。
- 一般学生とcircle managerは同じlogin UIを使う。新規登録のcircle manager希望は申請状態であり、確認前にedit権限を付与しない。service operatorをpublic signupから作成しない。
- Google / Apple / emailのAuthenticationとcircle単位Authorizationを分離する。provider login、email確認、大学domain一致だけでmanager権限を付与しない。モバイルのaccess tokenをFastAPIで検証し、DBのmembershipを認可根拠とする。
- manager権限は`user_id`と`circle_id`のmembershipで管理し、初期のcircle内roleは`manager`だけとする。初回はservice operatorが確認・承認し、追加は既存managerの推薦・招待後にservice operatorが最終承認する。
- 公開サークルの公式情報は団体の存在確認に使うが、申請者の管理権限確認とは分ける。非公開サークルは既存managerまたはservice operatorの個別確認を必要とする。
- managerの追加・交代・解除、account削除時のmembership失効、申請・承認・解除の監査ログを正式要件とする。service operatorはMFAを必須とする。
- initial scopeはpersonalized home、detailed circle search、favorite、my page、circle page / management、report / shareである。
- eventは2026年度内を目標とするが具体時期未定、chatは時期未定であり、initial実装済みと扱わない。
- universityとschool yearは任意・非公開、birth dateは初期収集しない。interestは任意、view historyは説明後に明示的に有効化し、直近20件または90日の早い方までとする。
- nickname、university、birth dateから完全・一部email addressを返す旧案はDEC-052で廃止した。provider login、存在を明かさないemail reset、確認済みidentityを使うsupportへ置き換える。
- Chakra UIは現在の依存関係に含まれていない。要件・設計上の決定なしに追加しない。
- `docs/requirements.md` と `docs/authentication.md` が正式仕様である。「要確認事項」を推測で実装しない。
- `docs/requirements-progress.md` は現在の進捗要約、`docs/requirements-review-2026-08-21.md` は追加検討・non-functional reviewである。
- 合意済み議事録の機能を無効化しないが、security・privacy・operationに不足するacceptance criteriaを決める前に危険な挙動を実装しない。

## 依存関係と構成

- `mobile/` が製品project、ルートNext.jsは別の技術検証npm projectである。各ディレクトリの `package-lock.json` を維持する。
- JavaScript依存関係の再現には原則として `npm ci` を使う。
- React Native向けSupabase Auth clientとSupabase projectはまだ導入・作成していない。初期実装workで正式手順と`mobile/package-lock.json`を更新する。
- `backend/requirements.txt` / `requirements-dev.txt` は依存version範囲の入力、`requirements.lock` / `requirements-dev.lock` はuvで生成した再現用lockである。DockerとCIはlockをpipで導入する。
- 正式schemaのmigration toolはAlembicとする。初回revision `20260915_0001`は`app_private`へ27 tableを作り、現在のprototype tableを削除・baseline化しない。
- FastAPIの現在のcamelCase responseは既存read技術検証にのみ適用する。正式API契約は`docs/api-contract.md`の`/api/v1`、response envelope、Problem Details、cursor、idempotencyを正とする。
- PostgreSQLの永続データを削除する `docker compose down -v` は、明示的な依頼なしに実行しない。

## 検証

変更範囲に応じて、実行可能な検証を行う。

### Next.js技術検証

```bash
npm run lint
npm run build
```

### React Native / Expo製品client

```bash
cd mobile
npm run check
npx expo-doctor@latest
```

`npm run check` はLint、TypeScript型検査、Jest testを順に実行する。`mobile/` を変更した場合に実行するiOS・Android製品clientの基本検証である。

### FastAPI / PostgreSQL

```bash
cd backend
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
.venv/bin/alembic history
docker compose up -d --build
curl http://localhost:8000/health
curl http://localhost:8000/api/circles
curl http://localhost:8000/api/events
```

初回はuvで `.venv` を作成し、`requirements-dev.lock` を導入する。`/health` が `{"status":"ok","database":"connected"}` を返すことを確認する。

## 文書の役割

- `README.md`: プロジェクトの入口と最短の起動手順
- `mobile/README.md`: 正式なiOS・Android製品client固有の操作
- `docs/development-workflow.md`: 開発情報源、Slack・Notion・Codex・Git/GitHubの役割と連携
- `docs/development-setup.md`: 共同で実施したmacOS環境構築の実績、再構築、検証
- `docs/requirements.md`: Notionの「第1回要件定義議事録」を同期した製品要件スナップショットと初期リリース範囲
- `docs/architecture.md`: 正式採用する目標構成と現在との差
- `docs/authentication.md`: 正式な認証・認可・運営者確認
- `docs/decisions.md`: 採用・未確定・廃止を含む重要な決定履歴
- `docs/requirements-progress.md`: 合意済み要件の反映状況と残作業
- `docs/requirements-review-2026-08-21.md`: 要件の追加検討事項とnon-functional review
- `docs/requirements-decision-report-2026-09-15.md`: 委任された詳細項目の調査・決定・実装引継ぎ
- `docs/screen-flow.md`: 画面構成、遷移、loading・empty・error・offline
- `docs/api-contract.md`: `/api/v1`のresponse、error、pagination、idempotency、互換性
- `docs/data-dictionary.md`: 正式field、初期DB schema、推薦、保持・削除
- `docs/non-functional-requirements.md`: OS、性能、可用性、backup、accessibility、security、運用SLA
- `docs/coding-readiness.md`: 実装可能範囲、未確定blocker、導入済みquality baseline
