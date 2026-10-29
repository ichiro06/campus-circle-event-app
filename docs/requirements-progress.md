# 要件定義の進捗

- 最終更新日: 2026-10-18（DEC-069のモバイルUI方針を反映）
- 状態: `W3 Mobile Foundation`は完了。`W4 Public Circle Slice`は公開read範囲の実装・検証が完了（public read slice COMPLETE。FR-001 / FR-005 / FR-017 / FR-018の全体完了ではない）。Personalized Home Contract、Home Production Ready、External Beta / Releaseは未決事項が残りBLOCKED（`docs/coding-readiness.md` 3.1）

## 1. 情報源

要件の一次情報はNotion「アプリ開発プロジェクトWiki」→「議事録」DB→「第1回要件定義議事録」である。`docs/requirements.md`は実装確認用snapshot、技術・認証・決定はリポジトリ文書を正とする。過去のCloud上Markdownは参照履歴であり、今後の更新元ではない。

今回の詳細決定は、ユーザーから判断を委任された範囲について公式資料と現在の構成を調査し、DEC-051～058として記録した。外部契約、支払、実在担当者は推測していない。

## 2. 確定済み

### 製品・構成

- 初期製品はiOS・Androidアプリだけ。製品Web、PC browser、別管理Webは作らない。
- `mobile/`のReact Native / Expo / TypeScript / Expo Routerを正式clientとする。
- `backend/`のFastAPI / Python / Pydantic / SQLAlchemy / psycopgを正式APIとする。
- localはPostgreSQL 16、productionはSupabase PostgreSQL / Auth / Storage、APIはRender、build / submitはEAS、配布はApp Store / Google Playとする。
- root Next.jsはread技術検証だけに残し、製品機能を追加しない。

### 初期機能

- personalized home、法政大学向けcircle search、favorite、my page
- circle card / detail、manager edit・審査状態、report、share
- 4タブnavigationと認証・manager・operatorの保護route
- loading、empty、error、offline、retry、timeout、deep linkの共通挙動

### Data・推薦

- 正式tableは`app_private` schema、UUID、UTC日時、JPY整数、`TEXT + CHECK`を使う。
- 公開revisionと下書き・審査revisionを分離する。
- category・tagは運営master、主categoryは1つ、tagは複数とする。
- ratingは団体自己申告の5指標（integer 1～5、`null`は未回答）。男女比はcategorical value（`null`は未回答、`not_disclosed`は明示的な非公開で別状態）で、個人genderを収集しない（DEC-062、2026-10-06）。
  - FR-017 rating contract（保持・表示仕様）: **RESOLVED**。ただしFR-017全体は**PARTIAL**のままであり、DEC-062の成立は全体完了ではない。
  - 5 ratingの検索filter / sort / ranking利用: S5 MVPでは**使用しない（EXCLUDED / RESOLVED FOR S5 MVP）**（DEC-063、2026-10-07）。保持とCircle Detail表示は維持し、将来の検索利用は別Human Decision。男女比はcategorical filterで、Search UIの選択肢は回答済み4 categoryのみ（下記「検索（S5）」）。
  - 「仲の良さ」「初心者歓迎度」は初期ratingから除外。
- 閲覧1点、お気に入り5点、興味3点。同一user・circleの閲覧は30分に1回。
- 上位10件は安定sort、以降はuser・JST日付・filterで決定的shuffleとする。
- 生年月日は初期収集しない。大学・学年は任意、閲覧履歴は明示操作後に最大20件または90日。

### 検索（S5、DEC-063、2026-10-07）

- DEC-063（S5検索のrating除外・男女比filter公開範囲・離散filter UI）: **RESOLVED**（Human Approved: YES）。
- HD-S1 / HD-S2 / HD-S3: **RESOLVED**。
  - 5 rating S5 search: **EXCLUDED / RESOLVED FOR S5 MVP**（search filter / sort / rankingに使わない。保持・Circle Detail表示は維持。W4 rollbackではない）。
  - gender balance Search UI scope: **RESOLVED**（回答済み4 categoryのみ。`not_disclosed`と`null`はUI filter optionに出さない。filter未指定時は`null`・`not_disclosed`を除外しない）。
  - camp / member / activity filter UI: **RESOLVED**（`campFrequencyCode` / `memberCountBand` / `activityFrequencyCode`は離散値chip複数選択。レンジスライダーはS5 MVPで不採用）。
