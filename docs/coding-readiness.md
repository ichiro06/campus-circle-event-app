# コーディング開始準備レポート

- 判定日: 2026-09-15
- 対象: ホウクルのiOS・Android初期製品
- 判定: **正式な公開サークルvertical sliceからコーディング開始可能**

## 1. 結論

React Native / Expo、FastAPI、PostgreSQLというBefore構成は維持する。2026-09-15に、前回blockerだった画面状態、data dictionary、API契約、初回DB schema、profile保持、推薦、manager確認、account recovery、非機能目標を正式化した。初回Alembic revisionは既存prototypeを変更せず`app_private`へ27 tableを作り、一時PostgreSQL 16でupgrade、downgrade、再upgradeを確認した。

したがって、公開サークル一覧・詳細を`Expo -> /api/v1 -> app_private PostgreSQL`で接続する最初のvertical sliceは開始できる。認証・Storage・deployは外部project値が必要な時点で止め、仮のsecretやidentifierを登録しない。

## 2. 実装基準として揃ったもの

| 領域 | 正式な参照先 | 状態 |
| --- | --- | --- |
| 製品範囲 | `docs/requirements.md` | iOS・Android専用、初期・将来機能を区別済み |
| 画面・通信状態 | `docs/screen-flow.md` | 4タブ、遷移、loading / empty / error / offlineを確定 |
| API | `docs/api-contract.md` | `/api/v1`、response、Problem Details、cursor、idempotencyを確定 |
| Data | `docs/data-dictionary.md` | field、constraint、保持・削除、推薦を確定 |
| DB migration | `backend/migrations/versions/20260915_0001_initial_product_schema.py` | `app_private` 27 table。往復検証済み |
| 認証・認可 | `docs/authentication.md` | Google / email、iOS Apple、session、manager確認を確定 |
| 非機能 | `docs/non-functional-requirements.md` | OS、性能、可用性、backup、accessibility、security、SLAを確定 |
| Quality | local command / GitHub Actions | mobile、backend、migration、Next.js技術検証の検査を用意 |

## 3. 実装順

実装前のWork 0として、現在の未commit差分を内容別にreviewし、Public repositoryへ共有可能かを確認する。このreviewは未追跡fileを含む現在の状態そのものが対象なので、`origin/main`から作る空の別worktreeではなく、現在のcheckoutと同じdirectory、または現在のworking treeを開始状態として引き継いだ環境で行う。ここではcommit / pushを自動実行せず、共有baselineが人間の確認後に確定してから、以降の実装を`codex/` branchとPull Requestで進める。

1. FastAPIへrequest ID、成功envelope、RFC 9457 errorの共通処理を追加する。（Work 1で完了）
2. `app_private`の公開circle read repository / Pydantic modelと一覧・詳細endpointを実装する。（Work 2で完了）
3. Expoへ4タブ、共通loading / empty / error / offline component、型付きAPI clientを追加する。（`W3 Mobile Foundation`: COMPLETE。PR #22でmainへmerge済み。merge commit: `f019ab1`）
4. `Home Contract / API Readiness Gate`は、公開read範囲とPersonalized Home / Releaseの未決事項を混同しないよう、開発gate A〜Dへ分割して扱う（3.1参照。製品仕様の新しいHuman Decisionではなく、既存のformal decisionsは変更しない）。Circle一覧APIの`GET /api/v1/circles?sort=most_favorited`はbackendで実装済みである（DEC-061 D1〜D4、PR #27。`favoriteCount`のresponse公開、fraud検知、Home推薦は含まない）。Gate A（Public Read API Readiness）はPASSであり、`W4 Public Circle Slice`（公開Circle一覧・詳細のvertical sliceをiOS SimulatorとAndroid Emulatorで接続する）は公開read範囲に限りREADY_TO_STARTである。Gate B（Personalized Home Contract Readiness）、Gate C（Home Production Ready）、Gate D（External Beta / Release Readiness）はBLOCKEDのままである。
5. profile、interest、view、favorite、推薦を認証前提のsliceとして追加する。
6. manager application、membership、revision、operator reviewをpermission matrix test付きで追加する。
7. report、account deletion、監視、backup / restore rehearsalを整え、限定公開へ進む。

正式ORM mappingは各sliceで必要なtableから追加し、初回migrationと差分testを行う。prototypeの`public.circles` / `public.events`へ正式機能を積み上げない。

View定義は正式文書間で未解決である。定義が解決するまで、circle view write、view history behavior、viewをsignalとして使うrecommendation logicは実装しない。この記録はGateだけを示し、閲覧元や計数条件を決定しない。

### 3.1 Home Contract / API Readiness Gateの分割（開発gate）

W4 Entry Gate Audit（基準: `main` `bdd252e`、PR #27 merge済み、main CI #44 SUCCESS）の結果に基づく、開発gateの整理である。製品仕様の新しいHuman Decisionではなく、FR-001、FR-002、FR-005、FR-013、DEC-055、DEC-061、API設計を変更しない。A2、R1、R2等の未決事項を確定するものでもない。W4開始前に必要な製品仕様上のHuman Decisionは0件である。

