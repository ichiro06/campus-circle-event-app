# データ辞書・初期DBスキーマ

- 状態: 正式仕様
- 決定日: 2026-09-15
- 対象: イベント・チャットを除く初期製品

## 1. 基本方針

- PostgreSQL 16を基準とする。
- 正式業務tableは`app_private` schemaへ置き、Supabase Data APIへ公開しない。mobileはFastAPIだけを経由する。
- 主keyはUUID v4、日時は`TIMESTAMPTZ`のUTC、金額はJPY整数とする。
- Supabase Authの`sub` UUIDと`accounts.id`を同じ値にする。local PostgreSQLでもmigrationを再現するため、`auth.users`へのDB外部keyは持たず、FastAPIが検証済みtokenとaccount状態を照合する。
- 状態値はPostgreSQL ENUMではなく`TEXT + CHECK`とする。状態追加・廃止を安全にmigrationできるためである。
- 公開中データと編集・審査中データをrevisionで分ける。
- prototypeの`public.circles` / `public.events`は正式tableではない。初回migrationは削除せず、`app_private`に独立して作成する。
- event、chat、notification、課金、user reviewは初期schemaへ入れない。

## 2. 共通field

特記がない業務tableは次を持つ。

| Field | 型 | Rule |
| --- | --- | --- |
| id | UUID | PK、`gen_random_uuid()` |
| created_at | TIMESTAMPTZ | DBで現在時刻、変更不可 |
| updated_at | TIMESTAMPTZ | 更新時にapplicationが更新 |

物理削除を遅延するresourceだけ`deleted_at`を持つ。公開queryは`deleted_at IS NULL`を必須条件にする。

## 3. Master data

### 3.1 `universities`

| Field | 型 | 必須 | Rule |
| --- | --- | --- | --- |
| id | UUID | yes | PK |
| name | VARCHAR(120) | yes | unique |
| slug | VARCHAR(80) | yes | lowercase unique |
| is_active | BOOLEAN | yes | default true |

初期値は法政大学とする。大学名は認証・管理権限の証明に使わない。

### 3.2 `campuses`

`university_id`、`name`、`slug`、都道府県・市区町村等の任意の所在地、`is_active`を持ち、`(university_id, slug)`をuniqueとする。

### 3.3 `categories`

`name`、`slug`、`display_order`、`is_active`を持つ運営管理master。1つの公開revisionにつき主categoryを1つ選ぶ。初期候補はスポーツ、音楽、文化・芸術、学術・技術、ボランティア、国際交流、メディア、ビジネス・キャリア、アウトドア、その他とし、正式投入値はseed reviewで表記を確認する。

### 3.4 `tags`

`name`、`slug`、`display_order`、`is_active`を持つ運営管理master。managerは既存tagを選び、新規語は申請して運営確認後に追加する。自由入力文字列をそのまま公開tagにしない。

## 4. Account・profile

### 4.1 `accounts`

| Field | 型 | 必須 | Rule |
| --- | --- | --- | --- |
| id | UUID | yes | Supabase Auth `sub`と同値、PK |
| status | TEXT | yes | `active`, `suspended`, `deletion_pending`, `deleted` |
| history_collection_enabled | BOOLEAN | yes | default false。説明後の明示操作でtrue |
| terms_accepted_at | TIMESTAMPTZ | conditional | 利用開始前に必須 |
| privacy_notice_version | VARCHAR(40) | conditional | 同意時version |
| deletion_requested_at | TIMESTAMPTZ | no | 削除受付時刻 |
| created_at / updated_at | TIMESTAMPTZ | yes | common rule |

email、password hash、OAuth provider tokenを複製しない。login identityはSupabase Authを正とする。

### 4.2 `profiles`

| Field | 型 | 必須 | Rule |
| --- | --- | --- | --- |
| user_id | UUID | yes | PK、`accounts.id` FK、cascade |
| nickname | VARCHAR(40) | onboarding後 | trim後2～40文字、不適切語確認 |
| avatar_asset_id | UUID | no | private upload後のmedia参照 |
| university_id | UUID | no | 自己申告、検索初期値にだけ利用 |
| school_year_code | TEXT | no | `undergrad_1`～`undergrad_6`, `master_1`, `master_2`, `doctoral`, `other`, `not_disclosed` |
| onboarding_completed_at | TIMESTAMPTZ | no | 完了時刻 |
| updated_at | TIMESTAMPTZ | yes | 更新時刻 |

