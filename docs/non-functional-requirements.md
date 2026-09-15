# 非機能要件

- 状態: 正式仕様
- 決定日: 2026-09-15
- 適用開始: 初期製品の実装・限定公開・一般公開

## 1. 前提

本書の値は、法政大学から始める2名規模の学生チーム、Expo / FastAPI / PostgreSQL構成、iOS・Androidストア配布を前提に、測定できて運用可能な初期目標として決定した。すべてを同じ時点のrelease blockerにせず、「開発中」「限定公開前」「一般公開前」に分ける。

## 2. 対応環境

| 項目 | 正式基準 | 確認時期 |
| --- | --- | --- |
| iOS | iOS 16.4以上 | CI相当確認とrelease candidate実機 |
| Android | Android 10 / API 29以上、target API 36 | emulatorとrelease candidate実機 |
| 端末 | 初期はphone・縦向きを最適化 | 各release |
| tablet | crashや操作不能を起こさない。専用最適化は将来 | 限定公開前 |
| 最新OS | store提出時点の最新正式OSでsmoke test | 各release |

Expo SDK 57はReact Native 0.86、iOS 16.4以上、Android 7以上を技術上の下限としている。製品としてはsecurity update状況と実機test範囲を考え、Android 10以上に絞る。

## 3. 性能

release build、一般的な直近5年の端末、安定した4GまたはWi-Fi、cache cold / warmを区別して測定する。

| 指標 | 目標 | Gate |
| --- | --- | --- |
| cold start TTID | p75 3.0秒以内 | 限定公開前 |
| warm start TTID | p75 1.5秒以内 | 限定公開前 |
| 初回利用可能内容 TTFD | p75 4.0秒以内 | 限定公開前 |
| local画面反応 | p95 300ミリ秒以内 | 開発中 |
| API GET server時間 | p95 500ミリ秒以内 | 一般公開前 |
| 検索・書込みserver時間 | p95 800ミリ秒以内 | 一般公開前 |
| API p99 | 2.0秒以内 | 一般公開前 |
| mobileから一覧1page表示 | p95 2.5秒以内 | 一般公開前 |
| 一覧JSON | 画像を除き250KB以内 | 開発中 |
| thumbnail | 1枚300KB以内を原則 | 開発中 |

server時間は外部OAuth画面やstore通信を除き、50同時利用、10,000サークル、100,000閲覧記録、50,000お気に入りのtest dataで測定する。未達時はquery plan、index、payload、画像変換を確認してから規模を拡張する。

## 4. 可用性・復旧

| 項目 | 目標 |
| --- | --- |
| productionの月間user-visible availability | 99.5%以上。計画停止も含む |
| API 5xx率 | 15分窓で1%未満。超過を通知 |
| crash-free sessions | telemetry導入後99.5%以上 |
| RPO | 24時間以内 |
| RTO | 8時間以内 |
| restore rehearsal | 四半期ごと |

Renderのsleepを伴うplan等、99.5%を測れない構成は内部開発・限定betaに限る。一般公開前に、常時起動APIと日次backupを満たすplanまたは同等の運用を用意する。この外部契約・課金はリポジトリ変更とは分け、所有者の承認後に行う。

- PostgreSQLは日次backupを取り、少なくとも7世代保持する。
- 無料planでmanaged daily backupがない場合は、暗号化した日次dumpを別のaccess-controlled保存先へ自動保管する。
- Supabase StorageのobjectはDB backupに含まれないため、object inventoryと復旧可能な複製を別に用意する。
- backupにも本番同等のaccess制御、保存期限、削除手順を適用する。

## 5. Offline・回復性

- 公開ホーム・検索・詳細、お気に入り・履歴の最後の正常データをread-onlyで表示する。
- offline表示と最終更新時刻を示す。
- 権限・個人情報・公開状態を変える書込みは自動queue送信しない。
- GETのretry条件、timeout、二重送信防止は`docs/screen-flow.md`と`docs/api-contract.md`を正とする。
- API停止時でもアプリが起動不能や無限loadingにならず、再試行・戻る・supportへの導線を示す。

## 6. Accessibility・使いやすさ

