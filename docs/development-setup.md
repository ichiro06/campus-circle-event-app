# macOS開発環境

最終環境監査日: 2026-09-15
正式方針反映日: 2026-09-14

この文書は、現在のリポジトリと開発端末を照合したmacOS向けセットアップ手順である。バージョンは監査端末で確認した値であり、プロジェクトがすべてを厳密に固定しているわけではない。

2026-09-01に、ユーザーと共同開発者が構築したBefore環境を正式構成として再採用した。初期製品はiOS・Android専用で、`mobile/` のExpoを製品client、`backend/` のFastAPIを製品API、PostgreSQLを業務DBとする。ローカルはDocker Compose PostgreSQL 16、本番はRender + Supabase、build / submissionはEAS、配布はApp Store / Google Playを使う。ルートNext.jsは既存のread API接続technical verificationに限り、製品Webや管理Webには使用しない。正式方針は `docs/architecture.md` を参照する。

## この文書の位置付け

このファイルを、実際に構築・確認した開発環境と、その再構築手順の基準文書とする。別のworkで環境に関する作業を始める場合は、最初に `AGENTS.md` と本書を確認する。

- 本書: 開発端末と現在のリポジトリで、実際に導入・確認できた環境
- `docs/architecture.md`: 今後の製品開発で正式採用する目標構成
- `docs/decisions.md`: 過去の方針、置換された方針、現在の決定
- `README.md`: リポジトリの入口と短い起動方法

本書の「確認済み」は、Terminal出力、設定ファイル、実際の起動試験のいずれかで確認できたものに限る。会話履歴や過去の手順書だけを根拠に完了扱いしない。端末やリポジトリの状態が変わった場合は、確認日と結果を更新する。

## 共同で実施した環境構築の要約

ユーザーがmacOSのTerminalで導入作業を進め、Codexが表示結果の確認、リポジトリ構成の作成・調整、各構成要素の接続試験を行った。2026-07-25時点で確認できる実績は次のとおりである。

| 区分 | 実際に行ったこと | 現在の状態 |
| --- | --- | --- |
| macOS基盤 | Terminal、zsh、Xcode Command Line Tools、Homebrewを準備 | 使用可能 |
| Git / GitHub | Git導入、SSH鍵作成、GitHub登録、SSH接続、remote設定、commit・pushを確認 | 使用可能 |
| GitHub CLI | `gh`をHomebrewで導入し、アカウント `ichiro06` として認証 | 使用可能。2026-09-15にGitHub API接続を再確認 |
| エディタ | Visual Studio Codeを導入 | 使用可能 |
| JavaScript | Node.js 24とnpmを導入 | Next.jsとExpoで使用可能 |
| Python | `uv`とuv管理のPython 3.13.14を導入 | 使用可能。ただし `python3` はmacOS標準の3.9.6を指す |
| コンテナ | Docker DesktopとDocker Composeを導入 | 製品APIとローカルPostgreSQLの開発で使用可能 |
| Web technical verification | Next.js、React、TypeScript、Tailwind CSSの依存関係を導入 | FastAPIのread API接続確認用。製品経路ではない |
| 製品API基盤 | FastAPI、Uvicorn、SQLAlchemy、psycopgをDockerイメージへ導入 | 起動、PostgreSQL接続、読み取りAPIを確認済み。認証・書込みは未実装 |
| ローカル製品DB | PostgreSQL 16をDocker Composeで構築 | FastAPI接続とprototype seedを確認済み。正式`app_private`初回Alembic revisionを作成・一時DBで往復検証済み |
| 製品モバイル基盤 | React Native、Expo、Expo Routerを `mobile/` に導入 | 初期画面、Lint、型検査、Jest test、Expo Doctorを確認済み。API・認証・製品機能は未実装 |
| 自動検査 | GitHub Actions、Jest、React Native Testing Libraryを導入 | local testは確認済み。GitHub上のCIはcommit・push後に初回確認が必要 |
| iOS確認環境 | XcodeとiOS Simulatorを導入 | iOS 26.3 Simulatorランタイムを確認済み |
| Android確認環境 | Android Studio、SDK、Emulator、Pixel 9 AVDを作成 | `Campus_Circle_API_36` を確認済み |
| UIライブラリ | 環境構築資料にあったChakra UIは導入対象から除外 | 未導入のまま維持 |
| 正式製品構成 | Expo + FastAPI + PostgreSQL、Render + Supabase + EAS +各ストア | ローカル基盤は構築済み。本番service / store連携は未構築 |