| Gate | 対象 | 状態 |
| --- | --- | --- |
| A. Public Read API Readiness | 公開Circle list、公開Circle detail、`sort=most_favorited`、OpenAPI、generated mobile type、public read contract | **PASS** |
| B. Personalized Home Contract Readiness | personalized recommendation、view signal、interest scoring、cold-start orchestration、決定的shuffle | **BLOCKED**（A2、R1、R2、view signalに対するmanager / operator除外scope） |
| C. Home Production Ready | Gate Bに加え、fraud / abnormal signalの具体仕様 | **BLOCKED**（DEC-061 D2のrelease gateを維持） |
| D. External Beta / Release Readiness | fraud具体仕様、most_favorited NFR分類、production-equivalent環境での性能検証、外部project・identifier・store等、既存release security gates | **BLOCKED** |

`W4 Public Circle Slice`はGate Aを満たすため**READY_TO_START**である。ただし対象は公開read vertical sliceだけであり、Gate B〜Dの未決事項はW4 public readの開始・実装を止めない。

#### W4で実装可能な範囲

- Home: `GET /api/v1/circles?sort=most_favorited`（未ログインHome。viewもinterestもないため、cold-startの順序制御に依存しない）
- Search: 既存の公開Circle list API（`q`、`newest`、`most_favorited`、既存固定enum filter）
- Circle detail: `GET /api/v1/circles/{circleId}`
- Mobile: Circle card、loading、empty、error、offline、retry、pagination、detail navigation、accessibility

これはFR-001、FR-005、FR-017、FR-018の全体完了を意味しない。W4はpublic read slice / partial implementationとして扱う。

- Retry: `docs/screen-flow.md` 6節で確定済みのGET retry（network error、timeout、429、502、503、504に限り最大2回、約0.5秒・1.5秒＋jitter、`Retry-After`優先）は、新仕様ではなく既存formal仕様の実装としてW4で必要である。
- Offline: persistent offline cacheのstorage / NetInfo等は未整備である。W4ではloading、error、offline状態、画面memory上の直近成功data保持までを対象にできる。アプリ再起動をまたぐpersistent offline cacheをW4必須にするかは決めていない。
- Search: 「おすすめ順」、popular tag導線、tag / category master endpoint依存UIは未実装 / deferredであり、W4で追加しない。

#### W4で実装しないもの

personalized Home、view write、favorite write、interest scoring、A2の決定的shuffle、R1、R2、fraud detection、manager / operator機能。`favoriteCount`をCircle responseとして公開せず、mobileでも表示しない。cursorはclient側でopaqueとして扱い、payloadを解釈しない。

#### 未決事項の状態（本整理では解決しない）

| 項目 | 状態 | 内容 |
| --- | --- | --- |
| A2 | UNRESOLVED | DEC-055の「user ID + JST date + filter」におけるfilterの意味。W4は決定的shuffleを実装しないためblockしない |
| R1 | UNRESOLVED | FR-001には「閲覧データ数 = Homeのサークルカードからサークルページへ遷移した回数」の意味定義がある。一方、Search経由・deep link経由、実際のview write trigger、30分dedup前後どちらを5件判定に使うかは未決。W4はview writeを実装しない。`docs/data-dictionary.md`・`docs/screen-flow.md`の既存view write文言は本整理で修正しない |
| R2 | UNRESOLVED | FR-001は「viewデータ5件未満 → favorite count順」、`docs/data-dictionary.md`は「interest scoreの後にfavorite count」と差がある。cold-start orchestrationはPersonalized Home実装前にHuman Decisionが必要。未ログインW4はviewもinterestもないため`sort=most_favorited`で実装できる |
| viewに対するmanager / operator除外scope | UNRESOLVED | favorite集計のA1を横展開しない |
| H10 | UNRESOLVED | `favoriteCount`のAPI response公開 |
| cursor confidentiality | FOLLOWUP | cursorは署名のみで暗号化していない。W4 start blockerではない |
| most_favorited NFR分類 | UNRESOLVED | GET p95 500ms／検索・書込みp95 800msのどちらか。正式な受入閾値は決めていない |
| 性能follow-up | OPEN | W4開発開始・public read実装は止めない。external beta / release前に、production-equivalent環境で正式dataset + concurrencyの再測定が必要 |
| fraud具体仕様 | OPEN | W4 public read start blockerではない。Home recommendationのproduction-ready扱い前またはexternal beta / production release開始前の早い方より前に必要（DEC-061 D2を維持） |

## 4. 現在ユーザー操作・外部契約が必要な事項

