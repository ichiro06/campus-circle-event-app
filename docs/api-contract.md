# API契約

- 状態: 正式仕様
- 決定日: 2026-09-15
- 最終更新日: 2026-09-19
- 対象: Expo製品clientとFastAPI製品API

## 1. 基本契約

- productionではHTTPSだけを使用する。
- base pathは`/api/v1`とする。現在の`/api/circles`と`/api/events`は技術検証であり、正式契約ではない。
- resource名は複数形の名詞、JSON fieldは`camelCase`とする。
- IDはJSON上でUUID文字列、日時はUTCのRFC 3339、日付は`YYYY-MM-DD`とする。
- 金額は小数ではなく日本円の整数で返す。
- OpenAPIを機械可読な契約の一次情報とし、CIで生成clientとの差分を確認する。
- 認証が必要なrequestは`Authorization: Bearer <access-token>`を使用し、tokenをqueryやbodyへ入れない。

## 2. 正常response

単一resourceは次の形とする。

```json
{
  "data": {
    "id": "508d3a74-2092-4b86-91f4-1ab66a647ac2",
    "name": "Example Circle"
  },
  "meta": {
    "requestId": "ce10e7b9-8636-4d63-a483-bd537f918c77"
  }
}
```

collectionは次の形とする。最終pageでは`nextCursor`を省略し、`hasMore`を`false`にする。

```json
{
  "data": [],
  "page": {
    "nextCursor": "opaque-value",
    "hasMore": true,
    "limit": 20
  },
  "meta": {
    "requestId": "ce10e7b9-8636-4d63-a483-bd537f918c77"
  }
}
```

作成は`201`とresource、更新はresourceを返す`200`、response bodyが不要な削除は`204`とする。

## 3. Error response

errorはRFC 9457のProblem Detailsを使い、`Content-Type: application/problem+json`とする。

```json
{
  "type": "about:blank",
  "title": "入力内容を確認してください",
  "status": 422,
  "detail": "2項目を修正してください",
  "instance": "/api/v1/circles/508d3a74-2092-4b86-91f4-1ab66a647ac2",
  "code": "VALIDATION_ERROR",
  "requestId": "ce10e7b9-8636-4d63-a483-bd537f918c77",
  "errors": [
    {"field": "annualCostMinYen", "code": "greater_than_or_equal"}
  ]
}
```

- 現在はowned domainが未確定のため、runtimeの`type`は`about:blank`とする。clientは`type`をstringのopaque metadataとして保持し、`type`単独でbusiness logicを分岐しない。
- `code`をclient分岐に使うstable application codeとし、`title`と`detail`は表示候補とする。
- 予期しない例外は一般化し、SQL、内部path、stack trace、個人情報を返さない。
- field errorは配列で返し、serverの文章だけをfield特定に使わせない。
- 全responseに追跡可能な`requestId`を付ける。

owned domain取得後は、最初の外部配布・beta公開前に`https://<owned-apex-domain>/problems/<problem-slug>`形式の正式HTTPS URIへ移行する。`problem-slug`はlowercaseのASCII Englishによるkebab-caseとし、version、HTTP status、provider名、`/api/v1/`を含めず、原則として末尾slashを付けない。移行前に仮domain、example domain、Render default domain、Supabase default domainを正式なProblem type URIとして使用しない。

主なstatusは次のとおりである。

| Status | 意味 |
| --- | --- |
| 400 | JSON構文やrequest全体が不正 |
| 401 | tokenなし・無効・期限切れ |
| 403 | 認証済みだが対象resourceの権限なし |
| 404 | 不存在、または存在を漏らさないため同等に扱う対象 |
| 409 | revision競合、状態遷移競合、処理中の同一idempotency key |
| 422 | field validationまたは同じkeyへの異なるpayload |
| 429 | rate limit。可能なら`Retry-After`を返す |
| 503 | 一時的な依存service停止またはmaintenance |

## 4. Pagination・検索

- collectionの既定`limit`は20、最大50とする。
- page番号ではなく不透明なcursorを使用する。
- cursorにはsort値とUUIDを含め、署名して改ざんを検出する。clientは内容を解釈しない。
- cursorは検索条件・sortに紐付け、発行から24時間を上限とする。期限切れは再検索を案内する。
- 全sortはUUIDまで含む安定順序を定義する。
- filterは同一条件内をOR、異なる種類をANDとする。ただし画面表示とAPI説明に明記する。
- 利用者入力はparameter bindingで扱い、検索文字列をSQLへ連結しない。

