# 正式アーキテクチャ

- 状態: 正式仕様
- 初回決定日: 2026-07-25
- 最終更新日: 2026-09-19
- 対象: ホウクル初期実装

## 1. 結論

初期製品はWebアプリケーションではなく、iOS・Android向けモバイルアプリケーションとする。共同開発者が構築済みのBefore環境を正式構成として再採用する。

```text
iOS / Android
  React Native / Expo / TypeScript / Expo Router
        |
        | HTTPS + JSON
        | Authorization: Bearer <Supabase access token>
        v
Render
  FastAPI / Python / Pydantic / SQLAlchemy
    - API contract
    - input validation
    - authentication token verification
    - circle-level authorization
    - moderation / audit
        |
        +------------------> Supabase PostgreSQL
        |                      - product data
        |                      - membership / review / audit data
        |
        +------------------> Supabase Storage
                               - circle / profile images

Authentication: Supabase Auth
Build / Submit: EAS Build / EAS Submit
Distribution: App Store / Google Play
Source / CI: GitHub
```

開発環境では、現在構築済みのDocker Compose PostgreSQL 16とFastAPIを使用する。本番のPostgreSQL、Auth、StorageはSupabase、FastAPIの配備先はRenderを目標とする。これらの外部projectはまだ未作成であり、採用決定と構築済みを混同しない。

サークル検索等を提供する製品Web、管理Web、PCブラウザ版は初期製品に含めない。ルートのNext.jsは既存FastAPI APIの表示確認に使う技術検証としてのみ保持し、製品機能を追加しない。プライバシーポリシー、利用規約、サポートURL、Universal Links / App Links検証ファイル等の最小限の静的公開ページは、ストア・OS要件を満たすための例外とし、製品Webアプリとは扱わない。

## 2. 採用技術、役割、採用理由

| 区分 | 採用技術 | 役割 | 採用理由 |
| --- | --- | --- | --- |
| Mobile framework | React Native / Expo | iOS・Androidの画面とnative連携 | 1つのTypeScript codebaseで両OSを開発でき、構築済みSimulator / Emulatorを活用できる |
| Routing | Expo Router | 画面routingとdeep link | 現在の`mobile/`に導入済みで、Expo標準構成と合わせられる |
| 言語 | TypeScript | モバイルUI、状態、API client、型 | 両OSのclient実装を共通化し、少人数チームの保守負担を抑える |
| API | FastAPI | HTTP / JSON API、入力検証、認証・認可、業務処理 | サークル単位認可、審査、監査を信頼できるserver境界へ集約できる |
| Backend language | Python | FastAPIの実装 | 現在のAPI技術検証と共同開発環境を活用できる |
| ORM / DB access | SQLAlchemy / psycopg | PostgreSQL accessとtransaction | 現在のFastAPI構成に導入済みで、DB処理をAPI側へ集約できる |
| Schema migration | Alembic | PostgreSQL schema変更をrevisionとしてGit管理 | SQLAlchemy公式系のmigration toolであり、local・staging・productionへ同じ変更順序を適用できる |
| Database | PostgreSQL 16 / Supabase PostgreSQL | サークル、ユーザー、審査、監査等の永続化 | 関係、制約、検索、transactionを扱え、SQLiteとの差を持ち込まない |
| Authentication | Supabase Auth | Google、email/password、session、回復、MFA | passwordやOAuthを独自実装せず、React Nativeから利用できる |
| Storage | Supabase Storage | profile・circle画像 | app binaryやAPI filesystemへ依存せず、公開範囲をpolicyで制御できる |
| API hosting | Render Web Service | FastAPIのbuild、deploy、HTTPS | FastAPIの公式deploy手順があり、GitHub連携で運用できる |
| Build / submit | EAS Build / EAS Submit | iOS・Android build、署名、store提出 | Expo projectを両storeへ配布する手順を共通化できる |
| Distribution | App Store / Google Play | 利用者への配布と更新 | iOS・Android専用製品の正式配布経路 |
| Source / CI | GitHub Actions | Pull Request、Lint、型検査、test、build、API / DB smoke test | GitHub上で共同開発者が同じquality gateを再現できる |
| Dependency monitoring | Dependabot | npm、pip、Docker、GitHub Actionsの更新候補を月次Pull Requestにする | 小規模チームで通知量を抑えながら既知の更新を追跡できる |

既存コードがあることだけを採用理由にしない。iOS・Android専用という製品要件、共同開発者が構築済みの環境、認可をserverへ集約する必要性、両OSを1 codebaseで保守できることを合わせて判断している。

## 3. 採用しない製品構成