生年月日は初期収集しない。大学・学年は任意で、認証、年齢確認、manager権限確認には使用しない。

### 4.3 `profile_interests`

`user_id`と`category_id`の複合PK。本人が任意選択し、cold-start推薦と検索初期値に使う。

### 4.4 `circle_views`

`id`、`user_id`、`circle_id`、`viewed_at`、`is_counted`、`excluded_reason`を持つ。公開詳細の取得成功時だけ作成し、同一user・circleの30分以内の再閲覧は推薦scoreへ数えない。利用者に見せる履歴は新しい順20件か90日の早い方までとする。

### 4.5 `favorites`

`user_id`、`circle_id`、`created_at`を持ち、`(user_id, circle_id)`をuniqueとする。削除は解除として物理削除し、監査対象操作にはしない。

## 5. Circle・公開情報

### 5.1 `circles`

| Field | 型 | 必須 | Rule |
| --- | --- | --- | --- |
| id | UUID | yes | PK |
| slug | VARCHAR(100) | yes | lowercase unique、公開URL用 |
| lifecycle_status | TEXT | yes | `draft`, `in_review`, `published`, `suspended`, `archived` |
| official_status | TEXT | yes | `official`, `unofficial`, `unknown` |
| verification_type | TEXT | yes | `official_public`, `public_unverified`, `private` |
| published_revision_id | UUID | no | 現在公開中revision。循環FKはmigration後に追加 |
| created_by_user_id | UUID | no | account削除後はnull可 |
| created_at / updated_at / deleted_at | TIMESTAMPTZ | conditional | common rule |

`verification_type`は団体・申請者の確認方法を選ぶ分類であり、アプリ上の公開／非公開設定を意味しない。

### 5.2 `circle_universities`

`circle_id`、`university_id`、任意の`campus_id`、`relationship_type`を持つ。`relationship_type`は`primary`, `participating`, `activity_base`。ホウクルでもインカレ団体の参加大学を保持できる。

### 5.3 `circle_revisions`

| Field | 型 | 必須 | Rule |
| --- | --- | --- | --- |
| id | UUID | yes | PK |
| circle_id | UUID | yes | circles FK |
| version_no | INTEGER | yes | circle内で1から採番、unique |
| status | TEXT | yes | `draft`, `in_review`, `changes_requested`, `approved`, `published`, `rejected`, `superseded` |
| display_name | VARCHAR(120) | yes | 公開名 |
| circle_type | TEXT | yes | `circle`, `club`, `intercollegiate`, `student_organization` |
| category_id | UUID | yes | 主category |
| headline | VARCHAR(100) | yes | card用短文 |
| summary | VARCHAR(300) | yes | card・検索用概要 |
| description | TEXT | yes | 詳細。上限5,000文字 |
| recruiting_status | TEXT | yes | `open`, `seasonal`, `closed`, `unknown` |
| member_count_band | TEXT | no | `1_10`, `11_30`, `31_80`, `81_150`, `151_plus`, `not_disclosed` |
| camp_frequency_code | TEXT | no | `none`, `once_year`, `twice_year`, `three_plus_year`, `unknown` |
| activity_frequency_code | TEXT | no | `less_monthly`, `monthly`, `two_three_monthly`, `weekly`, `two_three_weekly`, `four_plus_weekly`, `irregular` |
| annual_cost_min_yen / max_yen | INTEGER | no | 0以上、min <= max |
| rating_* | SMALLINT | no | 後述の4指標とcareer。1～5 |
| gender_balance_code | TEXT | no | 後述。個人genderは保持しない |
| submitted_by_user_id | UUID | no | 審査提出者 |
| submitted_at / reviewed_at / published_at | TIMESTAMPTZ | no | 状態に応じて記録 |
| review_note | TEXT | no | managerへ返す理由。証拠原本を含めない |
| created_at / updated_at | TIMESTAMPTZ | yes | common rule |

### 5.4 `circle_revision_tags`

`revision_id`と`tag_id`の複合PK。cardに出す`is_featured`と`display_order`を持ち、featuredは最大5件とする。

### 5.5 `activity_schedules`

revision単位で`weekday`（1=月～7=日、null=不定期）、`time_band`（`morning`, `daytime`, `evening`, `night`, `all_day`, `irregular`）、任意の開始・終了時刻、noteを持つ。終了は開始より後とする。