### 4.1 公開Circle Read

Work 2の正式な公開read endpointは次の2つである。データ源はPostgreSQL 16の`app_private` schemaだけとし、`public.circles` / `public.events`および`/api/circles` / `/api/events`の技術検証とは分離する。

- `GET /api/v1/circles`
- `GET /api/v1/circles/{circleId}`

一覧itemは`id`、`displayName`、`headline`、`summary`、`officialStatus`、`circleType`、`publishedAt`に加え、次の関連情報を返す。DB上nullableなscalarは`null`を許可し、関連がないcollectionは空配列とする。

- `category`: `id`、`name`、`slug`
- `universities`: `id`、`name`、`slug`、`relationshipType`、nullableなcampus名`campus`
- `featuredTags`: `is_featured = true`だけを`display_order`順に最大5件。各itemは`id`、`name`、`slug`
- `activitySchedules`: `weekday`、`timeBand`、`startsAt`、`endsAt`、`note`
- `activityLocations`: `prefecture`、`city`、`facilityName`、`nearestStation`、`isOnline`、`publicNote`

`headline`はカード用キャッチコピー、`summary`は主な活動内容・短い紹介として、それぞれ`circle_revisions.headline`と`circle_revisions.summary`へ対応する。`weekday`は`1`から`7`を月曜から日曜、DBの`NULL`を`irregular`として扱う。

詳細は一覧のcore情報に、`description`、`recruitingStatus`、`memberCountBand`、`campFrequencyCode`、`activityFrequencyCode`、5種類のrating、`genderBalanceCode`、全`tags`、`costs`を加える。tagは`id`、`name`、`slug`、`isFeatured`、costは`costType`、`amountMinYen`、`amountMaxYen`、`label`、`note`を返す。slug、年会費summary、social link、画像・media、revision ID / version、lifecycle・review・operator・manager・evidence・audit・storage object keyは返さない。

公開対象は次の全条件を満たすCircleと、その`published_revision_id`が指すrevisionだけである。一覧と詳細で同じpredicateを使い、不存在・削除済み・非公開・停止・published revisionなし・Circleとの不整合・publishedでないrevisionは、詳細ではすべて同じ`404 NOT_FOUND`とする。

- `circles.deleted_at IS NULL`
- `circles.lifecycle_status = 'published'`
- `circles.published_revision_id IS NOT NULL`
- `circle_revisions.id = circles.published_revision_id`
- `circle_revisions.circle_id = circles.id`
- `circle_revisions.status = 'published'`

一覧で受け付けるfilterは`q`、`officialStatus`、`circleType`、`campFrequencyCode`、`memberCountBand`、`activityFrequencyCode`、`weekday`、`timeBand`、`tagId`、`genderBalanceCode`だけとする。同じfilterの反復はOR、異なるfilter間と`q`はANDで結合する。

`q`はtrim後の1つのliteral substringとして、display name、headline、summary、description、大学名、campus名、tag名、活動場所の都道府県・市区町村・施設名・最寄駅・公開noteを検索する。`%`と`_`はwildcardではなくliteralとしてescapeし、空白だけの明示的な`q`は`422 VALIDATION_ERROR`とする。日本語形態素解析、かな正規化、類義語、relevance rankingは行わない。

sortは`newest`だけで、既定値も`newest`とする。正式順序は`circle_revisions.published_at DESC NULLS LAST, circles.id DESC`である。Circle一覧の`page`だけは共通fieldに必須の`totalCount`を加え、cursor適用前の現在時点における公開条件・filter一致総数を返す。snapshot countではない。

cursorはversion、sort、最後の`publishedAt`とCircle ID、正規化filter、発行・失効時刻をcanonical JSONへ格納し、server環境変数`CURSOR_SIGNING_SECRET`の32 bytes以上の固定secretでHMAC-SHA-256署名したbase64url値とする。有効期限は24時間で、形式・base64・JSON・署名・version・filter・sort・必須payload・期限のいずれかが不正なら、理由を外部へ分けず`400 INVALID_CURSOR`を返す。secretをGitやclientへ置かず、processごとにrandom生成しない。