| 構成 | 現在の扱い |
| --- | --- |
| Next.js + Supabase + Vercel | 2026-08-21から2026-09-01までの旧Web方針。製品経路から除外 |
| ルートNext.js | FastAPIのread APIを確認する既存技術検証。製品機能を追加しない |
| React + Vite | 製品clientに採用しない |
| SQLite | 開発・本番差が大きいため採用しない |
| 独自password認証 | 採用しない。Supabase Authへ委ねる |
| mobile clientから業務tableへの直接書込み | 初期採用しない。FastAPIを経由する |

## 4. モバイルアプリの責務

- 公開サークルのホーム、検索、カード、詳細を表示する。
- login、profile、favorite、履歴、通報、サークル管理等の画面を提供する。
- iOS・Androidで同じAPI contractを使用する。
- Supabase Authで得たaccess tokenをFastAPIへ送る。
- token、秘密情報、個人情報をlogやanalyticsへ出さない。
- 端末権限は必要な時点で目的を説明して要求し、拒否時の代替を用意する。
- APIのloading、offline、timeout、retry、empty、unauthorized、maintenance状態を扱う。
- clientから送る`role`、`circle_id`、`is_manager`を認可根拠にしない。

サービス運営者向けの公開・差し戻し・通報対応・管理者承認も、別の管理Webを作らず、同じモバイルアプリ内の保護された運営者画面として設計する。運営者権限は公開signupから取得できない。

## 5. FastAPIの責務

- `/api/v1`のversioned HTTPS / JSON APIを提供する。
- Pydanticで入力とresponseを検証する。
- Supabase Authの署名済みaccess tokenをissuer、signature、audience、expiration等で検証する。
- tokenの利用者IDと現在のaccount状態を確認する。
- protected operationごとに`user_id`、`circle_id`、membership状態、service operator権限をDBで再確認する。
- profile、favorite、履歴、サークル変更、管理者申請、公開審査、通報等のtransactionを管理する。
- rate limit、idempotency、audit、error responseを共通化する。
- DB接続情報、Supabase service secret、署名鍵管理情報をモバイルアプリへ渡さない。
- OpenAPIを機械可読なAPI契約の一次情報とし、生成TypeScript clientとの差分をCIで確認する。
- 正常response、RFC 9457 Problem Details、不透明cursor、24時間idempotency等は `docs/api-contract.md` を正とする。

初期製品の業務データはFastAPIを経由する。Supabaseのpublishable keyを持つアプリからPostgREST経由で業務tableへ直接書き込む構成は採用しない。

## 6. Supabaseの責務

### 6.1 Auth

- 一般GoogleアカウントによるGoogle login
- iOS版のSign in with Apple
- email/password登録とlogin
- email確認、password reset、email変更
- mobile sessionの発行・refresh・失効
- service operator向けMFA

大学Google Workspace、大学domain制限、大学SSOは使用しない。Google loginは本人のlogin identity確認であり、大学所属またはサークル管理資格の証明には使用しない。

iOS版は一般Google loginを提供し、大学account必須の教育機関例外を前提にできないため、App Store Review Guideline 4.8へ対応するSign in with Appleを初期release gateとする。Android版のApple loginは初期必須としない。

### 6.2 PostgreSQL

- primary key、foreign key、unique、check、transactionで整合性を守る。
- schema migrationをGit管理し、Dashboardの手作業だけで変更しない。
- FastAPI専用の最小権限DB roleを使用する。
- 正式業務tableは`app_private` schemaへ置き、Supabase Data APIへ公開しない。FastAPI専用roleだけへ必要な権限を与える。
- production dataをlocalやpreviewへコピーしない。
- 日次backup、RPO 24時間、RTO 8時間、四半期restore rehearsalを一般公開gateとする。Storage objectはDB backupと別に保護する。

### 6.3 Storage

- profile画像、サークル画像、審査中画像をbucketとpathで分離する。
- upload開始前にFastAPIでsessionと権限を確認し、signed URL等の限定された手段を発行する。
- MIME、拡張子、file signature、size、画像decodeを検証する。
- 不要なEXIFを削除する。
- service keyをアプリへ埋め込まない。

## 7. 認証・認可境界

```text
Supabase Auth
  -> account identity / mobile session

Expo app
  -> access tokenをAuthorization headerでFastAPIへ送信

FastAPI
  -> token検証
  -> account状態確認
  -> circle membership / service operator確認
  -> business rule / audit

PostgreSQL
  -> relationship、state、constraintを保持
```