現在ローカルで接続確認済みなのは、次のFastAPI read API経路である。

```text
ブラウザ
  -> Next.js
  -> FastAPI
  -> PostgreSQL 16
```

このブラウザ経路はAPI確認用technical verificationであり、正式製品経路ではない。正式目標は次のとおりである。

```text
iOS / Android Expo app
  -> FastAPI on Render
  -> Supabase PostgreSQL / Storage

Authentication: Supabase Auth
Build / submission: EAS Build / EAS Submit
Distribution: App Store / Google Play
```

現在のExpo画面はFastAPI未接続で、FastAPIも認証・認可・正式書込みendpointを持たない。正式schemaはGit上のmigrationとして確定したが、共有開発DBへの適用とORM接続は未実装であるため、構成採用と製品機能完成を混同しない。

## 前提

- macOS 26.5.2
- Apple Silicon (`arm64`)
- zsh 5.9
- GitHubリポジトリへのアクセス権
- iOS開発にはXcode、Android開発にはAndroid Studio / SDK

## 必要なソフトウェア

| ソフトウェア | 用途 | 監査端末のバージョン | 必須範囲 |
| --- | --- | --- | --- |
| Xcode | iOSビルド、iOS Simulator | 26.6 | iOS開発に必須 |
| Xcode Command Line Tools | Gitやビルドツール | Xcode 26.6に付属 | 必須 |
| Homebrew | macOS用パッケージ管理 | 6.0.11 | 推奨 |
| Git | バージョン管理 | 2.55.0 | 必須 |
| GitHub CLI (`gh`) | GitHub操作 | 2.96.0 | 推奨 |
| Visual Studio Code | エディタ | 1.130.0 | 推奨 |
| Node.js | Next.js、Expo | 24.18.0 | 必須 |
| npm | JavaScript依存関係管理 | 11.16.0 | 必須 |
| Python | ローカルPython実行 | uv管理 3.13.14 / macOS標準 3.9.6 | 任意 |
| uv | Pythonとツールの管理 | 0.11.26 | 任意 |
| Docker Desktop | FastAPI、ローカルPostgreSQL | Docker 29.6.1 | API / DB開発に必須 |
| Docker Compose | API / DBコンテナ構成 | 5.2.0 | API / DB開発に必須 |
| Android Studio | Android開発環境 | 2026.1.2.10 | Android開発に必須 |
| Android Platform Tools | `adb` | 37.0.1 | Android開発に必須 |
| Android Emulator | Android仮想端末 | 36.6.11.0 | Android確認に必須 |

現在のAndroid環境には、Android 16（API 36）、Build Tools 36.0.0、Google APIs ARM64システムイメージがある。AVDはPixel 9の `Campus_Circle_API_36` である。XcodeにはiOS 26.3のSimulatorランタイムがある。

## インストール

### 1. Xcode

App StoreからXcodeをインストールし、一度起動して追加コンポーネントとライセンス処理を完了する。

Command Line Toolsだけが必要な場合は次を使用できるが、iOS Simulatorには完全なXcodeが必要である。

```bash
xcode-select --install
xcode-select -p
xcodebuild -version
```

### 2. Homebrew

Homebrew未導入時は公式インストーラを使用する。

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Apple Siliconでは、インストーラが案内する `brew shellenv` を `~/.zprofile` に設定する。

```bash
eval "$(/opt/homebrew/bin/brew shellenv zsh)"
brew --version
```

### 3. Git、Node.js、uv、GitHub CLI

```bash
brew install git node@24 uv gh
```

Node.js 24を優先するため、 `~/.zshrc` に次を設定する。

```bash
export PATH="/opt/homebrew/opt/node@24/bin:$PATH"
```

GitHub CLIを使う場合は認証する。

```bash
gh auth login
gh auth status
```

監査端末ではGitHub CLIが `ichiro06` として認証済みである。`gh`のpreferred protocolはHTTPSだが、現在のGit remoteはSSH URLを使用している。どちらの認証情報も端末ごとに設定し、リポジトリへ保存しない。

Python 3.13は `uv python install 3.13` で導入済みである。

```bash
uv python install 3.13
python3.13 --version
```