## 5. Idempotency

次の重要なPOST・状態変更では`Idempotency-Key`を必須とする。

- 違反報告の作成
- サークル管理者申請・招待
- revisionの審査提出・承認・却下・公開
- membershipの付与・解除・移譲
- アカウント削除の開始

keyはclientが論理操作ごとに生成するUUIDで、同じ操作の再送だけ同じ値を使う。serverは24時間、actor、endpoint、payload hash、結果を保存する。

- 同じkey・同じpayload: 初回のstatusと結果を返す。
- 同じkey・異なるpayload: `422 IDEMPOTENCY_KEY_REUSED`。
- 同じkeyが処理中: `409 REQUEST_IN_PROGRESS`と`Retry-After`。
- keyなし: 対象endpointでは`400 IDEMPOTENCY_KEY_REQUIRED`。

このheaderは本サービス内の正式契約であり、IETF draftを成立済み標準として扱わない。

## 6. 更新競合

- 更新対象には`version`整数または`updatedAt`を返す。
- PUT / PATCHはclientが取得したversionを条件として送る。
- versionが異なる場合は`409 REVISION_CONFLICT`を返し、server側を無条件に上書きしない。
- サークル公開情報はpublished revisionとdraft / review revisionを分離する。

## 7. Versioningと互換性

- 追加可能な任意fieldや新endpointは`v1`内で追加できる。
- field削除、意味変更、型変更、必須化は新major pathで行う。
- 旧majorは、新major公開から180日か、直近30日active端末の95%が対応版へ更新するまでの長い方を維持する。
- 廃止予定は可能な範囲で`Deprecation`と`Sunset` header、release note、アプリ内更新案内で知らせる。
- 重大なsecurity事故で安全に維持できない場合だけ、記録した緊急決定により期間を短縮できる。
- 最低対応app versionをAPI側で判定し、危険な旧versionだけ更新必須画面へ誘導できるようにする。

## 8. 初期resource境界

初期実装は次のresourceを単位に設計する。endpointのrequest / response schemaは実装sliceごとにOpenAPIへ追加する。

| Resource | 主な操作 |
| --- | --- |
| circles | 公開一覧・詳細、manager向け担当一覧 |
| recommendations | user別ホーム一覧と説明用signal |
| favorites | 一覧、登録、解除 |
| profiles / interests / views | 本人のprofile・興味・履歴管理 |
| circle-revisions | 下書き、審査提出、差戻し、公開 |
| manager-applications / invitations / memberships | 管理権限の申請・確認・付与・失効 |
| reports | 違反報告作成とoperator処理 |
| operator-reviews / audit-logs | 保護された審査・監査参照 |
| account-deletion | 削除開始、再認証、状態照会 |

イベントresourceは将来機能であり、現在の`/api/events`技術検証をそのまま正式化しない。

## 9. Testと生成物

- FastAPIのPydantic response modelを全正式endpointへ設定する。
- OpenAPI JSONをCIで出力し、意図しないbreaking changeを検出する。
- TypeScript clientはOpenAPIから生成し、生成結果をGit管理してPRで確認する。
- 401 / 403 / 404の区別、他circle ID、他user ID、停止account、失効membershipを自動testする。
- paginationは同点、追加・削除、cursor改ざん、期限切れをtestする。
- idempotencyは同一再送、payload相違、同時request、24時間後をtestする。

## 10. 参考資料

- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457)
- [RFC 9865: Cursor-Based Pagination of SCIM Resources](https://www.rfc-editor.org/rfc/rfc9865)（cursor設計の参考。汎用REST APIの必須標準ではない）
- [RFC 8977: RDAP Query Parameters for Result Sorting and Paging](https://www.rfc-editor.org/rfc/rfc8977)（安定sort設計の参考。汎用REST APIの必須標準ではない）
- [RFC 9745: The Deprecation HTTP Response Header Field](https://www.rfc-editor.org/rfc/rfc9745)
- [RFC 8594: The Sunset HTTP Header Field](https://www.rfc-editor.org/rfc/rfc8594)
- [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/)
