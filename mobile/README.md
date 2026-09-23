# Campus Circle Mobile

React Native / Expoで作成したiOS・Android向けの正式な製品clientです。2026-09-01に、構築済みのExpo＋FastAPI＋PostgreSQL環境を正式構成として再採用しました。

プロジェクト全体の環境構築は`../docs/development-setup.md`、正式構成は`../docs/architecture.md`を参照してください。現在は4タブとCircle詳細のroute shell、共通画面状態、OpenAPI生成型、native fetch transport、公開Circle一覧・詳細のtyped facadeまで実装済みです。画面からのAPI呼出し、認証、検索UI、掲載等の製品機能は未実装です。

## 使用技術

- Expo SDK 57
- React Native 0.86
- React 19
- TypeScript
- Expo Router
- openapi-typescript 6.7.6

## 初回準備

```bash
cd ~/Developer/campus-circle-event-app/mobile
npm ci
cp .env.example .env.local
```

`.env.local`の`EXPO_PUBLIC_API_BASE_URL`は、iOS Simulatorでは`http://127.0.0.1:8000`、標準Android Emulatorでは`http://10.0.2.2:8000`を使用します。`EXPO_PUBLIC_`の値はapp bundleから読めるため、secretやservice role keyを入れないでください。

API base URLにはoriginだけを指定します。path、credentials、query、fragmentは指定できず、release buildではHTTPSが必須です。実機ではMacへ到達できるLAN addressを`.env.local`から注入し、source codeへ固定しません。

## API契約と型生成

`../backend/openapi.json`を唯一の生成元として、型を`src/api/generated/openapi.ts`へ生成します。生成物はGit管理し、直接編集しません。

```bash
npm run api:generate
npm run api:check
```

`api:check`は同じ生成を再実行し、生成fileだけに差分が残れば失敗します。CIではこのcheckを`npm run check`の前に実行します。

## 開発サーバー

```bash
npm start
```

Terminalに表示された操作案内から、実行先を選択します。

```bash
npm run ios
npm run android
```

`npm run ios`にはXcodeとiOS Simulator、`npm run android`にはAndroid StudioとAndroid Emulatorが必要です。

Expo SDK 57のbuild baselineはAndroid `minSdkVersion = 29`、`targetSdkVersion = 36`、iOS deployment target `16.4`です。Android minimumだけを`expo-build-properties`で明示し、SDK既定値と一致するtarget APIとiOS minimumは重複設定していません。

### Android Emulator

macOSでは、Android SDKをTerminalから使えるように `~/.zshrc` へ次を設定します。

```bash
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$PATH:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools"
```

設定後はTerminalを開き直し、Android StudioのDevice Managerで仮想端末を起動してから実行します。このMacでは、Android 16（API 36）のPixel 9仮想端末 `Campus_Circle_API_36` で表示を確認済みです。

```bash
cd ~/Developer/campus-circle-event-app/mobile
npm run android
```

## 検査

```bash
npm run api:check
npm run check
npx expo-doctor@latest
```

`npm run check`はLint、TypeScript型検査、Jest testを実行します。画面は`src/app`、API基盤は`src/api`、testは`__tests__`、公開可能な環境変数の検証は`src/config/environment.ts`にあります。今後の製品機能は、確定済み要件とAPI契約に従ってこのprojectへ実装します。