- same-filter OR / different-filter ANDは既存API contractであり、DEC-063で新規決定していない。backend APIのAPI capability（`genderBalanceCode`が`not_disclosed`を受理できること等）は変更していない。
- S5_SEARCH_ENTRY_GATE: **READY_WITH_SCOPE_LIMIT**（維持）。S5全体の完了（COMPLETE / READY_ALL）ではない。

### 検索（S5、DEC-066、2026-10-13）

DEC-066（S5検索のエリア段階実装・年間費用・通常タグ検索・活動時間帯）: **RESOLVED / HUMAN_APPROVED**（承認者: 一朗、ゆうすけ）。共通仕様は`docs/search-s5-spec.md`。意思決定の状態であり、実装完了ではない。

| 領域 | 意思決定 | 実装 | 要件の完了状態 |
| --- | --- | --- | --- |
| HD-1 エリア（D1） | RESOLVED / HUMAN_APPROVED（都道府県・市区町村を先行、沿線・駅は後続。選択粒度はDEC-068 H7） | 未実装 | 沿線・駅の実装まで元のMust要件に対して**PARTIAL** |
| HD-2 年間費用（D2） | RESOLVED / HUMAN_APPROVED（自己申告の入会初年度の標準的な年間費用、containment、範囲スライダー。上端と欠損値はDEC-068 H1・H2） | 未実装 | 未完了。上端の内部表現・NULLのDB符号化・カード / response表示は設計課題 |
| HD-3 タグ（D3） | RESOLVED / HUMAN_APPROVED（通常タグ検索7語彙、人気タグの特別扱いは初期除外。非アクティブ化の意味はDEC-068 H5） | `tagId` filterのみ。公開タグ一覧APIは未実装 | 人気タグの特別機能を提供しないまま元の「人気タグ」要件をCOMPLETEにしない |
| HD-4 活動時間帯（D4） | RESOLVED / HUMAN_APPROVED（`all_day` / `irregular`の意味論、曜日×時間帯は同一activity schedule） | backendの公開Circle一覧filterへ実装（2026-10-18のD4実装PR。同一activity schedule行での単一存在判定、通常4時間帯指定で`all_day`も一致）。mobileの曜日・時間帯UIは未実装。[過去] D4実装PR前は曜日と時間帯を独立判定し、`all_day`は展開なし | backend sliceのみ実装。S5全体は未完了 |

- 沿線・駅は削除した要件ではなく、実装を後続段階へ移した要件である。後続の開発日、リリース日、鉄道マスターの提供元、ライセンス、費用は未決。
- DEC-062 / DEC-063は変更しない（5 rating検索除外、男女比UIは回答済み4 category、合宿・規模・活動頻度は離散chip、W4 COMPLETE、FR-017 PARTIAL）。レンジスライダー不採用は合宿・規模・活動頻度だけで、年間費用のスライダーは維持する。
- `S5_DECISIONS = HUMAN_APPROVED`、`S5_SEARCH_ENTRY_GATE = READY_WITH_SCOPE_LIMIT`（維持）、`S5_IMPLEMENTATION = NOT_COMPLETE`。S5全体のCOMPLETE / READY_ALLは宣言しない。

### 検索の残課題の補完（S5、DEC-068、2026-10-18）

DEC-068（S5検索の残課題：年間費用上端・無制限予算・非アクティブタグ・行政区粒度を確定）: **RESOLVED / HUMAN_APPROVED**（H1・H2・H5・H7）。DEC-066・DEC-067の既存承認は変更しない。共通仕様は`docs/search-s5-spec.md`。意思決定の状態であり、実装完了ではない。

