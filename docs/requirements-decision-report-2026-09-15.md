# コーディング開始前の未確定事項 決定報告書

- 作成日: 2026-09-15
- 対象: ホウクル iOS・Android初期製品
- 結論: 製品判断を委ねられた9領域を正式化し、外部契約・実在担当者・予算以外は実装可能な受入条件まで具体化した

## 1. 調査対象と判断基準

現在のNotion「第1回要件定義議事録」、要件DB、リポジトリ文書、Expo / FastAPI / PostgreSQLの実装状態を比較し、次を優先して判断した。

1. iOS・Android専用アプリとして両OSで同じ挙動を保てること
2. 2名規模の学生チームが継続してtest・審査・復旧できること
3. Google account本人確認とサークル管理権限を混同しないこと
4. 不要な個人情報を集めず、失敗時にも漏えい・重複処理を起こしにくいこと
5. 数値目標が測定でき、一般公開のgateとして使えること

## 2. 正式決定

### 2.1 画面と状態

4タブをホーム・検索・お気に入り・マイページとし、詳細はstack、manager / operator機能はマイページ配下の保護routeとした。300ミリ秒を超える初回取得でskeleton、再取得では既存表示を保持する。offlineは最後の正常データの閲覧だけを許可し、権限・個人情報を変える書込みを自動queue送信しない。

理由は、mobileで通信断が通常発生する一方、サークル公開・権限付与・報告等の自動再送は二重処理や古い権限での実行が危険だからである。詳細は`docs/screen-flow.md`を正とする。

### 2.2 データ辞書とDB

正式tableをSupabase Data APIへ公開しない`app_private` schemaへ置き、FastAPIだけから扱う。公開revisionと下書き・審査revisionを分離し、UUID、UTC日時、JPY整数、TEXT + CHECKを共通ruleにした。prototypeの`public.circles` / `public.events`は削除しない。

雰囲気は団体の自己申告5指標とし、男女比を1～5の数値にしない。性別個票も収集しない。「仲の良さ」は検証困難、「初心者歓迎度」はtagと重なるため初期ratingから除外する。

### 2.3 API

`/api/v1`、camelCase、UUID、RFC 3339 UTC、RFC 9457 error、不透明cursor、既定20・最大50、重要POSTの24時間idempotencyを採用した。breaking changeは`v2`とし、旧majorを原則180日かactive端末95%移行まで維持する。

mobileアプリはstore審査・利用者更新に時間がかかるため、Web clientより後方互換期間が重要である。

### 2.4 Profile・個人データ

- nicknameはonboarding完了時に必須、画像は任意。
- 大学・学年は任意の自己申告。検索初期値に使うが、認証・権限証明に使わない。
- 生年月日は初期収集、推薦、回復から削除する。年齢制限が将来必要なら、まず年齢確認・年代区分等のより少ないdataで再設計する。
- 興味は任意で推薦へ3点。閲覧履歴は説明後の明示操作で開始し、停止・消去可能、20件または90日の早い方まで。

議事録の機能目的に対して生年月日の必然性がなく、自己申告の大学・生年月日を「本人確認」に使ってもaccount所有は証明できないためである。

### 2.5 推薦

閲覧1点、お気に入り5点を維持し、興味categoryを3点とした。閲覧は同一user・circleで30分に1回、履歴20件／90日、manager自身の団体操作を人気scoreから除外する。上位10件は明示したtie-break、以降はuser・JST日付・filterで決定的shuffleにする。

これにより「毎回完全randomで画面が揺れる」「連打で順位を上げる」「同点順がDB都合で変わる」を避ける。

### 2.6 サークル管理者確認

団体の存在確認と申請者の権限確認を分ける。公式掲載があっても申請者が公式窓口を管理できることを別に確認する。公開情報の弱い団体と非公開団体では、controlled channelへのone-time challenge、既存manager招待、複数member確認を組み合わせる。根拠の弱い初回・private初回・最後のmanager交代は2名確認とする。

初回判断は完全資料から5営業日、追加情報14日、30日無応答で失効、異議申立て30日、回答10営業日とした。証拠原本は判断・異議申立て終了から30日、絶対上限90日で削除し、判断metadataと監査は365日残す。

### 2.7 アカウント回復