- WCAG 2.2 AAのモバイルに適用できる項目を基準とする。
- 通常文字は4.5:1以上、大きい文字・主要UI図形は3:1以上のcontrastを確保する。
- iOSの主要操作領域は44 x 44pt以上、Androidは48 x 48dp以上とする。
- VoiceOverとTalkBackで順序、role、label、state、errorを理解できる。
- OSの文字サイズ200%で情報欠落、操作不能、横scrollを起こさない。
- 色、位置、音だけを唯一の情報手段にしない。
- motion低減設定と画面の明暗設定を尊重する。
- 限定公開前に、対象学生5人以上のtask testで「検索→詳細→お気に入り」を補助なし完了80%以上とする。

## 7. Security・Privacy

- mobileはOWASP MASVS Level 1、APIはOWASP API Security Top 10を初期baselineとする。
- release時に既知Critical / Highの未対応脆弱性を0件とする。
- 新規Criticalは24時間以内に停止・回避・修正版のいずれか、高は7日、Mediumは30日以内に対応方針を決める。
- 全正式APIでresource-level authorizationをtestし、client表示だけに依存しない。
- access token、password、provider token、審査証拠、完全なemailをlog・analytics・crash reportへ送らない。
- production secretはclient bundle、Git、`.env.example`へ置かない。
- 個人データの利用目的、保持・削除は`docs/data-dictionary.md`と`docs/authentication.md`を正とする。
- account削除はactive systemから7日以内、通常backupから30日以内に消去する。ただし不正・法的保全は理由と期限を限定して別管理する。

## 8. 保守性・品質

- Pull Requestでmobile Lint・TypeScript・Jest、backend Ruff・pytest・Alembic check、Next.js技術検証Lint・buildを実行する。
- 認証・認可matrixの許可／拒否caseは100%自動test対象とする。全体line coverageだけを品質指標にしない。
- 変更した業務ruleには正常、境界、拒否、権限違いのtestを追加する。
- DB schemaはAlembic revisionだけで変更し、production起動時の`create_all()`へ依存しない。
- OpenAPIと生成TypeScript clientの差分をCIで検出する。
- dependencyはlockfileを使い、互換性・license・脆弱性を確認せず自動mergeしない。
- productionへ直接pushせず、staging、migration、smoke test、段階release、rollback判断を記録する。

## 9. 運用目標

| 対象 | 初動・判断目標 |
| --- | --- |
| 管理者申請 | 必要資料が揃ってから5営業日以内に初回判断 |
| 追加情報待ち | 14日で通知、30日無応答で失効 |
| 異議申立て | 最終判断から30日以内受付、10営業日以内回答 |
| 重大ななりすまし・個人情報 | 1営業日以内に初動、危険な権限は確認後即時停止 |
| 通常の違反報告 | 5営業日以内に一次確認 |
| 監査ログ | 365日保持 |
| API運用log | 原則30日保持、個人情報を記録しない |

担当者名、当番表、緊急連絡先は運用開始前に実在するメンバーを割り当てる。推測で文書へ氏名を入れない。

## 10. Cost

- 外部serviceの月額上限そのものは支払責任者が決めるため、未確定の唯一の数値項目として残す。
- 承認された予算の70%で注意、90%で警告、100%到達前にscale・機能・plan変更を人が判断する。
- 自動upgradeや有料addon購入を実装・運用の既定動作にしない。
- 一般公開に必要なavailability・backupと予算が両立しない場合は、公開規模を限定し、要件を黙って下げない。

## 11. 測定記録

各releaseで、端末・OS・build type・network条件・test data量・測定時刻を記録する。目標未達は「失敗」だけでなく、影響、暫定回避、担当、再確認日をissueまたはNotion taskへ残す。

## 12. 参考資料

- [Expo SDK reference](https://docs.expo.dev/versions/latest/)
- [Android app startup time](https://developer.android.com/topic/performance/vitals/launch-time)
- [Android accessibility](https://developer.android.com/guide/topics/ui/accessibility)
- [Apple Accessibility](https://developer.apple.com/accessibility/)
- [OWASP MASVS](https://mas.owasp.org/MASVS/)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [Supabase backups](https://supabase.com/docs/guides/platform/backups)