- Google、Appleまたはemailでloginできることは、サークル管理資格を意味しない。
- 新規登録時の「サークル管理者希望」は申請状態だけを作り、確認前に編集権限を与えない。
- サークル管理者権限はglobal roleではなく、`user_id`と`circle_id`のmembershipで表現する。
- membershipが`active`の場合だけ担当circleを変更できる。
- 既存管理者の推薦・招待だけでは有効化せず、サービス運営者が最終承認する。
- サービス運営者はpublic signupから取得できないserver-managed roleとする。
- モバイル画面でbuttonを隠すだけの認可を禁止する。

詳細は`docs/authentication.md`に定める。

## 8. データ設計方針

正式なtable、column、constraint、index、削除・保持規則は `docs/data-dictionary.md` を正とする。主なentityは次のとおりである。

- `profiles`
- `universities`
- `campuses`
- `categories`
- `tags`
- `circles`
- `circle_revisions`
- `circle_memberships`
- `manager_applications`
- `manager_invitations`
- `manager_evidence`
- `activity_schedules`
- `activity_locations`
- `circle_costs`
- `social_links`
- `favorites`
- `circle_views`
- `reports`
- `media_assets`
- `service_operators`
- `audit_logs`
- 将来: `events`、`event_revisions`、`chats`、`messages`、`notifications`

全tableは`app_private` schemaへ置き、UUID、UTCの`TIMESTAMPTZ`、JPY整数、`TEXT + CHECK`を共通ruleとする。公開中のサークル情報と、サークル管理者が編集中・確認待ちのrevisionを分離し、確認待ちの内容で公開版を上書きしない。Supabase Authの`sub`と`accounts.id`を同じUUIDにするが、local PostgreSQLとの再現性のため`auth.users`へのDB FKは持たず、FastAPIがtokenとaccountを照合する。

## 9. local・preview・production

| 環境 | Mobile | API | DB / Auth / Storage | 状態 |
| --- | --- | --- | --- | --- |
| local | Expo development server、iOS Simulator、Android Emulator。API URLは`EXPO_PUBLIC_API_BASE_URL` | Docker Compose FastAPI | Docker Compose PostgreSQL 16。Auth / Storage local構成は要決定 | Expo初期画面、環境変数validation、testとAPI・DBを個別確認済み。Expo→APIは未接続 |
| preview / staging | EAS development / preview build候補 | productionと分離したRender service候補 | productionと分離したSupabase project候補 | 未構築 |
| production | App Store / Google Play配布build | Render Web Service | production Supabase project | 未構築 |

- local、preview、productionでsecretと個人データを共有しない。
- API base URL、Supabase URL、publishable key、deep link schemeをbuild profileごとに分離する。
- server secret、DB password、Supabase service secretを`EXPO_PUBLIC_`変数へ入れない。
- EAS、Apple、Google、Render、Supabaseのownerを個人1名だけに依存させない。

## 10. build・deploy・release

- Expo appはEAS BuildでiOS・Android buildを作成する。
- EAS SubmitをApp Store Connect / Google Play Consoleへの提出経路として採用する。
- FastAPIはRender Web Serviceへ配備する。
- production deployはCI、migration、API互換性、mobile app versionの順序を確認する。
- mobile releaseはstore reviewと段階的rolloutを考慮し、APIを旧app versionと後方互換にする。
- 緊急時にAPI側で危険な操作を停止できるようにする。
- App Review用のdemo accountまたはreview手順を用意し、審査中もbackendを稼働させる。
- アカウント作成を提供するため、アプリ内account削除をrelease gateとする。
- Privacy Policy、Support URL、ストアmetadata、Data Safety / App Privacy回答をrelease前に整備する。

## 11. 実装品質・セキュリティ方針

実装品質の最低基準として、GitHub ActionsでmobileのLint・型検査・Jest test、FastAPIのRuff・pytest・Alembic設定確認、FastAPI / PostgreSQLのbuild・health・read endpoint、Next.js technical verificationのLint・buildを実行する。Dependabotは月次とし、互換性を確認せず自動mergeしない。

Python依存はversion範囲を`requirements.txt` / `requirements-dev.txt`へ記述し、uvで生成した`requirements.lock` / `requirements-dev.lock`をDockerとCIへ使用する。実行時は従来どおりpipを使い、依存管理方式を全面変更しない。入力を変更したPull Requestでは対応するlockも再生成する。

現在のcircle / event技術検証だけがruntimeの`Base.metadata.create_all()`を使い、正式`app_private` schemaはAlembic revisionだけで変更する。初回revisionは `docs/data-dictionary.md` の初期schemaを作り、prototype tableを削除・移行しない。正式ORM mappingは実装sliceごとに追加してmigrationとの一致をtestし、それまではprototype metadataをAlembic autogenerateへ渡さない。