nickname・大学・生年月日の一致からemailを表示する旧方式は採用しない。Google / Appleの既存identityで試す、推定したemailへreset送信を依頼する、supportへ進む、の3経路に置き換える。存在有無を同じ表示・時間で応答し、完全・一部emailを返さない。

password reset tokenはone-time・30分、normalized emailのHMACとIPでrate limit、reset後は全sessionを失効する。passwordは15文字以上・少なくとも64文字まで許容、画一的な記号規則を設けず、blocklist・rate limit・password managerとpasteを許可する。

### 2.8 Login

一般Google OAuthとemail/passwordを維持する。大学Google限定・大学domain制限・大学SSOは実装しない。iOS版は、Googleを主要loginとして提供するため、App Store Review Guideline 4.8に対応するSign in with Appleも初期提供する。Android版はGoogleとemail/passwordを初期提供し、Appleは必須にしない。

Appleの教育機関account例外は、学校が発行するaccountを必須とする場合等が対象である。本製品は大学accountを必須にしないため、例外を前提にしない。

### 2.9 非機能要件

最低OS、起動・API速度、99.5%可用性、RPO 24時間、RTO 8時間、accessibility、security修正期限、個人data削除、管理申請SLAを測定条件とともに決定した。一般公開前に必要な常時起動plan・日次backupは費用が発生し得るため、契約操作だけは所有者判断へ残した。

## 3. 現状との差

| 領域 | 現在 | 実装開始時の最初の差分 |
| --- | --- | --- |
| Mobile | 静的初期画面、test基盤 | 4タブ・状態component・API client shell |
| API | unversioned read技術検証 | `/api/v1`共通response / error / request ID |
| DB | prototype public table | `app_private`初回migration。prototypeは保持 |
| Auth | 未導入 | Supabase project値、secure session、email、Google、iOS Apple |
| Authorization | 文書設計のみ | account / membership、resource-level test |
| External | project / store未接続 | ownerがSupabase / Render / EAS / Apple / Googleを作成・共有 |

## 4. まだ開発者本人の操作・決定が必要な事項

- baseline差分review、commit / push、GitHub Actions初回実行、共同開発者招待、branch ruleset設定
- 正式service名、bundle identifier、Android package name
- Apple Developer、Google Play Console、Google Cloud、Supabase、Render、Expo / EASのaccount・owner・支払責任者
- production / staging regionと許容月額。予算70%・90% alertの基準額
- Privacy Policy・利用規約の公開文面と必要に応じた法務確認
- 実在するservice operator、当番、緊急連絡先
- eventの具体release日、chat・notification等の将来優先順位

これらは推測して設定・契約していない。GitHub CLIは2026-09-15に`ichiro06`として接続確認済みで、Public repositoryへのADMIN権限も確認したが、commit / pushやrepository設定変更は行っていない。

## 5. 初期コーディングへの引継ぎ順

1. 初回migrationとschema testを通す。
2. `/api/v1`共通response・Problem Details・request IDを実装する。
3. Expoの4タブと共通状態を作り、公開サークル一覧を縦sliceで接続する。
4. Supabase Auth local / hosted方針を確定した外部値で接続し、email、Google、iOS Appleを実装する。
5. profile / interest / view、favorite、推薦を順に接続する。
6. manager application / membership / revision / operator reviewを認可test付きで実装する。
7. report、account deletion、monitoring、backup / restore rehearsalを通して限定公開する。

## 6. 主な一次資料

- [Apple App Review Guidelines 4.8](https://developer.apple.com/app-store/review/guidelines/)
- [Apple: Offering account deletion in your app](https://developer.apple.com/support/offering-account-deletion-in-your-app/)
- [Expo SDK reference](https://docs.expo.dev/versions/latest/)
- [Android: Build an offline-first app](https://developer.android.com/topic/architecture/data-layer/offline-first)
- [Android: App startup time](https://developer.android.com/topic/performance/vitals/launch-time)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/)
- [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457)
- [Supabase Auth sessions](https://supabase.com/docs/guides/auth/sessions)
- [Supabase backups](https://supabase.com/docs/guides/platform/backups)
- [個人情報保護委員会 個人情報保護法Q&A](https://www.ppc.go.jp/files/pdf/2506_APPI_QA.pdf)