この端末では `python3.13` はuv管理のPython 3.13.14を指す。一方、 `python3` は `/usr/bin/python3` のPython 3.9.6を指すため、Python 3.13が必要な操作では `python3.13` または `uv run --python 3.13 ...` を明示する。現在のFastAPI技術検証はDocker内のPythonを使うため、ホスト側の `python3` の版には依存しない。

### 4. Visual Studio CodeとDocker Desktop

公式インストーラ、またはHomebrew Caskを使用する。

```bash
brew install --cask visual-studio-code docker
```

Dockerコマンドを使う前にDocker Desktopを起動する。

### 5. Android Studio

```bash
brew install --cask android-studio android-commandlinetools android-platform-tools
```

Android StudioのSDK Manager、または `sdkmanager` で次を導入する。

- Android SDK Platform 36
- Android SDK Build-Tools 36.0.0
- Android Emulator
- Android SDK Platform-Tools
- Android SDK Command-line Tools
- Android 16 / Google APIs / ARM64 v8a system image

`~/.zshrc` に次を設定する。

```bash
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$PATH:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools"
```

Android StudioのDevice ManagerでPixel 9のAVDを作成する。監査端末では `Campus_Circle_API_36` が作成済みである。

## リポジトリの取得

```bash
mkdir -p ~/Developer
cd ~/Developer
git clone git@github.com:ichiro06/campus-circle-event-app.git
cd campus-circle-event-app
```

SSH接続を確認する場合は次を実行する。

```bash
ssh -T git@github.com
```

## 依存関係

`mobile/` が正式製品client、`backend/` が正式製品APIである。ルートNext.jsは別のtechnical verification npm projectとして保持する。作業対象のlockfileに合わせて導入する。

```bash
# 正式製品client
cd ~/Developer/campus-circle-event-app/mobile
npm ci

# Next.js technical verificationを再現する場合だけ
cd ..
npm ci
```

バックエンドの依存範囲は`backend/requirements.txt`、開発用追加依存は`backend/requirements-dev.txt`へ記述する。uvで生成した`requirements.lock`をDocker、`requirements-dev.lock`をlocal testとCIでpip installする。`uv sync`への全面移行は行わず、Before環境のDocker + pipを維持する。

監査時の主な解決済みバージョンは次のとおり。

- Next.js 16.3.5 / React 19.2.4 / TypeScript 5.9.3 / Tailwind CSS 4.3.2
- Expo 57.0.22 / Expo Router 57.0.21 / React Native 0.86.3 / React 19.2.3 / TypeScript 6.0.3
- FastAPI 0.141.1 / Uvicorn 0.52.4 / SQLAlchemy 2.0.52 / psycopg 3.3.5 / Alembic 1.20.0
- pytest 9.1.1 / Ruff 0.16.7 / HTTPX2 2.12.0
- PostgreSQL 16

上記は2026-09-14に生成したlockの解決結果である。入力用requirementsを変更した場合は対応するlockを再生成し、同じPull Requestでreviewする。

## 環境変数と設定

### Next.js

現在のルート `.env.example` はNext.jsからFastAPIへ接続するtechnical verification専用であり、正式モバイル製品の設定ではない。

`.env.example`:

```dotenv
API_BASE_URL=http://localhost:8000
```

コードにも同じデフォルト値があるため、ローカルの標準構成では設定を省略できる。変更する場合は、Git管理外の `.env.local` を作成する。

```bash
cp .env.example .env.local
```

このNext.js用変数へ製品のSupabase secretやGoogle Client Secretを追加しない。

### FastAPI / PostgreSQL製品開発環境

Docker Composeは開発用の `DATABASE_URL` を `backend/compose.yaml` で設定する。

```text
postgresql+psycopg://campus:campus_password@db:5432/campus_circle_app
```

この認証情報はローカル開発専用である。本番環境では使用せず、秘密情報管理方式を別途決定する。

### Expo製品client

モバイルアプリのAPI URLは、Expo標準の`EXPO_PUBLIC_API_BASE_URL`で設定する。`mobile/.env.example`をGit管理し、端末固有値はGit管理外の`mobile/.env.local`へ置く。

```bash
cd ~/Developer/campus-circle-event-app/mobile
cp .env.example .env.local
```

- iOS Simulator: `http://127.0.0.1:8000`
- Android Emulator: `http://10.0.2.2:8000`
- 実機: Macへ到達できるLAN addressを使用する