| 項目 | 意思決定 | 実装 | 要件の完了状態 |
| --- | --- | --- | --- |
| H1 年間費用の上端 | RESOLVED / HUMAN_APPROVED（「20,000円以上」は予算上限なし。実額を切り捨てない） | 未実装 | 未完了。内部表現・API parameter形式は技術設計 / 実装PR |
| H2 上限なし予算と欠損値 | RESOLVED / HUMAN_APPROVED（上限なしでは下限既知・上限不明を条件付きで一致。未回答は不一致。filter無指定では除外しない） | 未実装 | 未完了。DB符号化・CHECK・migrationは技術設計 / PRレビュー |
| H5 タグの非アクティブ化 | RESOLVED / HUMAN_APPROVED（R1。新規選択肢から除外し、既存表示・`tagId`検索・タグ名キーワード検索は維持） | 公開タグ一覧APIは未実装。`tags.is_active`は初回migrationで定義済みだがORM未マッピング。実DBへの適用は未確認 | 未完了 |
| H7 市区町村の選択粒度 | RESOLVED / HUMAN_APPROVED（政令指定都市は市単位、東京都23特別区は区単位。行政区情報を失わない） | 未実装（`city`は自由記述で地域コードの列なし） | 沿線・駅の実装までエリア検索はPARTIAL |

- 未決: H4（年間費用のカード・response表示）は後続に保留。H6（地域マスターの取得元・利用条件・更新方式）とH9（オンライン併用データの判別 / 移行基準）は技術設計・PRレビューで具体化する。H3・H8・H10は既存承認の範囲内で解釈する。
- 事実訂正: 以前のrepository docsとNotion DEC-066・DEC-067にあった「`tags`テーブルにactive / inactiveを表す列がない」は誤記だった。初回migrationで`is_active`列は定義済みである。
- `S5_SEARCH_ENTRY_GATE = READY_WITH_SCOPE_LIMIT`（維持）、`S5_IMPLEMENTATION = NOT_COMPLETE`。FR-004・FR-005、S5全体のCOMPLETE / READY_ALLは宣言しない。

### 検索結果0件時の導線（FR-005、DEC-067、2026-10-15）

DEC-067（FR-005の検索結果0件時UXを通常タグによる再検索導線に確定）: **RESOLVED / HUMAN_APPROVED**（承認者: 一朗）。共通仕様は`docs/search-s5-spec.md` 4.5。DEC-066 D3（人気タグの特別扱いは初期除外）は変更しない。意思決定の状態であり、実装完了ではない。

| 項目 | 意思決定 | 実装 | 要件の完了状態 |
| --- | --- | --- | --- |
| 条件の見直し・すべての解除（D2） | RESOLVED / HUMAN_APPROVED | 条件解除は実装済み（ラベルは「検索条件を解除」）。「検索条件を見直す」の独立した操作は未実装 | 未完了。「検索条件を見直す」の実装方式は実装PRで決める |
| 「タグから探し直す」導線（D3） | RESOLVED / HUMAN_APPROVED（選択時に条件を解除してそのタグだけで再検索、並び順は維持） | 未実装。公開タグ一覧APIは未実装。mobileのAPI query型・`CircleListFilters`は既存の`tagId` filterに対応しているが、検索画面（`SearchScreen`）は`tagId`の設定・送信とタグ選択UIを実装していない | 公開タグ一覧APIとタグ導線の実装までPARTIAL |
| タグ一覧API不可時の分岐（D4） | RESOLVED / HUMAN_APPROVED | 未実装。現行の0件画面を暫定的に利用する（D2〜D5の実装済みを意味しない） | 未完了 |
| 直前の検索条件へ戻す操作（D5） | RESOLVED / HUMAN_APPROVED（アプリ内の一時状態。サーバー保存なし） | 未実装 | 未完了。復元可能期間とUIは実装時に提案 |

- 0件と通信エラーの分岐（loading → error → empty）は現行mobileで実装済み（D1の前提）。
- 「人気タグ」という表現は使わない。人気タグの特別機能を提供しないまま元の「人気タグ」要件をCOMPLETEにしない（DEC-066 D3）。
- FR-005全体、S5全体のCOMPLETE / READY_ALLは宣言しない。

### モバイルUIの方針（DEC-069、2026-10-18）

DEC-069（モバイルUIに全画面スケルトンローディングと白基調Liquid Glassを採用する）: **RESOLVED / HUMAN_APPROVED**。`docs/ui-design-guidelines.md` 1.1、`docs/screen-flow.md` 5.1.1、`docs/decisions.md`へ同期した。意思決定の状態であり、実装完了ではない。