### 5.6 `activity_locations`

revision単位で都道府県、市区町村、施設名、最寄駅、online flag、任意の公開説明を持つ。正確な集合場所や個人住所は公開fieldへ入れない。

### 5.7 `circle_costs`

revision単位で`cost_type`（`admission`, `annual`, `monthly`, `per_event`, `other`）、`amount_min_yen`、`amount_max_yen`、`label`、`note`を持つ。費用なしは0円のannual summaryとし、nullを0円の意味にしない。

### 5.8 `social_links`

revision単位で`service`（初期は`instagram`, `line`, `website`, `other`）、URL、表示順を持つ。許可schemeとhostを検証し、script等を受け付けない。

### 5.9 `media_assets` / `circle_revision_media`

`media_assets`はStorage object key、owner、MIME、size、width、height、checksum、scan status、削除時刻を保持する。bucketの公開URLを永続的な権限根拠にしない。`circle_revision_media`はrevisionとの関係、役割（`cover`, `gallery`）、代替text、表示順を持つ。

## 6. 雰囲気・特徴の定義

値はサークル管理者の自己申告であり、「団体による自己申告」と表示する。運営確認は掲載基準の確認であり、実態を保証する認証マークにしない。

| Field | 1 | 3 | 5 |
| --- | --- | --- | --- |
| drinking_frequency_rating | なし | 月1回程度 | 週1回以上 |
| liveliness_rating | 落ち着いている | どちらもある | とても賑やか |
| commitment_rating | 気軽な交流中心 | 継続的に活動 | 大会・公演・成果を強く重視 |
| attendance_flexibility_rating | 原則参加 | 活動により異なる | 完全に自由 |
| career_opportunity_rating | 役割機会は少ない | 役割を選べる | 継続的な企画・対外活動機会がある |

飲み会は2=`年1～3回`、3=`月1回程度`、4=`月2～3回`とする。尺度は将来変更できるよう説明versionを保持する。

男女比は5段階scoreにしない。任意の自己申告`gender_balance_code`を`women_majority`, `balanced`, `men_majority`, `mixed_or_other`, `not_disclosed`から選ぶ。個人ごとのgender、人数、推測値は収集しない。「仲の良さ」は検証困難、「初心者歓迎度」はtagと重複するため初期ratingへ追加しない。

## 7. 管理権限・審査

### 7.1 `manager_applications`

申請者、対象circle、状態（`submitted`, `evidence_requested`, `under_review`, `approved`, `rejected`, `withdrawn`, `expired`, `appealed`）、確認方式、申請理由、提出・期限・判断・異議申立て時刻、担当operator、判断理由を持つ。申請中はmembershipを作らず、承認transactionで作る。

### 7.2 `manager_evidence`

application、evidence type、Storage object keyまたは確認先、提出時刻、確認時刻、削除予定時刻、削除時刻を持つ。原本をaudit logへ複製しない。標準方式で学生証を求めない。

### 7.3 `manager_invitations`

circle、招待するmanager、対象userまたはHMAC化email、one-time token hash、`pending / accepted / expired / revoked`、7日後の期限を持つ。plain tokenをDBへ保存しない。受諾だけでactiveにせず、運営者の最終承認を必要とする。

### 7.4 `circle_memberships`

`user_id`、`circle_id`、`role=manager`、状態（`active`, `suspended`, `revoked`, `expired`）、付与元application、開始・終了・解除者・解除理由を持つ。同一user・circleでactiveを1件だけ許す。activeだけが編集・提出できる。

### 7.5 `service_operators`

`user_id` PK、`status=active/suspended/revoked`、MFA確認時刻、付与者・付与理由を持つ。公開signupから作らない。重要操作時にMFA assuranceと再認証時刻を確認する。

## 8. Safety・operation

### 8.1 `reports`

reporter、対象circle、category、自由記述、状態（`submitted`, `triaged`, `investigating`, `resolved`, `dismissed`）、担当operator、判断理由、解決時刻を持つ。reporter情報と内容を一般公開しない。

### 8.2 `audit_logs`

actor user、actor type、action、target type / UUID、circle、before / afterの機微でないJSON、reason、request ID、結果、作成時刻を持つappend-only table。password、token、完全なemail、証拠原本、自由記述の個人情報を入れない。更新・削除は通常のapplication roleに許可しない。

