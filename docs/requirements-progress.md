# 要件定義の進捗

- 最終更新日: 2026-09-24
- 状態: iOS・Android専用方針、Before構成、初期実装に必要な詳細設計・非機能要件を確定。Notion同期と外部project準備を除き、最初のvertical sliceを実装可能

## 1. 情報源

要件の一次情報はNotion「アプリ開発プロジェクトWiki」→「議事録」DB→「第1回要件定義議事録」である。`docs/requirements.md`は実装確認用snapshot、技術・認証・決定はリポジトリ文書を正とする。過去のCloud上Markdownは参照履歴であり、今後の更新元ではない。

今回の詳細決定は、ユーザーから判断を委任された範囲について公式資料と現在の構成を調査し、DEC-051～058として記録した。外部契約、支払、実在担当者は推測していない。

## 2. 確定済み

### 製品・構成

- 初期製品はiOS・Androidアプリだけ。製品Web、PC browser、別管理Webは作らない。
- `mobile/`のReact Native / Expo / TypeScript / Expo Routerを正式clientとする。
- `backend/`のFastAPI / Python / Pydantic / SQLAlchemy / psycopgを正式APIとする。
- localはPostgreSQL 16、productionはSupabase PostgreSQL / Auth / Storage、APIはRender、build / submitはEAS、配布はApp Store / Google Playとする。
- root Next.jsはread技術検証だけに残し、製品機能を追加しない。

### 初期機能

- personalized home、法政大学向けcircle search、favorite、my page
- circle card / detail、manager edit・審査状態、report、share
- 4タブnavigationと認証・manager・operatorの保護route
- loading、empty、error、offline、retry、timeout、deep linkの共通挙動

### Data・推薦

- 正式tableは`app_private` schema、UUID、UTC日時、JPY整数、`TEXT + CHECK`を使う。
- 公開revisionと下書き・審査revisionを分離する。
- category・tagは運営master、主categoryは1つ、tagは複数とする。
- ratingは団体自己申告の5指標。男女比は任意区分で、個人genderを収集しない。
- 閲覧1点、お気に入り5点、興味3点。同一user・circleの閲覧は30分に1回。
- 上位10件は安定sort、以降はuser・JST日付・filterで決定的shuffleとする。
- 生年月日は初期収集しない。大学・学年は任意、閲覧履歴は明示操作後に最大20件または90日。

### API・DB

- `/api/v1`、camelCase、UUID、RFC 3339 UTC、RFC 9457 Problem Detailsを採用する。
- cursor paginationは既定20・最大50、重要操作は24時間のidempotencyを使う。
- 初回Alembic revisionは`app_private`へ27 tableを作成し、prototype tableを変更しない。
- 一時PostgreSQL 16でupgrade、27 table、downgrade、再upgradeを確認済み。

### 認証・認可

- 初期loginは一般Google OAuth、email/password、iOS版Sign in with Apple。
- 大学Google account必須、大学domain制限、大学SSOは実装しない。
- Authenticationとcircle単位Authorizationを分離し、provider loginだけでmanager権限を付与しない。
- managerは`user_id`・`circle_id` membershipが`active`の場合だけ編集できる。
- 団体存在と申請者権限を別確認し、公開可否に応じてcontrolled channel、既存manager招待、member確認を組み合わせる。
- 証拠原本は判断・appeal終了後30日、絶対上限90日。判断監査は365日。
- nickname・大学・生年月日からemailを表示せず、provider login・共通応答reset・確認済みidentityのsupportに置き換える。

### 非機能

- iOS 16.4以上、Android 10 / API 29以上、phone縦向きを初期最適化する。
- cold start p75 3秒、API GET p95 500ms、一般公開availability 99.5%、RPO 24h、RTO 8hを初期目標とする。
- WCAG 2.2 AA相当、MASVS L1 / API Security Top 10、Critical / High 0件をrelease gateにする。
- SLA、backup、restore、削除期限は`docs/non-functional-requirements.md`を正とする。

## 3. 将来機能・未確定

| 項目 | 状態 |
| --- | --- |
| event | 2026年度内目標、具体release未定。現在のprototype APIは正式化しない |
| chat / DM | 時期・moderation・保持が未定。初期対象外 |
| notification | channel・同意・頻度・費用が未定 |
| LINE login | 将来候補 |
| Android版Apple login | 将来候補。iOS版は初期決定済み |
| circle auto deletion | 初期対象外 |
| paid boost / advertising | 構想のみ。自然推薦に混ぜない |
| MARCH / 全大学 | 将来phase |

## 4. 人の操作・判断が残るもの

- Work 3以降のPull Request review・人間merge承認、共同開発者招待、required checks設定（GitHub CLI接続は確認済み）
- 正式service名、bundle identifier、Android package name、link domain
- Supabase / Render / EAS / Apple / Googleのowner、region、plan、支払責任者
- 許容月額、production monitoring / SMTP等の有料service選定
- Privacy Policy、利用規約、Support URLの公開文面
- 実在するservice operator、第二確認者、当番、緊急連絡先
- categories / tagsの初期seed語彙の最終表記review
- event等の将来優先順位

## 5. 現在の実装事実

- `mobile/`: 4タブとCircle詳細route shell、共通状態、API URL validation、OpenAPI生成型、native fetch transport、公開Circle typed facade、Lint・型検査・Jestまで。画面からのAPI呼出しと認証は未実装。
- `backend/`: unversioned read技術検証を維持しつつ、正式`/api/v1`共通基盤と`app_private`公開Circle一覧・詳細を実装済み。認証・書込み・他resourceは未実装。
- PostgreSQL: prototype public tableに加え、Git上に正式`app_private`初回migrationがある。共有開発DBへの適用は各開発者が明示的に行う。
- GitHub Actions: MobileのOpenAPI生成型stale check、Lint・型検査・Jest、Backend PostgreSQL integration、Compose migration往復、Next.jsの4 jobを定義済み。各Pull Requestのlatest HEADの結果をGitHubで確認する。
- 外部project: Supabase、Render、EAS、各storeは未構築。

## 6. 次のwork

1. Work 3のMobile共通基盤Pull Requestをreviewし、GitHub上のCIと人間承認を確認する。
2. 公開Circle一覧・詳細を両Simulatorで接続し、最小vertical sliceを完成させる。
3. 外部projectが必要になる直前にowner・identifier・planを確定する。
4. 認証・profile・favorite・推薦、manager審査の順でpermission test付き実装へ進む。

詳細は`docs/coding-readiness.md`と`docs/requirements-decision-report-2026-09-15.md`を参照する。