| 項目 | 意思決定 | 実装 | 状態 |
| --- | --- | --- | --- |
| 全画面スケルトンローディング | HUMAN_APPROVED（300ミリ秒基準・再取得時のデータ保持など`docs/screen-flow.md` 5.1の状態契約と両立させる） | 未実装（現行は一覧・詳細の一覧型Skeletonのみ） | 詳細は後続のUI設計 |
| 白基調のLiquid Glass UI | HUMAN_APPROVED（具体的なカラーコード・design tokenは未確定） | 未実装 | 詳細は後続のUI設計 |
| 適用画面・対象component・fallback・Dark Mode・アクセシビリティ | 未決 | 未実装 | `PENDING_TECHNICAL_DESIGN` |

- `MOBILE_UI_VISUAL_DIRECTION = HUMAN_APPROVED`、`MOBILE_UI_DESIGN_DETAILS = PENDING_TECHNICAL_DESIGN`、`MOBILE_UI_IMPLEMENTATION = NOT_COMPLETE`。
- S5検索、W4 COMPLETE、認証・認可、画面遷移は変更しない。

### API・DB

- `/api/v1`、camelCase、UUID、RFC 3339 UTC、RFC 9457 Problem Detailsを採用する。
- cursor paginationは既定20・最大50、重要操作は24時間のidempotencyを使う。
- 初回Alembic revisionは`app_private`へ27 tableを作成し、prototype tableを変更しない。
- 一時PostgreSQL 16でupgrade、27 table、downgrade、再upgradeを確認済み。

### 認証・認可

- 初期loginは一般Google OAuth、email/password、iOS版Sign in with Apple。
- 大学Google account必須、大学domain制限、大学SSOは実装しない。
- Authenticationとcircle単位Authorizationを分離し、provider loginだけでmanager権限を付与しない。
- managerは`user_id`・`circle_id` membershipが`active`の場合だけ編集できる。
- 団体存在と申請者権限を別確認し、公開可否に応じてcontrolled channel、既存manager招待、member確認を組み合わせる。
- 証拠原本は判断・appeal終了後30日、絶対上限90日。判断監査は365日。
- nickname・大学・生年月日からemailを表示せず、provider login・共通応答reset・確認済みidentityのsupportに置き換える。

### 非機能

- iOS 16.4以上、Android 10 / API 29以上、phone縦向きを初期最適化する。
- cold start p75 3秒、API GET p95 500ms、一般公開availability 99.5%、RPO 24h、RTO 8hを初期目標とする。
- WCAG 2.2 AA相当、MASVS L1 / API Security Top 10、Critical / High 0件をrelease gateにする。
- SLA、backup、restore、削除期限は`docs/non-functional-requirements.md`を正とする。

## 3. 将来機能・未確定

| 項目 | 状態 |
| --- | --- |
| event | 2026年度内目標、具体release未定。現在のprototype APIは正式化しない |
| chat / DM | 時期・moderation・保持が未定。初期対象外 |
| notification | channel・同意・頻度・費用が未定 |
| LINE login | 将来候補 |
| Android版Apple login | 将来候補。iOS版は初期決定済み |
| circle auto deletion | 初期対象外 |
| paid boost / advertising | 構想のみ。自然推薦に混ぜない |
| MARCH / 全大学 | 将来phase |
| S5検索の残課題 | 仕様方針はDEC-066（2026-10-13）で確定済み。年間費用の上端・上限なし予算と欠損値、非アクティブタグ、市区町村の選択粒度はDEC-068（2026-10-18）で確定済み。未決: 沿線・駅の時期とデータ提供元、地域マスターの取得元・利用条件・更新方式、オンライン併用データの判別 / 移行基準、年間費用の上端の内部表現・NULLのDB符号化・カード / response表示、公開タグ一覧APIのendpoint・response形式・seed、人気タグの再導入時期（詳細は`docs/search-s5-spec.md` 8節）。FR-005の0件時の導線はDEC-067（2026-10-15）で確定済みだが、公開タグ一覧APIとタグ導線は未実装。男女比UIの最終表示文言とDEC-062のbalanced意味記述の整合確認、rating尺度・UI最終文言確定後の検索利用の再検討も残る |

## 4. 人の操作・判断が残るもの

- Work 3以降のPull Request review・人間merge承認、共同開発者招待、required checks設定（GitHub CLI接続は確認済み）
- 正式service名、bundle identifier、Android package name、link domain
- Supabase / Render / EAS / Apple / Googleのowner、region、plan、支払責任者
- 許容月額、production monitoring / SMTP等の有料service選定
- Privacy Policy、利用規約、Support URLの公開文面
- 実在するservice operator、第二確認者、当番、緊急連絡先
- categories / tagsの初期seed語彙の最終表記review
- event等の将来優先順位