Expoは`EXPO_PUBLIC_`変数をapp bundleへ埋め込む。API base URL、将来のSupabase URL / publishable key等の公開可能な値だけに使用し、DB password、JWT署名secret、Google Client Secret、Supabase service role key等を置かない。staging / production値をEASで管理する方法、Supabase project値、redirect URIは外部project作成時に確定する。FastAPI側のsecretはRender等のserver-side secretとして管理する。

## 起動

### FastAPIとPostgreSQLの製品開発環境

```bash
cd ~/Developer/campus-circle-event-app/backend
docker compose up -d --build
docker compose ps
```

- FastAPI: `http://localhost:8000`
- OpenAPI UI: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

終了:

```bash
docker compose down
```

通常の `down` ではPostgreSQL volumeを削除しない。データ削除を伴う `down -v` は意図を確認してから実行する。

### 現在のNext.js技術検証画面

FastAPIを先に起動する。

```bash
cd ~/Developer/campus-circle-event-app
npm run dev
```

- トップ: `http://localhost:3000`
- サークル: `http://localhost:3000/circles`
- イベント: `http://localhost:3000/events`

### Expo製品client

```bash
cd ~/Developer/campus-circle-event-app/mobile
npm start
```

実行先を直接指定する場合:

```bash
npm run ios
npm run android
```

Androidでは先にAndroid Emulatorを、iOSではiOS Simulatorを利用可能な状態にする。

## 動作確認

