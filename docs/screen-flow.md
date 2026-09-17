# 画面構成・状態設計

- 状態: 正式仕様
- 決定日: 2026-09-15
- 対象: iOS・Android初期製品

## 1. 目的

本書は、初期製品の画面構成、画面遷移、認証境界、loading・empty・error・offline状態の共通挙動を定める。製品Web、PCブラウザ版、別管理Webは対象外である。

## 2. ナビゲーション

初期画面は次の4タブとする。

| タブ | 未ログイン | ログイン済み |
| --- | --- | --- |
| ホーム | 人気順の公開サークル | パーソナライズされた公開サークル |
| 検索 | 利用可 | 利用可 |
| お気に入り | ログイン案内 | お気に入り一覧 |
| マイページ | ログイン・新規登録案内 | プロフィール、履歴、設定、権限別メニュー |

サークル詳細はタブより上のstack画面として開く。サークル管理者・サービス運営者の画面はマイページから入り、同じアプリ内でもserverの権限確認を通過した場合だけ表示・操作できる。

想定するExpo Routerのrouteは次のとおりである。実装時にファイルを分割しても、利用者から見える遷移と権限境界は変えない。

```text
src/app/
  _layout.tsx
  (tabs)/
    _layout.tsx
    index.tsx
    search/index.tsx
    favorites.tsx
    me/index.tsx
  circles/[circleId].tsx
  (auth)/
    sign-in.tsx
    sign-up.tsx
    forgot-password.tsx
    reset-password.tsx
    recovery-help.tsx
  (protected)/
    profile/edit.tsx
    interests.tsx
    history.tsx
    reports/new.tsx
    manager/applications/new.tsx
    manager/applications/[applicationId].tsx
    manager/circles/[circleId]/index.tsx
    manager/circles/[circleId]/edit.tsx
  (operator)/
    reviews/index.tsx
    reviews/[reviewId].tsx
    audit/index.tsx
  legal/
    privacy.tsx
    terms.tsx
    support.tsx
```

## 3. 主な画面遷移

### 3.1 閲覧とお気に入り

1. ホームまたは検索からサークル詳細を開く。
2. 詳細の公開情報を取得できた時点で閲覧を1回記録する。
3. お気に入りを押した未ログイン利用者はログインへ進む。
4. 認証後は元のサークル詳細へ戻し、利用者が改めてお気に入り操作を確定する。ログイン前の書込みを自動実行しない。

### 3.2 サークル管理者申請

1. マイページから管理者申請を開始する。
2. 対象サークルを選ぶか、新規団体の存在確認情報を入力する。
3. 申請者と団体の関係を示す確認方法を選び、必要な情報を提出する。
4. 完了画面と申請状況画面を表示する。
5. `active` membershipになるまで編集画面へ遷移させない。

### 3.3 編集と公開

1. `active`管理者が担当サークルの編集を開始する。
2. 入力途中は端末内の一時下書きとして保持できるが、別サークルへ流用しない。
3. serverへ下書きを保存し、公開確認へ提出する。
4. 競合時は新旧内容を再取得し、利用者に選択させる。上書きを自動実行しない。
5. 公開中revisionと審査中revisionを分け、審査中の内容を一般公開しない。

## 4. Deep Link

- 初期対応は公開サークル詳細、認証callback、password resetとする。
- 認証が必要なlinkは、認証完了後に元の安全なrouteへ戻す。
- 外部から渡されたreturn URLをそのまま開かず、アプリ内の許可routeだけに限定する。
- manager・operator routeはdeep linkの到達可否にかかわらずFastAPIで毎回認可する。
- Universal Links / App Linksのdomain、association file、bundle identifier / package nameは外部project作成時に確定する。

## 5. 共通状態

### 5.1 Loading

- 300ミリ秒以内に完了する処理では、不要な全画面spinnerを出さない。
- 初回一覧・詳細が300ミリ秒を超える場合は、実レイアウトに近いskeletonを表示する。
- 再取得時は前回の正常データを残し、画面全体を空にしない。
- 送信・画像upload等は進行中であることと取消可否を示す。
- screen readerへloading開始・完了を通知する。

### 5.2 Empty

- 単に「データがありません」とせず、0件の理由と次の1操作を示す。
- 検索0件は条件解除、お気に入り0件は検索、履歴0件はホーム、管理対象0件は申請への導線を置く。
- permission不足、通信失敗、未取得をemptyとして表示しない。

### 5.3 Error

| 状態 | 画面の挙動 |
| --- | --- |
| timeout / network | 前回データを保持し、再試行を表示 |
| 401 | token更新を1回だけ試し、失敗時は元の行き先を保持してログインへ誘導 |
| 403 | 権限がないことを説明し、自動再試行しない |
| 404 | 対象が削除・非公開・不存在の可能性を示し、一覧へ戻す |
| 409 | 最新データを再取得し、競合内容を確認させる |
| 422 | 該当入力欄と要約の両方へvalidation errorを示す |
| 429 | `Retry-After`に従い、再試行可能時刻を示す |
| 5xx / maintenance | 利用者の入力を可能な範囲で保持し、再試行または戻る操作を示す |

内部例外、stack trace、token、他人のID、審査証拠を利用者向けメッセージへ含めない。問い合わせ用に`requestId`だけを表示できる。

### 5.4 Offline

- 最後に正常取得した公開ホーム、検索結果、サークル詳細、お気に入り、閲覧履歴をread-onlyで表示できる。
- 「オフライン」と最終更新時刻を常時分かる形で表示する。
- お気に入り変更、違反報告、サークル編集、管理者申請・承認、アカウント変更・削除は無効化し、online復帰後に利用者が明示的に再実行する。
- 重要な書込みを端末内queueから自動送信しない。二重処理や古い権限での実行を避けるためである。
- 端末cacheへtoken、email、非公開revision、管理者確認証拠、operator監査詳細を保存しない。

## 6. Retry・Timeout・二重送信

- 画像以外のAPI timeoutは10秒、画像uploadは60秒を初期値とする。
- GETはnetwork error、timeout、429、502、503、504に限り最大2回再試行する。
- 待機は約0.5秒、1.5秒にjitterを加え、`Retry-After`があれば優先する。
- その他の4xxは自動再試行しない。
- 書込みは利用者の二重押下を無効化する。再送が必要な対象では同じ`Idempotency-Key`を使う。
- アプリ再起動後に未完了の重要書込みを自動再開せず、serverの結果を照会してから利用者に再試行を案内する。

## 7. 画面受入条件

- iOSとAndroidで、未ログイン・一般学生・申請中・manager・operatorの各権限から許可／拒否遷移を確認する。
- loading、empty、offline、401、403、404、409、422、429、5xxをmockまたはtest APIで再現する。
- 戻る操作、Android predictive back、background復帰、deep link、token期限切れでデータや権限を取り違えない。
- 画面表示制御だけで権限を保証せず、保護操作のAPI testでも同じ結果を確認する。
- VoiceOver / TalkBack、文字200%、横方向scrollなし、44pt / 48dp以上の主要操作領域を確認する。

## 8. 参考資料

- [Android: Build an offline-first app](https://developer.android.com/topic/architecture/data-layer/offline-first)
- [Android: App startup time](https://developer.android.com/topic/performance/vitals/launch-time)
- [Apple Human Interface Guidelines: Managing accounts](https://developer.apple.com/design/human-interface-guidelines/managing-accounts)
- [Expo Router authentication](https://docs.expo.dev/router/advanced/authentication/)