## 5. 現在の実装事実

- `mobile/`: 4タブとCircle詳細route shell、共通状態、API URL validation、OpenAPI生成型、native fetch transport、公開Circle typed facade、Lint・型検査・Jestまで。画面からのAPI呼出しと認証は未実装。
- `backend/`: unversioned read技術検証を維持しつつ、正式`/api/v1`共通基盤と`app_private`公開Circle一覧・詳細を実装済み。認証・書込み・他resourceは未実装。
- PostgreSQL: prototype public tableに加え、Git上に正式`app_private`初回migrationがある。共有開発DBへの適用は各開発者が明示的に行う。
- GitHub Actions: MobileのOpenAPI生成型stale check、Lint・型検査・Jest、Backend PostgreSQL integration、Compose migration往復、Next.jsの4 jobを定義済み。各Pull Requestのlatest HEADの結果をGitHubで確認する。
- 外部project: Supabase、Render、EAS、各storeは未構築。

## 6. 次のwork

1. `W3 Mobile Foundation`: COMPLETE。PR #22でmainへmerge済み（merge commit: `f019ab1`）。
2. `Home Contract / API Readiness Gate`: 公開read範囲とPersonalized Home / Releaseの未決事項を混同しないよう、開発gate A〜Dへ分割した（`docs/coding-readiness.md` 3.1。W4 Entry Gate Audit結果の整理であり、製品仕様の新しいHuman Decisionではない）。Circle一覧APIの`sort=most_favorited`はbackendで実装済みである（`favoriteCount`のresponse公開、fraud検知、Home推薦は含まない）。favorite集計のmanager / service operator除外scopeとrole評価時点（A1）、most_favoritedのD1〜D4（DEC-061）は2026-10-04のHuman Decisionで確定済み（RESOLVED）である。
   - A. Public Read API Readiness: **PASS**
   - B. Personalized Home Contract Readiness: **BLOCKED**（A2、R1、R2、view signalに対するmanager / operator除外scopeが未決）
   - C. Home Production Ready: **BLOCKED**（Gate Bに加え、fraud / abnormal signalの具体仕様が必要。DEC-061 D2のrelease gate、OPEN）
   - D. External Beta / Release Readiness: **BLOCKED**（fraud具体仕様、most_favorited NFR分類、production-equivalent性能検証、外部project・identifier・store等、既存release security gates）
   - 未決のまま: A2、R1、R2、view signalに対するmanager / operator除外scope、H10、most_favorited NFR分類はUNRESOLVED、cursor confidentialityはFOLLOWUP、性能follow-upとfraud具体仕様はOPEN。5 ratingの検索filter / sort / rankingは、DEC-062で別Human Decisionへ分離され、DEC-063（2026-10-07）でS5 MVPでは使用しないと確定済み（将来の検索利用は別Human Decision）。
3. `W4 Public Circle Slice`: 公開read範囲の実装と、自動検証・iOS Simulator・Android Emulatorの主要flow確認が完了（COMPLETE。実装状況であり製品要件の承認ではない。VoiceOver実操作とTalkBackの読み上げ音声は未確認）。未ログインHome（`sort=most_favorited`）、Search public list、Circle card、Circle detailを両Simulatorで接続する。FR-001 / FR-005 / FR-017 / FR-018の全体完了ではなくpartial implementationとして扱い、personalized Home、view write、favorite write、interest scoring、決定的shuffle、fraud検知、manager / operator機能は含めない。DEC-062（2026-10-06）によるW4のrollbackはなく、W4 COMPLETEとFR-017全体PARTIALを維持する。
4. `View Definition Gate`: View定義は正式文書間で未解決である。解決するまでcircle view write、view history behavior、viewをsignalとして使うrecommendation logicは実装しない。
5. 外部projectが必要になる直前にowner・identifier・planを確定する。
6. 認証・profile・favorite、manager審査の順でpermission test付き実装へ進む。Viewをsignalとして使うrecommendationはView Definition Gate解決後とする。

詳細は`docs/coding-readiness.md`と`docs/requirements-decision-report-2026-09-15.md`を参照する。