### APIとデータベース

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/circles
curl http://localhost:8000/api/events
```

`/health` の期待値:

```json
{"status":"ok","database":"connected"}
```

### FastAPI code quality

```bash
cd ~/Developer/campus-circle-event-app/backend
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r requirements-dev.lock
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
.venv/bin/alembic history
```

Alembic historyには`20260915_0001 (head)`が表示される。PostgreSQL起動後、正式schemaを初めて適用する場合は次を実行する。

```bash
.venv/bin/alembic upgrade head
```

このrevisionは`app_private`に27 tableを作り、既存の`public.circles` / `public.events`を変更しない。共有・本番DBで`downgrade`を実行してはならない。

### Next.js

```bash
npm run lint
npm run build
```

Google Fontsのbuild時取得は除去済みであり、技術検証のbuildは外部font取得に依存しない。Next.js 16の既定Turbopackが制限環境内で内部portを作れないため、productではないroot technical verificationのbuildは公式`--webpack` optionを使用する。

### Expo製品client

```bash
cd mobile
npm run check
npx expo-doctor@latest
```

`npm run check`はLint、TypeScript型検査、Jest testを順に実行する。

## 確認済み

2026-07-25の監査で確認した項目:

- Gitリポジトリは `main` で `origin/main` と同期していた。
- Git remoteは `git@github.com:ichiro06/campus-circle-event-app.git` である。
- ルートと `mobile/` のnpm依存関係が導入済みで、 `npm ls --depth=0` が成功した。
- Dockerイメージを現在のソースからビルドできた。
- PostgreSQLがhealthyになり、FastAPIが起動した。
- `/health` がデータベース接続成功を返した。
- サークル一覧APIとイベント一覧APIが、それぞれ3件のseedデータを返した。
- Android AVD `Campus_Circle_API_36` とiOS 26.3 Simulatorランタイムが存在する。
- GitHub CLIが認証済みで、SSHのGit remoteが設定されている。
- uv管理のPython 3.13.14と、macOS標準のPython 3.9.6が共存している。
- Next.jsのLintと本番ビルドが成功した。
- ExpoのLintとTypeScript型検査が成功した。
- Expo Doctorの20項目すべてが成功した。

2026-09-14の再監査で確認した項目:

- Expo SDK 57のdependencyを公式互換versionへ揃え、`react-native` 0.86.3と`jest-expo` 57.0.5の整合を確認した。
- Mobile Lint、TypeScript型検査、2 test suites / 5 testsが成功した。
- Expo Doctorの21項目すべてが成功した。
- Next.jsを16.3.5へ更新し、Lint、本番build、root `npm audit` 0件を確認した。
- Docker ComposeからPostgreSQLをhealthy、FastAPIをrunningにし、health、circle list、event listを確認した。
- GitHub ActionsとDependabotのYAML parse、`git diff --check`が成功した。
- FastAPIのRuff、pytest 5件、空のAlembic historyが成功した。
- Python runtime / development依存のlockを生成し、DockerとCIの導入元へ設定した。
- この時点ではGitHub CLIの保存済み認証が無効だったが、2026-09-15にユーザーが再loginした。

2026-09-15のschema監査で確認した項目:

- 正式data dictionaryと`/api/v1`契約、画面状態、認証運用、非機能目標を確定した。
- 初回revision `20260915_0001`を一時PostgreSQL 16へ適用し、`app_private`の27 tableを確認した。
- 一時DBで`downgrade base`により同schemaだけを削除し、再度`upgrade head`できることを確認した。
- 既存の永続volumeとprototype tableは変更していない。
- GitHub CLIは`ichiro06`として認証済みで、`ichiro06/campus-circle-event-app`（Public、default branch `main`、viewer permission `ADMIN`）をGitHub API経由で確認した。
- Git remoteは`git@github.com:ichiro06/campus-circle-event-app.git`のままである。commit、push、共同開発者招待、ruleset変更は行っていない。
- Mobile Lint・TypeScript・2 suites / 5 tests、Expo Doctor 21 / 21、Backend Ruff・format・pytest 5件、Next.js technical verificationのLint・build、Alembic history、CI YAML、`git diff --check`が成功した。

既存の `mobile/README.md` には、iOS SimulatorとAndroid Emulatorで初期画面を表示確認済みと記録されている。2026-07-25の文書監査では両Simulatorの画面表示を再実行していないため、将来のUI変更時には再確認する。

## 未実施・未整備

正式モバイル構成について未実施のもの:

- ExpoからFastAPIへのversioned HTTPS JSON通信
- FastAPIのSupabase Auth JWT検証、circle単位認可、正式`/api/v1` endpointとwrite API
- 正式schema用のSQLAlchemy mapping、repository、正式seed、OpenAPI generated client
- Supabase clientと必要なdependencyの導入
- Supabase development / staging / production projectの作成
- Supabase Auth、PostgreSQL、Storage、policyの接続
- 一般Google OAuth、email/password、iOS版Sign in with Apple
- Google Cloud OAuth consent screen、mobile Client ID、redirect / deep link設定
- Sign in with AppleのApple Developer / Supabase / Expo実値設定と審査確認
- home recommendation、formal search、favorite、my page、circle management、report等の製品機能
- Render service、environment variable、health check、staging / production deploy
- EAS project、build profile、署名、App Store / Google Play submission
- iOS 16.4以上・Android 10以上のSimulator / Emulatorと実機release test記録
- GitHubへpush後の初回CI実行、monitoring、backup / restore、incident response
- Privacy Policy、terms、support URL、account deletion、store privacy申告

Next.js technical verificationについて未実施・非対象のもの:

- 製品機能、正式auth、管理画面、Vercel deploymentは追加しない
- archive、別branchへの移動、削除の時期は未確定

## 注意事項・既知の問題

- `backend/compose.yaml` は既存の `postgres_campus-postgres-data` volumeを再利用する。過去に別のCompose projectが作成したvolumeがある端末では、所有project名の警告が表示されるが、2026-07-25の起動とデータ接続は成功した。
- PostgreSQLのprototype tableだけはFastAPI起動時の`Base.metadata.create_all()`で作る。正式業務tableは`app_private`のAlembic revisionで管理し、prototypeへ正式機能を追加しない。
- seedデータは対象テーブルが空の場合だけ追加され、Docker volumeに永続化される。
- DockerとCIは生成済みlockを使用する。入力用requirementsとlockの更新漏れをPull Requestで確認する。
- `mobile/` の `npm audit` は2026-09-14時点で18件（moderate 14件、high 4件）を報告する。Expo / Metro等の推移依存であり、`npm audit fix --force`はExpo Router / Splash Screenを非互換versionへ変更するため適用しない。DependabotとExpo SDK patchを追跡し、release前に再監査する。
- `~/.zprofile` には `brew shellenv` が重複して記載されている。動作への影響は確認されていないが、将来整理できる。
- Android Emulatorは通常のサンドボックス内コマンドではCPU機能エラーになる場合がある。macOS上で通常起動すると動作する。
- mobile製品clientはAPI未接続である。正式契約は`docs/api-contract.md`で確定済みだが、current read APIはunversioned technical verificationのままである。新規実装は`/api/v1`へ行う。
- Docker Desktop、Simulator、Expo開発サーバーはメモリを使用するため、不要なものは停止する。
