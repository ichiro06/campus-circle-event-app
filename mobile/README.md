# Campus Circle Mobile

React Native / Expoで作成したiOS・Android向けの正式な製品clientです。2026-09-01に、構築済みのExpo＋FastAPI＋PostgreSQL環境を正式構成として再採用しました。

プロジェクト全体の環境構築は`../docs/development-setup.md`、正式構成は`../docs/architecture.md`を参照してください。現在は静的な初期画面まで実装済みで、FastAPI接続、認証、検索、掲載等の製品機能は未実装です。

## 使用技術

- Expo SDK 57
- React Native 0.86
- React 19
- TypeScript
- Expo Router

## 初回準備

```bash
cd ~/Developer/campus-circle-event-app/mobile
npm ci
cp .env.example .env.local
```

`.env.local`の`EXPO_PUBLIC_API_BASE_URL`は、iOS Simulatorでは`http://127.0.0.1:8000`、標準Android Emulatorでは`http://10.0.2.2:8000`を使用します。`EXPO_PUBLIC_`の値はapp bundleから読めるため、secretやservice role keyを入れないでください。

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
npm run check
npx expo-doctor@latest
```

`npm run check`はLint、TypeScript型検査、Jest testを実行します。画面は`src/app`、testは`__tests__`、公開可能な環境変数の検証は`src/config/environment.ts`にあります。今後の製品機能は、確定済み要件とAPI契約に従ってこのprojectへ実装します。
