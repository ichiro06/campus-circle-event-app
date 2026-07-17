# Campus Circle Mobile

iOS・Android向けのReact Native / Expoアプリです。

## 使用技術

- Expo SDK 57
- React Native 0.86
- React 19
- TypeScript
- Expo Router

## 初回準備

```bash
cd ~/Developer/campus-circle-event-app/mobile
npm install
```

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
npm run lint
npx tsc --noEmit
npx expo-doctor@latest
```

アプリの画面は `src/app`、共通コンポーネントやAPI処理は今後 `src` 以下に追加します。