- GitHub CLI: 2026-09-15に`ichiro06`として認証とGitHub API接続を確認済み。対象repositoryはPublic、権限はADMIN、default branchは`main`。
- GitHub: 差分review後のbaseline commit / push、共同開発者招待、required checks / ruleset設定。
- 正式service名、bundle identifier、Android package name。
- Apple Developer、Google Play Console、Google Cloud、Supabase、Render、Expo / EASのowner・支払責任者・region・plan。
- Privacy Policy、利用規約、Support URLの公開文面と必要に応じた法務確認。
- 実在するservice operator、第二確認者、当番、緊急連絡先。
- productionの月額上限。承認額の70% / 90% alertは設定方針だけ確定済み。

これらは現在の公開read UI / APIのコーディングを止めない。該当する外部接続・認証・公開releaseへ到達する前のgateとする。

## 5. 現在着手してよい範囲

- `app_private`初回migrationを基準とする公開circle read model / repository / endpointの保守・拡張
- `W4 Public Circle Slice`の公開read範囲（3.1。Gate A PASS）。personalized Home、view write、favorite write等は含まない
- `/api/v1`共通response、error、request ID、cursor helperとtest
- Expo Routerの4タブ・公開詳細・認証route shell
- loading、empty、error、offline bannerとaccessibility test
- OpenAPIからのTypeScript client生成設定と差分check
- nickname、profile、interest、history、favoriteのschema / API。ただしSupabase接続値は外部project作成後
- recommendationの純粋関数とabuse exclusion test
- manager permission matrix、申請状態機械、監査eventの純粋なdomain test

## 6. 現在してはいけないこと

- prototype tableを正式schemaとして流用・破壊・自動移行すること
- Supabase / Render / EAS / storeへ仮owner、仮identifier、推測したsecretを登録すること
- Google、Apple、email確認だけでcircle manager権限を付与すること
- nickname・大学・生年月日からemailを表示すること
- 生年月日を初期profileやpassword resetで収集すること
- offline queueから公開、権限付与、報告、account変更を自動送信すること
- event / chat / notificationを初期実装済みとしてAPI・DBへ混ぜること
- `npm audit fix --force`やExpo major updateを検証なしで行うこと
- 差分review前にbaselineを一括commit / pushすること

## 7. 開発者が実行する確認

モバイル:

```bash
cd mobile
npm ci
cp .env.example .env.local
npm run api:check
npm run check
npx expo-doctor@latest
```

FastAPIとmigration:

```bash
cd backend
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r requirements-dev.lock
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
.venv/bin/alembic history
docker compose up -d --build
docker compose exec api alembic upgrade head
```

`docker compose down`はvolumeを残す。`docker compose down -v`はdata削除の明示依頼なしに実行しない。

## 8. 2026-09-15の検証

- Alembic history: `20260915_0001 (head)`
- 一時PostgreSQL 16: upgrade pass、27 table確認、downgradeでschema消去、再upgrade pass
- Mobile: Lint、TypeScript、2 test suites / 5 testsがpass
- Expo Doctor: 21 / 21 checksがpass
- Backend: Ruff check、Ruff format check、pytest 5件がpass（依存libraryのDeprecationWarning 1件のみ）
- Next.js technical verification: Lintとproduction buildがpass
- CI YAML parseと`git diff --check`: pass
- GitHub CLI: `ichiro06`として認証、GitHub API接続、Public repositoryへのADMIN権限を確認
- GitHub上のCI: 未実行。commit / push後に確認が必要

### Mobile dependency security debt（2026-09-15確認）

- 対象: `image-size@1.2.1`を起点とするMetro 0.84.4系の推移依存経路で、細工されたICNSおよびJXL / HEIF画像の解析が停止し得るDoS advisoryが`npm audit`のHigh 4件として報告されている。
- 現在の到達可能性: 確認時点ではMetroがrepository / build入力のlocal assetを解析する経路であり、公開サークルread APIやremote user inputを直接処理するruntime経路ではない。現在の静的Mobile baselineと正式testはpassしている。
- 判断: 開発baselineでは既知のsecurity debtとして一時受容する。限定公開またはreleaseの許可ではなく、信頼できない画像assetをrepository / build入力へ追加しない。
- 再評価条件: patched upstream versionが利用可能になった時、Work 3以降で画像処理範囲またはbuild入力が変わる時、限定公開 / release判断前。
- Exit criteria: 限定公開判断前に再監査し、release時までに既知Critical / Highの未対応脆弱性を0件とする。

2026-09-24のWork 3では`openapi-typescript` 6.7.6をdevDependencyとして追加した。全dependency監査はmoderate 15件・high 5件、runtimeだけの監査は既存と同じmoderate 14件・high 4件で、Criticalはともに0件だった。増分のHighはdev-onlyの`undici`経路であり、localのcommit済みOpenAPI snapshot生成に限定する。TypeScript 6をpeer rangeに含む安全な後継generatorが利用可能になった時点で更新する。

## 9. 参照

- `docs/requirements-decision-report-2026-09-15.md`
- Notion「アプリ開発プロジェクトWiki」→「議事録」DB→「第1回要件定義議事録」
- [Expo SDK reference](https://docs.expo.dev/versions/latest/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Alembic](https://alembic.sqlalchemy.org/en/latest/)
- [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