Expo SDKは同一SDK内の公式互換versionへ揃える。major SDK update、`npm audit fix --force`、native workflowを変えるdependencyは、自動適用せずSimulator / Emulatorと必要な実機で確認する。root Next.js technical verificationは、制限環境でも再現できるNext.js公式の`--webpack` buildを使用する。

- HTTPS以外でproduction APIへ接続しない。
- access tokenをquery parameterへ入れない。
- mobile appへserver secretを埋め込まない。
- access tokenは15分を初期値とし、refresh tokenはExpo SecureStoreの端末限定・unlock後access相当で保存し、Android backupから除外する。
- certificate pinningは更新不能や障害リスクを含め、採否を別途判断する。
- APIはresource単位で認可し、IDOR・cross-circle accessを自動testする。
- login、password reset、report、管理者申請、画像uploadへrate limitを設ける。
- crash reportやanalyticsへtoken、email、審査資料を送らない。生年月日は初期収集しない。
- dependency、container image、mobile buildの脆弱性確認をrelease gateへ含める。
- OWASP MASVS Level 1とOWASP API Security Top 10を初期baselineとし、数値gateは `docs/non-functional-requirements.md` を正とする。

## 12. 現在との差

| 項目 | 現在 | 正式化に必要なこと |
| --- | --- | --- |
| Expo | static initial screen、両Simulator環境、API URL validation、Lint・型検査・Jest testあり | API接続、正式navigation、auth、各機能、実機確認 |
| FastAPI | unversioned read技術検証、`/api/v1`共通基盤、`app_private`公開Circle一覧・詳細、Ruff / pytest / OpenAPI baseline | mobile接続、auth、write、authorization、audit、他resource |
| Local PostgreSQL | Docker Compose PostgreSQL 16とprototype seed。`app_private`正式初回revision、公開Circle用ORM・repositoryあり | 他sliceのORM、認証連携後のseed、各機能migration |
| Supabase | project / dependency未構築 | PostgreSQL、Auth、Storage、environment分離 |
| Render | project未作成 | build、start、secret、health check、monitoring |
| EAS | build / submit未設定 | project owner、credentials、build profiles、submit設定 |
| Stores | account・listing未確認 | organization ownership、契約、metadata、review、release手順 |
| GitHub Actions | mobile、Backend PostgreSQL integration、Compose、Next.js technical verificationの4 job定義あり | 各Pull Requestのlatest HEAD確認とrequired checkのruleset設定 |
| Next.js | FastAPI read API表示の技術検証。offline build対応、既知Critical修正済み | 製品機能を追加せず、保持・archive時期を別途決定 |
| Vercel | projectなし | 初期製品では使用しない |

2026-09-14に外部projectを必要としないdependency整合、test、CI、環境変数、共同開発基盤を追加し、2026-09-15に画面、API、data、認証運用、非機能要件と初回schemaを正式化した。2026-09-18に`/api/v1`共通基盤、2026-09-19に`app_private`公開Circle一覧・詳細を追加した。mobile接続、auth、write、他の正式resource、deployは未実装である。

## 13. 要確認事項

1. Expo managed workflowを維持する範囲とdevelopment build / native moduleの条件
2. local Auth / StorageをSupabase CLIで再現するか、共有development projectを使うか
3. production / staging Supabase projectの実値と分離
4. Render / Supabaseのregion、plan、月額上限、cost alertの基準額
5. EAS、Apple Developer、Google Play Consoleの組織ownerと支払責任者
6. bundle identifier、Android package name、Universal Links / App Linksのdomain
7. service operator向けモバイル画面の配布・初期付与・緊急復旧の実在担当者
8. store review用account、Privacy Policy、Support URLの公開先と文面
9. crash reporting、analytics、monitoring serviceの選定と費用
10. Expo major SDK updateの承認・実機確認手順
11. Next.js技術検証をarchiveまたは削除する時期

## 14. 公式資料

- [Expo](https://docs.expo.dev/)
- [EAS Build](https://docs.expo.dev/build/introduction/)
- [EAS Submit](https://docs.expo.dev/deploy/submit-to-app-stores/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Render FastAPI deployment](https://render.com/docs/deploy-fastapi)
- [Supabase Auth with React Native](https://supabase.com/docs/guides/auth/quickstarts/react-native)
- [Supabase JWT](https://supabase.com/docs/guides/auth/jwts)
- [Supabase Storage](https://supabase.com/docs/guides/storage)
- [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Google Play policy center](https://play.google.com/about/developer-content-policy/)
- [OWASP MASVS](https://mas.owasp.org/MASVS/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