### 8.3 `idempotency_records`

actor、endpoint、key UUID、payload hash、処理状態、status code、response reference、作成・期限を持つ。`(actor, endpoint, key)`をunique、保持24時間とする。responseへ個人情報本体を複製せず、必要ならresource IDを参照する。

## 9. 推薦rule

- 直近20件か90日の早い方のcounted viewをcategoryへ1点加算する。
- お気に入り中のサークルのcategoryへ5点加算する。
- onboardingで選んだ興味categoryへ3点加算する。
- counted viewが5件未満なら、興味scoreの後に公開サークルのお気に入り数を使う。興味もない場合はお気に入り数順とする。
- 同一user・circleの閲覧は30分に1回だけ数える。詳細取得成功前、未ログイン、停止account、非公開・削除circleは数えない。
- manager / operatorによる自分の担当circleの閲覧・お気に入りは公開人気scoreから除外する。
- 上位10件はcategory score降順、公開お気に入り数降順、`published_at`降順、circle UUID昇順で決める。
- 11件目以降はuser ID、JST日付、filterをseedにした決定的shuffleとし、その日・同一条件では順序を安定させる。
- 1日100件を超える詳細取得、1日30回を超えるfavorite toggle等の異常signalは公開rankingから一時除外し、24時間以内に自動解除または運営確認する。
- 推薦には「最近見たカテゴリ」「興味」「人気」等の説明labelを表示する。
- 履歴停止・消去は次回取得から即時反映する。有料順位を導入する場合は自然順位と混ぜず、広告表示と別決定を必要とする。

## 10. 保持・削除

| Data | Retention / deletion |
| --- | --- |
| Auth identity | account削除時にSupabase Authから削除。active systemは7日以内 |
| profile、interest、favorite | userが変更・削除するかaccount削除まで |
| circle view | 最大20件か90日の早い方。停止後は新規収集しない |
| manager evidence原本 | 最終判断または異議申立て終了から30日、絶対上限90日 |
| application・membership判断metadata | 関係終了後365日 |
| audit log | 365日。事故・法的保全は理由・access・期限を記録し最大3年 |
| report | 解決後365日。法的保全は例外管理 |
| idempotency record | 24時間 |
| API運用log | 原則30日、個人情報を記録しない |
| 削除済み個人dataのbackup | 通常30日以内に世代更新で消去 |

account削除時はmembership、未完了申請、招待をtransactionで失効する。circleの公開情報は別managerまたは運営管理へ残し、自動物理削除しない。最後のmanagerが消える場合は未割当・編集停止として運営確認へ送る。

## 11. Index・constraintの最低基準

- 全FKの検索側へ必要なindexを明示する。
- 公開一覧は`lifecycle_status`, `published_revision_id`、公開日時、categoryの組合せを測定してindex化する。
- favoritesはuser一覧とcircle集計の両方向にindexを持つ。
- viewsは`(user_id, viewed_at desc)`と`(user_id, circle_id, viewed_at desc)`を持つ。
- active membership、未完了application、pending invitationにはpartial unique indexを使う。
- min/max金額、rating 1～5、曜日1～7、終了時刻、状態遷移をDB CHECKとservice ruleの両方で守る。
- FK削除ruleは意図を明示し、利用者・circle削除で監査根拠を誤ってcascadeしない。

## 12. 初回Alembic revision

初回revisionは`app_private` schemaと本書の初期table・constraint・indexだけを作る。prototype tableを削除・移行せず、event tableも正式化しない。migrationは空のPostgreSQL 16に`upgrade head`、`check`、`downgrade base`、再`upgrade head`を実行して検証する。

本書とSQLAlchemy metadata、migrationに差が出た場合は、本書を黙って変更せず、decision historyと要件への影響を確認する。

## 13. 参考資料

- [PostgreSQL 16 constraints](https://www.postgresql.org/docs/16/ddl-constraints.html)
- [PostgreSQL UUID type](https://www.postgresql.org/docs/16/datatype-uuid.html)
- [Supabase: Securing your API](https://supabase.com/docs/guides/api/securing-your-api)
- [Supabase: Tables and Data](https://supabase.com/docs/guides/database/tables)
- [個人情報保護委員会 個人情報保護法Q&A](https://www.ppc.go.jp/files/pdf/2506_APPI_QA.pdf)
