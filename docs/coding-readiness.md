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
3. Expoへ4タブ、共通loading / empty / error / offline component、型付きAPI clientを追加する。（Work 3で実装、Pull Requestの人間承認待ち）
4. 公開一覧・詳細のvertical sliceをiOS SimulatorとAndroid Emulatorで接続する。（次の実装work）
5. profile、interest、view、favorite、推薦を認証前提のsliceとして追加する。
6. manager application、membership、revision、operator reviewをpermission matrix test付きで追加する。
7. report、account deletion、監視、backup / restore rehearsalを整え、限定公開へ進む。

正式ORM mappingは各sliceで必要なtableから追加し、初回migrationと差分testを行う。prototypeの`public.circles` / `public.events`へ正式機能を積み上げない。

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
