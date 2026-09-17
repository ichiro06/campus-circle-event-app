# 要件定義レビュー報告

- 初回レビュー日: 2026-08-21
- 方針再レビュー日: 2026-09-01
- 詳細確定日: 2026-09-15
- 状態: モバイル専用Before構成と、初期コーディングに必要な詳細要件を反映済み

## 1. 結論

2026-08-21の初回レビューで判明した、画面例外、data定義、API、DB、privacy、推薦、manager確認、account recovery、非機能目標の不足は、2026-09-15に解消した。判断根拠、具体値、変更した旧方針は`docs/requirements-decision-report-2026-09-15.md`とDEC-051～058を正とする。

正式構成は次のとおりであり、Web製品は開発しない。

```text
iOS / Android React Native / Expo app
  -> /api/v1 HTTPS JSON
  -> FastAPI on Render
  -> app_private schema on Supabase PostgreSQL

Authentication: Supabase Auth
Storage: Supabase Storage
Build / submit: EAS
Distribution: App Store / Google Play
```

## 2. レビュー履歴

### 2026-08-21

当時の議事録中の「Webアプリケーション」という表現を根拠に、Next.js + Supabase + Vercelを推奨した。この方針は後に正式に置き換えられ、DEC-031 / DEC-032へ履歴として残っている。

### 2026-09-01

ユーザーと共同開発者が「製品Webは開発せず、構築済みBefore環境でiOS・Androidだけを開発する」と再確認した。Expo + FastAPI + PostgreSQL、Render + Supabase + EAS +各storeをDEC-044～048で再採用した。

### 2026-09-15

ユーザーから、前回列挙した詳細不足について製品の完成形・現状・公式資料をもとに判断を委任された。実装・運用できる受入条件へ落とし込み、DEC-051～058で確定した。

## 3. 2026-09-15に解消した指摘

| 旧指摘 | 決定 | 正式文書 |
| --- | --- | --- |
| 画面遷移・状態がない | 4タブ、保護route、loading / empty / error / offline、retry / timeout | `docs/screen-flow.md` |
| data dictionaryがない | 27 table、field、constraint、rating / cost / schedule、保持 | `docs/data-dictionary.md` |
| API契約がない | `/api/v1`、envelope、RFC 9457、cursor、idempotency、互換期間 | `docs/api-contract.md` |
| 初回DB schemaがない | `app_private`初回Alembic revision。prototypeは保持 | migration、DEC-054 |
| profileの目的・保持がない | 大学・学年は任意、生年月日なし、履歴20件／90日 | requirements、authentication |
| 推薦のtie・abuse・randomがない | 安定sort、30分重複除外、日次決定的shuffle | data dictionary、DEC-055 |
| manager証拠・SLA・appealがない | 団体区分別証拠、5営業日、異議申立て、30／90日原本削除 | authentication、DEC-056 |
| email忘れが危険 | emailを表示せずprovider / reset / supportへ置換 | authentication、DEC-052 |
| password reset詳細がない | 共通応答、one-time 30分、rate limit、全session失効 | authentication、DEC-052 |
| iOS Google login審査が未確定 | Sign in with AppleをiOS初期要件化 | authentication、DEC-057 |
| 非機能値がない | OS、性能、可用性、backup、accessibility、security、SLA | `docs/non-functional-requirements.md` |

## 4. 重要な設計判断

### AuthenticationとAuthorization

Google、Apple、email/passwordの成功はlogin identityの確認だけである。サークル管理権限は`user_id`・`circle_id`のactive membershipをFastAPIが確認した場合だけ認める。公式掲載は団体の存在を補強しても、申請者の権限を自動証明しない。

### 個人データ

初期目的のない生年月日は収集しない。大学・学年は任意で、認証やmanager確認へ流用しない。閲覧履歴は説明後に有効化し、停止・消去を提供する。証拠原本は長期監査logに複製しない。

### Offline

通信断でも公開cacheを見られるようにする一方、公開・report・権限付与等を勝手に再送しない。このサービスでは「後で同期される便利さ」より、重複・権限変化・誤公開の回避を優先する。

### DB

Supabaseを使ってもmobileから業務tableへ直接書かず、Data APIへ公開しない`app_private` schemaをFastAPIから利用する。prototypeは削除せず、正式実装を別schemaで始める。

## 5. 非機能要件の評価

数値は大規模serviceを装うものではなく、2名チームが測れる初期基準とした。

- iOS 16.4以上、Android 10 / API 29以上
- cold start TTID p75 3.0秒、API GET p95 500ms
- 一般公開availability 99.5%、RPO 24h、RTO 8h
- WCAG 2.2 AA相当、VoiceOver / TalkBack、44pt / 48dp
- MASVS L1、API Security Top 10、release時Critical / High 0件
- manager申請5営業日、重大report 1営業日、通常report 5営業日

Renderのsleep回避、managed backup、監視等に費用が必要なら、限定betaと一般公開を分ける。支払権限のない自動契約は行わず、要件を黙って下げない。

## 6. 依然として人が決める事項

- 正式service名、大学ロゴ・画像・公開情報の利用範囲
- categories / tags seedの最終表記
- external projectのowner、region、plan、支払責任者、月額上限
- bundle identifier、Android package name、link domain
- Privacy Policy、利用規約、Support URLの公開文面
- 実在service operator、当番、第二確認者、緊急連絡先
- event / chat / notification / monetizationの時期・個別要件
- Next.js技術検証のarchive時期

## 7. 実装への引継ぎ

正式な公開circle read vertical sliceから開始してよい。順序と禁止事項は`docs/coding-readiness.md`を正とし、外部project値が必要になるまではlocalのPostgreSQL 16と両Simulatorで進める。

## 8. 参考資料

- [Expo SDK reference](https://docs.expo.dev/versions/latest/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Apple account deletion](https://developer.apple.com/support/offering-account-deletion-in-your-app/)
- [Android offline-first](https://developer.android.com/topic/architecture/data-layer/offline-first)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/)
- [OWASP MASVS](https://mas.owasp.org/MASVS/)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [Supabase backups](https://supabase.com/docs/guides/platform/backups)
