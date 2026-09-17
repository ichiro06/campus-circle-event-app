# 技術・設計上の決定

最終更新日: 2026-09-17（Pull Requestのmerge方式とcommit identityを確定）

この文書は、過去の方針と最新方針を混同しないための決定記録である。旧方針を消さず、何から何へ変更したかを残す。環境構築だけでは判断できない内容は「未確定」とする。

## 状態

- **採用**: 現在の方針として有効
- **暫定採用**: 現在使用しているが、追加判断により変更する可能性がある
- **未確定**: プロダクトまたは運用上の判断が必要
- **廃止**: 以前は採用していたが使用しない
- **置換**: 別の方針に置き換えられた

## 現在有効な主要方針

- 要件ソースの内容: DEC-030
- 要件ソースの参照先・同期: DEC-043
- 製品形態: DEC-044
- 技術構成・API境界: DEC-045
- 配備・配布: DEC-046
- 認証連携・認可実施点: DEC-047（login方式はDEC-033とDEC-057）
- Web技術の扱い: DEC-048
- 開発品質・CI・依存更新: DEC-049
- 初期機能と後続機能: DEC-034
- アカウント種別と権限: DEC-035
- 認証と認可の分離・circle単位membership: DEC-038
- 管理者確認フロー: DEC-039
- 管理者の追加・交代・失効とaccount削除: DEC-040
- 監査ログとservice operator MFA: DEC-041
- Google / email identityの明示link: DEC-042
- 画面・通信状態: DEC-051
- profile・account recovery: DEC-052
- API契約: DEC-053
- 初期DB schema: DEC-054
- 推薦・不正対策: DEC-055
- manager確認の証拠・SLA・保持: DEC-056
- iOS Sign in with Apple: DEC-057
- 非機能目標: DEC-058
- Pull Requestのmerge方式: DEC-059
- commit author email: DEC-060

DEC-001からDEC-043には、検討経緯を残すため旧方針も記録している。状態が「置換」の決定内容や補足は現在の採用方針ではないため、上記の決定と各正式仕様を優先して読む。

## 記録形式

```markdown
## DEC-XXX: タイトル

- 日付:
- 状態:
- 決定内容:
- 決定理由:
- 旧方針:
- 根拠:
```

## DEC-001: 製品の主対象をiOS・Androidアプリとする

- 日付: 2026-07-17までに決定、2026-07-25に再確認
- 状態: 置換
- 決定内容: 主なユーザー向けクライアントをiOS・Androidアプリとする。
- 決定理由: Webではなく両OSのアプリとして初期開発する方針が明示され、Simulator / Emulatorを含む環境も構築済みである。
- 旧方針: Next.js Webアプリ中心の環境構築方針。途中でDEC-015によりWebへ戻したが、DEC-023で再度置換した。
- 根拠: `mobile/`、`docs/development-setup.md`、本workの明示指示。

## DEC-002: モバイルにReact NativeとExpoを使用する

- 日付: 2026-07-17、2026-07-25に再採用
- 状態: 置換
- 決定内容: React Native、Expo、TypeScript、Expo Routerを初期製品のモバイル基盤とする。
- 決定理由: iOS・Androidを共通コードベースで開発でき、Xcode SimulatorとAndroid Emulatorで確認できる環境がある。学生チームが2つのnative codebaseを保守するより負担が小さい。
- 旧方針: DEC-015で将来候補へ変更したが、DEC-023で初期製品へ戻した。
- 根拠: `mobile/package.json`、`mobile/app.json`、`docs/development-setup.md`。

## DEC-003: バックエンドにFastAPI、データベースにPostgreSQLを使用する

- 日付: 2026-07-17、2026-07-25に正式採用
- 状態: 置換
- 決定内容: FastAPI、Pydantic、SQLAlchemy、psycopgとPostgreSQLを使用する。ローカルは現在のPostgreSQL 16を使用する。
- 決定理由: モバイルから独立したAPI契約を提供し、サークル単位の認可、審査、監査をサーバーへ集約できる。SQLiteとの差異も避けられる。
- 旧方針: DEC-017でFastAPIをWeb初期製品から外したが、モバイル初期製品への変更に伴いDEC-024で置換した。
- 根拠: `backend/`、`backend/compose.yaml`、`docs/architecture.md`。

既存コードが存在することだけを採用理由にしない。二言語・別デプロイの負担より、認可を信頼できるAPI境界へ集約する利点を優先した。

## DEC-004: クライアントとバックエンドをHTTP / JSON APIで接続する

- 日付: 2026-07-17、2026-07-25に正式採用
- 状態: 置換
- 決定内容: ExpoアプリはFastAPIのversioned HTTP / JSON APIを利用する。
- 決定理由: iOS・Androidで共通の契約を使え、DBをアプリへ直接公開せずに認証・認可・入力検証を一か所で行える。
- 旧方針: Next.js Server Components / Server ActionsからSupabaseを直接利用するWeb案。
- 根拠: `docs/architecture.md`。

## DEC-005: Next.jsを技術検証用として残す

- 日付: 2026-07-17、2026-07-25に再確認
- 状態: 置換
- 決定内容: ルートのNext.jsはFastAPI接続とサークル・イベント表示を確認する既存技術検証として当面保持する。
- 決定理由: API確認に利用できる一方、製品クライアントへする必要はない。
- 旧方針: DEC-016で製品Web基盤へ昇格したが、DEC-027で再び製品対象外へ変更した。
- 根拠: `app/`、`lib/api.ts`、`docs/architecture.md`。

Next.jsへ初期製品機能を追加しない。削除または別保管する時期は未確定とする。

## DEC-006: Chakra UIを導入しない

- 日付: 2026-07-17までに決定
- 状態: 採用
- 決定内容: 過去の環境構築資料にあるChakra UIを現在の構成へ追加しない。
- 決定理由: 現在の依存関係に含まれず、製品クライアントはReact Native / Expoであるため、要件・design decisionなしにWeb向けUI libraryを追加しない。
- 旧方針: Chakra UI導入手順を含むWeb環境構築案。
- 根拠: ルートと `mobile/` の `package.json`。

## DEC-007: JavaScript依存関係はnpmで管理する

- 日付: 2026-07-17
- 状態: 採用
- 決定内容: ルートと `mobile/` を別々のnpm projectとして管理し、それぞれの `package-lock.json` を使用する。
- 決定理由: 現在のprojectがnpmで生成・導入され、lockfileが存在するため。
- 旧方針: なし。
- 根拠: 2つの `package.json` と `package-lock.json`。

## DEC-008: バックエンド依存関係はDocker内のpipで導入する

- 日付: 2026-07-17
- 状態: 暫定採用
- 決定内容: 現在は `backend/requirements.txt` をDocker build時にpipで導入する。
- 決定理由: 現在のローカル構成を再現できる。
- 旧方針: uvは端末へ導入したが、backend projectの依存管理には未採用。
- 根拠: `backend/Dockerfile`、`backend/requirements.txt`、`docs/development-setup.md`。

現在のversion範囲指定は完全なlockではない。uvへ移行するかpipのlock方式を採用するかは、初期実装workで決定する。

## DEC-009: 認証方式と権限モデルを未確定とする

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: 環境構築時点では認証方式を決めない。
- 決定理由: 認証コードと正式要件がなかったため。
- 旧方針: なし。
- 根拠: 2026-07-25時点の実装監査。

DEC-019のGoogle OAuth案を経て、DEC-025の一般メール＋パスワードとサークル別手動審査へ置換した。

## DEC-010: ホスティング、デプロイ、配布方式を未確定とする

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: 環境構築時点ではAPI、DB、Web、EAS、ストア、CIの採用先を決めない。
- 決定理由: ローカル環境だけが構築されていたため。
- 旧方針: なし。
- 根拠: 2026-07-25時点の実装監査。

Web向けのDEC-020を経て、モバイル配布を含むDEC-026へ置換した。

## DEC-011: 要件文書と認証文書は要件確定workで作成する

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: `requirements.md` と `authentication.md` を環境構築情報だけから推測して作らない。
- 決定理由: 要件定義と認証設計はプロダクト判断を必要とするため。
- 旧方針: なし。
- 根拠: 環境構築workの明示指示。

本workで正式文書を作成したため、役割を終えた履歴として残す。

## DEC-012: 初期サービスは法政大学向けとする

- 日付: 2026-07-25
- 状態: 採用
- 決定内容: 初期フェーズの対象大学を法政大学とし、MARCHや大学横断検索は将来拡張とする。
- 決定理由: 1大学へ限定することで、初期データ確認と審査運用を成立させやすい。
- 旧方針: 対象大学を明示しない一般的な大学サークル検索アプリ。
- 根拠: 外部要件定義書、`docs/requirements.md`。

「ホウクル」「マークル」は仮称であり、正式名称ではない。

## DEC-013: 初期実装候補を継続検討する

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: ホーム、検索、お気に入り、マイページを初期候補として整理する。
- 決定理由: 過去資料で時期と範囲が一致していなかったため。
- 旧方針: サークル・イベント一覧だけの技術検証。
- 根拠: 外部要件定義書、`docs/requirements-progress.md`。

DEC-021で初期リリース範囲を確定した。

## DEC-014: イベントとチャットの初期採用を未確定とする

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: 過去資料の不一致があるため、イベントとチャットの初期採用を保留する。
- 決定理由: サービス目的には含まれる一方、個別ページでは時期未定だったため。
- 旧方針: イベント一覧の技術検証を製品採用と混同する状態。
- 根拠: 外部要件定義書、現在の `app/events/` と `backend/main.py`。

DEC-021でイベントの閲覧・掲載・審査を採用し、チャットを初期対象外とした。

## DEC-015: 初期製品をレスポンシブWebアプリとする

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: スマートフォンとPCのブラウザで利用するWebを初期製品とし、iOS・Androidアプリを将来候補とする。
- 決定理由: 当時の依頼をWebアプリとして解釈し、ストア対応を減らす判断をした。
- 旧方針: DEC-001のiOS・Android主対象、DEC-002のExpo正式採用。
- 根拠: 旧版 `docs/requirements.md` と `docs/architecture.md`。

この解釈はユーザーの意図と異なっていた。初期からiOS・Androidアプリを開発する明示指示により、DEC-023で置換した。

## DEC-016: Next.jsを製品Web基盤として採用する

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: Next.js App Router、React、TypeScript、Tailwind CSSを製品Webに使用する。
- 決定理由: Web前提ではSSRとVercel運用に利点があった。
- 旧方針: Next.jsを技術検証だけにする方針、およびReact + Vite案。
- 根拠: 旧版 `docs/architecture.md`。

製品形態をiOS・Androidへ戻したため、DEC-027で製品構成から外した。Next.jsは既存技術検証としてのみ保持する。

## DEC-017: FastAPIを初期製品構成から外す

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: Web初期リリースではFastAPIと専用API hostingを使用しない。
- 決定理由: Next.js + SupabaseのWeb案では構成要素を減らせたため。
- 旧方針: DEC-003のFastAPI / PostgreSQL構成。
- 根拠: 旧版 `docs/architecture.md`。

モバイルアプリには独立API境界が必要であり、複雑な認可を集約するため、DEC-024でFastAPIを正式採用した。

## DEC-018: SupabaseでPostgreSQL、Auth、Storageを統合する

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: Next.jsからSupabase PostgreSQL、Auth、Storageを利用し、ローカルもSupabase CLIへ移行する。
- 決定理由: Web案でDB、認証、画像、RLSを一つのサービスへまとめるため。
- 旧方針: SQLite案、plain PostgreSQL Compose。
- 根拠: 旧版 `docs/architecture.md`。

DEC-024により、Supabase PostgreSQL / Auth / Storageは本番サービスとして継続採用するが、業務データはFastAPI経由とし、ローカルは現在のPostgreSQL 16 Composeを使用する。SQLiteは引き続き不採用である。

## DEC-019: Google OAuthと手動権限審査を採用する

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: Supabase Auth経由のGoogle OAuthを一般ログインに使い、サークル権限は手動審査する。
- 決定理由: 独自passwordを持たずに認証する案だったため。
- 旧方針: メール＋password、大学domain一致を重視する案。
- 根拠: 旧版 `docs/authentication.md`。

大学Googleアドレスでの認証は不要という明示指示により、DEC-025の一般メール＋パスワードへ置換した。大学Google Workspaceの利用可否は、初期要件の確認事項からも外した。

## DEC-020: VercelとSupabaseへデプロイする

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: WebをVercel、DB/Auth/StorageをSupabaseへ配置する。
- 決定理由: Next.js Web案の配信先を単純化するため。
- 旧方針: Vercel / Cloudflare、Render、Supabaseを組み合わせる案とデプロイ未決定。
- 根拠: 旧版 `docs/architecture.md`。

Web初期製品を取りやめたため、DEC-026のRender + Supabase + EAS + App Store / Google Play構成へ置換した。Vercelは初期製品で使用しない。

## DEC-021: 初期リリース範囲を検索・掲載・審査へ限定する

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: サークル・イベントの一覧、詳細、検索、一般ユーザーのお気に入り・通報、運営者の掲載・変更申請、管理者の審査・非公開化・権限管理を初期範囲とする。
- 決定理由: サービスの中心価値と情報の信頼性を成立させる最小範囲である。
- 旧方針: イベント・チャットの時期が資料間で不一致、個人向けレコメンドを初期実装とする案。
- 根拠: `docs/requirements.md`。

チャット、DM、レコメンド、通知、口コミ、参加申込、決済、広告、有料上位表示、複数大学検索は初期対象外とする。旧版にあった「ネイティブアプリは初期対象外」という記述はDEC-023により無効である。

## DEC-022: 承認済み公開版と審査中の変更版を分離する

- 日付: 2026-07-25
- 状態: 採用
- 決定内容: サークル・イベントは不変の本体とrevisionを分け、審査中の変更が承認済み公開版を上書きしない構造にする。
- 決定理由: 更新中に公開情報が消えることと、未承認変更が公開されることを防ぐため。
- 旧方針: `circles` / `events` 自体へ状態を直接持たせる案と、現在の単一行試作。
- 根拠: `docs/requirements.md`、`docs/architecture.md`。

詳細schemaと状態遷移は初期実装workでmigrationとテストを含めて確定する。

## DEC-023: 初期製品をiOS・Androidアプリとして再確定する

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: `mobile/` のExpo projectを初期製品とし、最初の機能実装からiOS・Androidを対象にする。
- 決定理由: ユーザーがWebではなくiOS・Androidアプリを希望しており、両OSのSimulator / Emulator環境も構築・確認済みである。
- 旧方針: DEC-015のレスポンシブWeb初期製品。
- 根拠: 本workの明示指示、`docs/development-setup.md`。

サークル検索などを提供する製品Webサイト、Webアプリ、別管理Web画面は初期実装に含めない。ストア必須のPrivacy Policy、Support URL、Universal/App Links検証ファイルを公開する最小限の静的ページは例外とする。

## DEC-024: Expo + FastAPI + PostgreSQLを正式構成とする

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: 製品clientはReact Native / Expo、APIはFastAPI、DBはPostgreSQLとする。開発DBはDocker ComposeのPostgreSQL 16、本番DBはSupabase PostgreSQLとする。
- 決定理由: 両OSを1コードベースで開発し、認証・サークル別認可・審査・監査を独立APIへ集約できる。開発と本番でSQLiteとの差異を持ち込まない。
- 旧方針: Next.js + Supabase + Vercel、React + Vite + FastAPI + SQLite。
- 根拠: `docs/architecture.md`、`docs/development-setup.md`、現在のリポジトリ。

Supabaseへの直接client書込みは初期採用しない。業務データはFastAPIを経由する。

## DEC-025: 一般メール＋パスワード認証と手動運営者審査を採用する

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: Supabase Authのメールアドレス＋パスワードとメール確認を採用する。大学Googleアカウント、Google OAuth、大学domain制限は実装しない。サークル権限は管理者が手動審査する。
- 決定理由: 大学accountへの依存をなくし、一般利用者の登録とサークル運営資格を明確に分離できる。パスワード管理はSupabaseへ委ねる。
- 旧方針: DEC-019のGoogle OAuthと、大学Google Workspaceを候補として検証する方針。
- 根拠: 本workの明示指示、`docs/authentication.md`。

`owner`、`editor`、`service_admin` はTOTP MFAを必須とする。

## DEC-026: Render、Supabase、EAS、各ストアへ配備する

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: FastAPIをRender、PostgreSQL/Auth/StorageをSupabase、モバイルbuildと提出をEAS、配布をApp Store / Google Playとする。ストア必須文書とUniversal/App Links検証ファイルはRender Static Siteで公開する。
- 決定理由: FastAPIとExpoを各公式・標準的な配備経路で管理でき、学生チームでも署名・secret・deployを共有しやすい。
- 旧方針: DEC-020のVercel + Supabase Web構成、および配布先未決定。
- 根拠: `docs/architecture.md`、各サービスの2026-07-25時点の公式仕様。

開発は無料枠を利用できる。Render Freeは休止し、Supabase Freeは自動backupがないため、安定公開では有料planを前提とする。具体的なplanと月額上限は未確定である。

## DEC-027: Web技術を製品経路から外す

- 日付: 2026-07-25
- 状態: 置換
- 決定内容: Next.js、Vercel、React + Viteを初期製品の構成に使用しない。Next.jsは既存API確認用の技術検証としてだけ保持する。
- 決定理由: 初期製品はiOS・Androidアプリであり、同時に製品Webを保守すると学生チームの範囲と費用が増える。
- 旧方針: Next.js製品WebとVercel配信、またはReact + Vite製品Web。
- 根拠: DEC-023、`docs/architecture.md`。

Web向け公開ページが将来必要になった場合は、別の要件・decisionとして再評価する。

## DEC-028: 実測済み開発環境の基準を `development-setup.md` とする

- 日付: 2026-07-25
- 状態: 採用
- 決定内容: 開発端末、導入済みtool、Simulator / Emulator、起動・接続確認の事実は `docs/development-setup.md` を基準とする。
- 決定理由: 過去資料の想定構成と実際の環境を混同しないため。
- 旧方針: 要件資料や会話中の構成案を、環境構築済みの事実として扱う状態。
- 根拠: `docs/development-setup.md`。

同文書が示すとおり、ホストの `python3` は3.9.6、`python3.13` はuv管理の3.13.14を指す。現在のFastAPIはDocker内Pythonを使用する。

## DEC-029: 開発情報源とツールの役割を分離する

- 日付: 2026-07-25
- 状態: 採用
- 決定内容: プロダクト要件、タスク、担当、進捗はNotion、技術仕様と開発ルールはリポジトリ文書、実装はGit、議論はSlackで管理する。CodexはNotionとリポジトリの正式情報を確認して作業する。
- 決定理由: Slack上の会話が無承認で仕様へ変わることを防ぎ、要件、技術仕様、実装事実の責任範囲を明確にするため。
- 旧方針: 開発ツール間の正式な情報源と承認フローは未定義。
- 根拠: `docs/development-workflow.md`、`.codex/config.toml`。

Notion MCPの読み取りは通常利用できる設定とし、書き込み相当のtoolはユーザー承認を要求する。SlackとCodex Cloudの直接連携は、GitHubとCodex Cloudの開発運用が安定するまで導入しない。

## DEC-030: 合意済みの第1回要件定義議事録を最優先の要件ソースとする

- 日付: 2026-08-21
- 状態: 採用
- 決定内容: 共同製作者間で合意済みの「第1回要件定義議事録」の内容を正式な製品要件として採用し、過去の議事録、過去版Markdown、過去の会話と相違する場合は同議事録を優先する。現在の参照先と同期手順はDEC-043で定める。
- 決定理由: ユーザーが共同製作者とのconsensusを明示し、同文書の内容で進めることを決定したため。
- 旧方針: repository外の同議事録を作成途中の過去資料として扱い、2026-07-25版 `docs/requirements.md` を優先する方針。
- 根拠: 2026-08-21の明示指示、次のsource snapshot。

同期時点の参照履歴snapshot（一次情報ではない）:

- 会議日: 2026-07-16
- file更新日時: 2026-08-20 15:04:30 +0900
- SHA-256: `0768944180a8db8cea9393df6a7c0606190ec067fdb088eeba7cfee4f7597d84`
- 参照履歴: Notion「アプリ開発プロジェクトWiki」→「議事録」DB→「第1回要件定義議事録」から同期したローカルexport

Notionをproduct requirementsの正式管理先とするDEC-029は維持する。今回使用したCloud上Markdownは、Notionページから同期した時点を識別する参照履歴として残す。正式な参照場所をCloud上MarkdownからNotionページへ明確化する変更はDEC-043に記録する。

## DEC-043: 要件定義の一次情報をNotionの議事録ページとする

- 日付: 2026-08-23
- 状態: 採用
- 決定内容: 今後の正式な要件定義の一次情報を、Notionの「アプリ開発プロジェクトWiki」内にある「議事録」データベースの「第1回要件定義議事録」ページとする。`docs/requirements.md`、`docs/requirements-progress.md`、要件レビュー等のリポジトリ文書は、このページを同期したレビュー用スナップショットとして維持する。
- 決定理由: 共同製作者が合意した要件を、更新・承認状態を含めて共同管理できる場所を将来の参照先として明確にするため。ローカルCloud上のexportだけを一次情報とすると、Notionで更新された内容とのずれや古いコピーを根拠にした実装が起きるため。
- 旧方針: 2026-08-21の同期時点では、Cloud上のMarkdown exportを「現在の要件source」と説明し、そのpathとhashをリポジトリへ記録していた。exportは今回の同期対象を識別する履歴情報へ位置付けを変更する。
- 根拠: 2026-08-23の読み取り確認で、指定ページが「アプリ開発プロジェクトWiki」配下の「議事録」データベースに存在することを確認した。ユーザーによる正式な参照先の指定。

運用上、Notionページを確認してからリポジトリ文書を同期する。Notionページとリポジトリ文書に差異がある場合は、差異・更新日時・実装影響を報告し、同期と承認が済むまで不明な要件を実装しない。Notionが一時的に利用できない場合は最後の同期済みスナップショットを読み取り・診断に限って使用し、要件変更の根拠にはしない。Notionのprivate URLやpage IDは、公開され得るリポジトリ文書へ記録しない。

## DEC-031: 初期製品をレスポンシブWebアプリケーションへ変更する

- 日付: 2026-08-21
- 状態: 置換
- 決定内容: 初期製品をスマートフォンとPCのbrowserで利用するresponsive Web applicationとする。
- 決定理由: DEC-030のsourceが製品をWeb applicationとして定めているため。
- 旧方針: DEC-023のiOS / Android native app initial product、DEC-027のproduct Web除外。
- 根拠: DEC-030、`docs/requirements.md`。

この方針は2026-09-01の共同開発者との再確認によりDEC-044へ置換した。`mobile/` とSimulator / Emulator環境を正式product routeへ戻し、製品WebとPC browser版は初期対象から外した。

## DEC-032: Next.js + Supabase + Vercelを正式構成とする

- 日付: 2026-08-21
- 状態: 置換
- 決定内容: Next.js App Router / React / TypeScript / Tailwind CSSをproduct Web、SupabaseをPostgreSQL / Auth / Storage、Vercelをhostingとする。initial productではFastAPIを使用しない。
- 決定理由: Web要件に一致し、frontendとserver処理をTypeScript projectへまとめ、少人数の学生チームが2言語・2deploy・JWT/API型同期を保守する負担を減らせるため。SupabaseがGoogleとemail/password auth、PostgreSQL、Storageを統合できるため。
- 旧方針: DEC-024のExpo + FastAPI + PostgreSQL、DEC-026のRender / EAS / app store構成。
- 根拠: DEC-031、`docs/architecture.md`、Next.js・Supabase・Vercelの公式仕様。

この方針はDEC-045、DEC-046、DEC-048へ置換した。React + ViteとSQLiteは引き続き不採用とする。

## DEC-033: 初期認証に一般Google loginとemail/passwordを採用する

- 日付: 2026-08-21
- 状態: 採用
- 決定内容: Supabase Authを用い、一般Google accountのGoogle OAuthとemail/passwordをinitial loginにする。一般学生とcircle managerでlogin UIを共通にする。
- 決定理由: DEC-030のsourceに両方式がinitial implementationとして記載され、Supabase AuthがReact Nativeから両方を扱えるため。
- 旧方針: DEC-025のemail/passwordのみ、Google OAuth初期不採用。
- 根拠: DEC-030、`docs/authentication.md`。

大学Google accountを必須にせず、university domain restrictionとuniversity SSOを実装しない。Google account所有だけでcircle managerを自動承認しない。モバイルでのtoken受け渡しとFastAPIでの検証はDEC-047、iOS審査上のlogin選択は同決定のrelease gateに従う。

## DEC-034: initial scopeをhome personalization・search・favorite・my pageとする

- 日付: 2026-08-21
- 状態: 採用
- 決定内容: personalized home、詳細なcircle search、favorite、my page、circle page / card、circle management、report / shareをinitial scopeとする。eventは2026年度内を目標とするが時期未定、chatは時期未定とする。
- 決定理由: DEC-030のsource内の「初期実装」「ホウクルで実装」「実装時期未定」の区分に従うため。
- 旧方針: DEC-021のpersonalization除外とevent initial inclusion。
- 根拠: DEC-030、`docs/requirements.md`。

initial my pageに記載されたevent / chat関連項目は、各機能の提供開始後に有効化する。initialからplaceholderを表示するかは未確定とする。

## DEC-035: account typeとservice operation privilegeを分離する

- 日付: 2026-08-21
- 状態: 採用
- 決定内容: 新規登録時の「guest / manager」は一般学生とcircle manager希望として扱う。circle manager希望は確認待ち状態であり、確認前にedit権限を与えない。service operatorはpublic signupから取得できない。
- 決定理由: sourceの同一login UXとaccount type選択を維持しつつ、service-wide privilegeのself-assignmentを防ぐため。
- 旧方針: source内で「管理者」がcircle managerとservice operatorのどちらか明確でない状態、および旧 `owner` / `editor` / `service_admin` model。
- 根拠: `docs/requirements.md`、`docs/authentication.md`。

circle manager内をowner / editor等へ分けるかは未確定とする。後続のDEC-038で、初期は`manager`だけを採用する方針へ具体化した。

## DEC-036: non-functional requirementの数値を再度未確定とする

- 日付: 2026-08-21
- 状態: 置換（DEC-058）
- 決定内容: authoritative sourceのnon-functional requirements欄が空のため、旧mobile仕様にあった3秒、99.5%、RPO 24時間、RTO 8時間等を合意済み正式値として引き継がない。review候補として再評価する。
- 決定理由: sourceにない数値をconsensus済みとして扱わず、iOS・Androidアプリ、FastAPI、PostgreSQL、ストア配布に合う測定対象・条件を改めて合意するため。
- 旧方針: 2026-07-25版 `docs/requirements.md` のmobile向けnon-functional target。
- 根拠: DEC-030、`docs/requirements-review-2026-08-21.md`。

iOS / Androidの対応OS・端末、アプリ起動・API応答、accessibility、offline / poor network、availability、backup、security、operation、store release、costを別途合意する。

## DEC-037: email address忘れ機能へsecurity gateを設ける

- 日付: 2026-08-21
- 状態: 置換（DEC-052）
- 決定内容: nickname、university、birth date一致後にemail addressを表示する合意済み機能は保持するが、追加本人確認、表示方式、rate limit、auditを決定するまで実装しない。
- 決定理由: 3項目だけではaccount所有者を十分に確認できず、完全なemail address表示がaccount列挙と個人情報漏えいにつながり得るため。
- 旧方針: 同3項目の一致だけで完全なemail addressを表示する記述、および過去の同機能を全面除外する方針。
- 根拠: `docs/requirements.md`、`docs/authentication.md`、security review。

この時点ではblockerとして明示した。後続のDEC-052で、完全・一部emailを表示しない安全な回復flowへ置き換えた。

## DEC-038: AuthenticationとAuthorizationを分離し、管理者権限をcircle単位で管理する

- 日付: 2026-08-21
- 状態: 採用
- 決定内容: Googleまたはemail/passwordによるAuthenticationと、特定circleを管理できるAuthorizationを分離する。サークル管理者権限はglobal user roleではなく、`user_id`と`circle_id`のmembershipで管理する。初期のcircle内roleは`manager`だけとし、`active`の複数管理者を許可する。
- 決定理由: Googleログイン成功はGoogle account本人の確認に過ぎず、特定サークルの代表・管理権限を証明しないため。サークル単位で管理すれば、複数circleの担当範囲と解除を明確にできるため。
- 旧方針: DEC-035でcircle manager内の`owner` / `editor`分割を未確定とし、account種別と管理者権限の境界を文書上の整理に留めていた。
- 根拠: `docs/requirements.md`、`docs/authentication.md`、`docs/architecture.md`。

クライアントのrole、Google email、大学domain、user metadataを権限の根拠にしない。2026-09-01以降は、FastAPIがSupabase Auth access tokenを検証し、保護されたDB上のcircle membershipを確認して認可する。旧Web構成のServer Action / Route Handlerを認可実施点にしない。

## DEC-039: サークル管理者の確認は初回手動確認と追加推薦・最終承認の二段階とする

- 日付: 2026-08-21
- 状態: 採用
- 決定内容: 初回管理者は、公開・非公開を問わず、サービス運営者がサークルの存在と申請者の管理権限を確認してから承認する。既存管理者がいる場合の追加管理者は、既存`active`管理者の推薦・招待を受け付けるが、サービス運営者の最終承認後にだけ`active`とする。
- 決定理由: 公式一覧やGoogle accountは団体の存在またはaccount本人を補強しても、申請者がそのcircleを管理できることを単独では証明しないため。初回を手動確認し、追加を推薦＋運営者確認にすることで、学生チームの運用負荷と不正取得リスクを抑えるため。
- 旧方針: DEC-035の「確認待ち」までの整理、および確認証拠・公開／非公開の具体方式が未確定だった状態。
- 根拠: `docs/requirements.md`、`docs/authentication.md`、`docs/requirements-review-2026-08-21.md`。

公開サークルで公式情報がある場合は、団体の存在確認と申請者が団体窓口を管理できることの確認を分ける。公式情報があっても申請者との関係が確認できない場合は権限を付与しない。非公開サークルで既存管理者がいない場合は、サービス運営者による初回個別確認を行い、根拠不足なら承認しない。Google domain一致、共有パスワード、既存管理者だけの承認は単独方式として採用しない。

## DEC-040: 管理者の追加・交代・失効とaccount削除をmembership lifecycleで扱う

- 日付: 2026-08-21
- 状態: 採用
- 決定内容: 管理者membershipに`pending`、`evidence_requested`、`active`、`rejected`、`revoked`、`expired`等の状態を持たせ、`active`だけに編集権限を与える。複数管理者を許可し、交代では後任を先に承認してから旧管理者を解除する。
- 決定理由: 代表者交代やaccount削除でcircleを失わせず、権限のない状態と編集可能な状態を明確に分けるため。
- 旧方針: 管理者の複数登録、交代、最後の管理者、account削除時のmembership処理が未確定だった状態。
- 根拠: `docs/requirements.md`、`docs/authentication.md`、`docs/architecture.md`。

account削除・侵害・規約違反では対象membership、申請、招待を失効させる。他に管理者がいればcircleの公開情報を継続し、最後の管理者がいなくなればcircleを未割当・編集停止としてサービス運営者が再確認する。管理者accountや一人の管理者の操作だけでcircleを自動・即時物理削除しない。

## DEC-041: 管理者権限操作を監査し、service operatorにMFAを要求する

- 日付: 2026-08-21
- 状態: 採用
- 決定内容: 申請、追加情報要求、推薦、招待、承認、却下、解除、交代、公開・非公開化、account削除による失効を監査ログへ記録する。service operatorはMFAと重要操作前の再認証を必須とする。circle managerは初期一律MFAにせず、重要操作の再認証、通知、監査で保護する。
- 決定理由: サービス全体の権限を持つservice operatorと、circle単位のmanagerを同じ負荷で保護せず、少人数チームが継続運用できる範囲で影響の大きい操作を強く保護するため。
- 旧方針: MFAの採否と管理者権限操作の監査が未確定だった状態。
- 根拠: `docs/requirements.md`、`docs/authentication.md`、`docs/architecture.md`、Supabase MFA公式仕様、OWASP Authentication / Authorization guidance。

監査ログには実行者、対象user、対象circle、操作、前後状態、理由、確認根拠の参照、時刻、結果を残す。確認証拠の原本やpassword、provider tokenはログへ保存しない。根拠が弱い初回申請、最後の管理者解除、サービス全体の緊急操作は別担当者の確認を記録する運用を推奨する。

## DEC-042: Googleとemail/passwordのidentity linkingは本人の明示操作だけ許可する

- 日付: 2026-08-21
- 状態: 採用
- 決定内容: 1つのservice accountへGoogle identityとemail/password identityを追加する場合、ログイン済み本人がaccount設定から明示的にlinkする。provider emailが一致するだけの自動mergeは行わない。別accountの統合はsupport対応へ分離する。
- 決定理由: email一致だけでaccountを結合すると、誤結合やaccount takeoverにつながるため。複数login手段を利用したい場合の利便性は、両方の所有確認と明示操作で確保するため。
- 旧方針: Googleとemail/passwordのaccount統合を未確定とし、provider email一致時の扱いを決めていなかった状態。
- 根拠: `docs/requirements.md`、`docs/authentication.md`、Supabase users / identities公式仕様。

link、unlink、mergeの結果がサークルmembershipを別userへ移すことはない。membershipの移譲は、DEC-039とDEC-040の管理者確認・交代フローを別に通す。

## DEC-044: 初期製品をiOS・Android専用アプリとして再確定する

- 日付: 2026-09-01
- 状態: 採用
- 決定内容: 初期製品はiOS・Android向けモバイルアプリだけを提供する。製品Web、PC browser版、別管理Webは初期開発しない。サービス運営者機能も、権限で保護したモバイルアプリ内画面として設計する。
- 決定理由: ユーザーと共同開発者がBefore環境を既に構築しており、両OSアプリだけを開発する製品方針を明示的に再確認したため。環境の存在だけでなく、2名規模でもReact Native / Expoの共通codebaseで両OSを保守できる点を評価した。
- 旧方針: DEC-031のresponsive Web初期製品。DEC-023をいったん置換していたが、本決定でモバイル専用方針を再採用する。
- 根拠: 2026-09-01の明示指示、共同開発者の構築済みBefore環境、`docs/requirements.md`。

Privacy Policy、Support URL、Universal Links / App Linksの検証ファイルなど、ストア審査・OS連携に必要な最小限の静的ページは製品Webとはみなさない。公開機能を持つWebアプリへ拡張する場合は別決定を必要とする。

## DEC-045: Expo + FastAPI + PostgreSQLを正式構成として再採用する

- 日付: 2026-09-01
- 状態: 採用
- 決定内容: `mobile/` のReact Native / Expo / TypeScript / Expo Routerを製品client、`backend/` のFastAPI / Python / Pydantic / SQLAlchemy / psycopgを製品API、PostgreSQLを業務DBとする。mobileとAPIはversioned HTTPS JSON APIで接続し、業務データの読書きはFastAPIを経由する。
- 決定理由: iOS・Androidを1 codebaseで提供しながら、入力検証、circle単位認可、審査、監査を信頼できるserver境界へ集約できるため。既存コードがあることだけではなく、不正な直接書込みを避けられることと、共同開発者が既に再現できる構成であることを評価した。
- 旧方針: DEC-032のNext.js + Supabase直接利用。内容としてはDEC-024を再採用し、現在の要件に合わせてAPI認証境界を明確化する。
- 根拠: `docs/architecture.md`、`docs/development-setup.md`、`docs/authentication.md`。

ローカルDBはDocker ComposeのPostgreSQL 16、本番DBはSupabase PostgreSQLを使用する。Supabase StorageとAuthは採用するが、mobile clientから業務tableへ直接書き込まない。この時点ではAPI version、schema、migration、generated clientの方式を要確認としていた。後続のDEC-050でmigration toolにAlembicを採用し、正式schemaと最初のrevisionは引き続き要確認とした。

## DEC-046: Render、Supabase、EAS、各アプリストアを正式な配備先とする

- 日付: 2026-09-01
- 状態: 採用
- 決定内容: FastAPIはRender、PostgreSQL / Auth / StorageはSupabase、iOS・Android buildとsubmissionはEAS Build / EAS Submit、配布はApp Store / Google Playを使用する。Vercelは初期製品で使用しない。
- 決定理由: Before構成の役割を維持し、API、managed database / auth / storage、両ストア配布を小規模チームが運用可能なサービスへ分けるため。
- 旧方針: DEC-032のVercel + Supabase Web構成。内容としてはDEC-026を再採用する。
- 根拠: `docs/architecture.md`、各サービスの公式仕様。

各service / store accountの所有者、支払責任者、plan、region、budget、staging、EAS project、bundle identifier / package name、署名鍵、release権限は未確定であり、実装・release work前に決定する。

## DEC-047: Supabase Authのmobile sessionをFastAPIで検証し、DB membershipで認可する

- 日付: 2026-09-01
- 状態: 採用
- 決定内容: React NativeアプリはSupabase Authで一般Google OAuthとemail/passwordを扱い、取得したaccess tokenをHTTPSのAuthorization headerでFastAPIへ送る。FastAPIはtokenの署名、issuer、audience、expiry等を検証し、server側DBの`user_id`・`circle_id` membershipと状態を確認して認可する。
- 決定理由: Authenticationとcircle単位Authorizationを分離し、mobile内の表示やprovider metadataを権限根拠にしないため。Google login成功は特定circleの管理権限を証明しない。
- 旧方針: DEC-032 / DEC-038に含まれていたNext.js Server Action / Route HandlerとRLS中心のWeb認可実施点。login方式自体はDEC-033を継続する。
- 根拠: `docs/authentication.md`、`docs/architecture.md`、Supabase Auth / JWT公式仕様。

大学Google account、大学domain制限、大学SSOは実装しない。Apple loginの扱いは、公式条件を再確認した後続のDEC-057でiOS初期要件へ確定した。

## DEC-048: Next.jsとVercelを初期製品経路から外す

- 日付: 2026-09-01
- 状態: 採用
- 決定内容: ルートNext.jsはFastAPI read APIとの接続確認に使った既存technical verificationとしてのみ保持し、製品機能、管理画面、認証、正式デプロイを追加しない。Vercel projectは初期製品向けに作成しない。
- 決定理由: 初期製品がモバイル専用であり、同じ製品機能をWebへ重複実装・保守する必要がないため。既存検証を直ちに削除せず、混同を防いだ上で保管判断を後続へ分ける。
- 旧方針: DEC-031 / DEC-032の製品WebとVercel。
- 根拠: DEC-044、DEC-045、`docs/architecture.md`。

Next.js技術検証をarchive、別branchへ移動、または削除する時期は未確定とする。変更時はユーザーの既存作業を確認し、別決定として記録する。

## DEC-049: コーディング開始用のquality baselineを採用する

- 日付: 2026-09-14
- 状態: 採用
- 決定内容: `mobile/`はExpo SDK 57の公式互換dependency、Jest、`jest-expo`、React Native Testing Libraryを用い、`npm run check`でLint・TypeScript・testを実行する。GitHub Actionsはmobile、FastAPI / PostgreSQL、Next.js technical verificationを別jobで検査する。Dependabotはnpm、pip、Docker、GitHub Actionsを月次で確認する。mobileの公開可能なAPI URLは`EXPO_PUBLIC_API_BASE_URL`とし、secretを置かない。
- 決定理由: 無料かつ可逆的な標準toolで、大学生2人の共同開発でもlocalとPull Requestの検査を揃え、依存更新の通知量を抑えられるため。Expo標準のenvironment variableとtest手順に合わせることで独自仕組みを増やさないため。
- 旧方針: DEC-010でCIを未確定としていた状態、およびmobileでLint・型検査だけを手動実行していた状態。製品技術構成を変更する決定ではない。
- 根拠: Expo environment variable / unit testing公式資料、GitHub Actions公式資料、`docs/coding-readiness.md`。

Expo SDKは同一SDK内の互換patchへ更新した。ルートNext.js technical verificationは16.3.5へ更新し、既知Criticalを解消した。buildにはNext.js公式の`--webpack` optionを使い、制限環境でTurbopackが内部portを作れない問題を製品構成へ持ち込まない。`npm audit fix --force`、Expo major SDK update、native workflow変更は自動適用しない。GitHub ActionsとDependabotはbaselineをcommit・pushして初回実行を確認するまで「GitHub上で稼働済み」とは扱わない。

## DEC-050: AlembicとPython dependency lockを採用する

- 日付: 2026-09-14
- 状態: 採用
- 決定内容: PostgreSQL schema migrationにはAlembicを使用する。Python dependencyは`requirements.txt` / `requirements-dev.txt`を入力とし、uvで生成したruntime / development lockをDockerとCIへpipで導入する。Ruffとpytestをbackendのquality gateへ追加する。
- 決定理由: SQLAlchemyと同じmodel metadataを基準にschema変更をreview可能なrevisionへでき、2人の端末とCIで同じdependency versionを再現できるため。既存のDocker + pip起動方法を維持し、共同開発者の環境変更を最小限にする。
- 旧方針: DEC-008のrange指定requirementsだけをDockerで解決する暫定方針、およびmigration方式を未確定としていた状態。
- 根拠: Alembic、Ruff、pytest、FastAPI testingの公式資料、`backend/`、`docs/coding-readiness.md`。

現在のcircle / event modelはtechnical verificationであり、正式な初期migrationへ自動採用しない。この条件はDEC-054で満たし、`app_private`だけを作る初回revisionを追加した。prototypeの起動時`Base.metadata.create_all()`は技術検証に限定して残す。

## DEC-051: mobile画面遷移と通信状態の共通挙動を確定する

- 日付: 2026-09-15
- 状態: 採用
- 決定内容: 初期navigationをホーム、検索、お気に入り、マイページの4タブとし、サークル詳細をstack、manager / operator機能をマイページ配下の保護routeにする。300ミリ秒を超える初回取得はskeleton、再取得は正常dataを保持し、offlineではcacheをread-only表示する。重要な書込みはoffline queueから自動送信しない。
- 決定理由: iOS・Androidで同じ受入条件を持ち、通信断時の無限loading、空表示、二重送信、古い権限での操作を避けるため。
- 旧方針: 画面案はあったが、transition、loading / empty / error / offline、retry、timeoutの正式条件が未確定だった状態。
- 根拠: `docs/screen-flow.md`、Android offline-first / startup公式資料、Expo Router公式資料。

GETは対象errorだけ最大2回再試行し、非upload APIは10秒、画像uploadは60秒でtimeoutする。401、403、404、409、422、429、5xxのUI挙動も同文書を正とする。

## DEC-052: 必要最小限のprofileと安全なaccount recoveryへ変更する

- 日付: 2026-09-15
- 状態: 採用
- 決定内容: universityとschool yearは任意の自己申告とし、生年月日は初期収集しない。nickname・university・birth date一致からemailを表示する方式と、university・birth dateをpassword reset条件にする方式は採用せず、provider login、利用者が入力したemailへの共通応答reset、確認済みidentityを使うsupportに置き換える。
- 決定理由: 生年月日に初期機能上の必要目的がなく、自己申告profileはaccount所有を証明できないため。完全・masked emailの表示はaccount存在と個人情報を第三者へ漏らし得るため。
- 旧方針: FR-009 / FR-025 / FR-026とDEC-037に残っていた生年月日収集、3項目一致後のemail表示、3項目によるpassword reset、追加security gate未確定状態。
- 根拠: `docs/requirements.md`、`docs/authentication.md`、NIST SP 800-63B、OWASP Forgot Password、個人情報保護委員会Q&A。

passwordは15文字以上・64文字以上を許容し、組合せruleや定期変更を要求しない。reset linkはone-time・30分、存在有無は共通応答、reset後は全sessionを失効する。閲覧履歴は説明後の明示操作で開始し、最大20件または90日とする。

## DEC-053: `/api/v1`と共通API契約を採用する

- 日付: 2026-09-15
- 状態: 採用
- 決定内容: 正式APIを`/api/v1`、HTTPS / JSON、camelCase、UUID、UTC RFC 3339とする。正常response envelope、RFC 9457 Problem Details、既定20・最大50の署名付き不透明cursor、重要操作の24時間`Idempotency-Key`、楽観的競合検出を共通契約にする。
- 決定理由: mobile releaseは利用者の更新が遅れるため、error処理、pagination、再送、旧app互換をendpointごとに独自実装しないため。
- 旧方針: 現在のunversioned read APIを技術検証とし、version、response、error、pagination、idempotency、client生成を未確定としていた状態。
- 根拠: `docs/api-contract.md`、RFC 9457、RFC 9745、RFC 8594、FastAPI公式資料。

breaking changeは新major pathへ分け、旧majorは180日または直近30日active端末の95%移行までの長い方を維持する。OpenAPIを機械可読な一次情報とし、TypeScript clientを生成・Git管理する。

## DEC-054: `app_private`正式schemaと初回migrationを採用する

- 日付: 2026-09-15
- 状態: 採用
- 決定内容: 正式業務tableをSupabase Data APIへ公開しない`app_private` schemaへ置き、FastAPIだけを業務data境界とする。UUID、UTC日時、JPY整数、`TEXT + CHECK`、公開revisionと審査中revisionの分離を採用する。初回Alembic revisionは正式初期tableだけを作り、prototypeの`public.circles` / `public.events`を削除・移行しない。
- 決定理由: local PostgreSQLとSupabase PostgreSQLで同じmigrationを再現し、mobileからの直接書込み面を減らしながら、既存のread技術検証を破壊しないため。
- 旧方針: DEC-050でAlembicだけを採用し、data dictionaryと最初のrevisionを未確定としていた状態。
- 根拠: `docs/data-dictionary.md`、PostgreSQL 16 constraint / UUID公式資料、Supabase API hardening公式資料。

Supabase Authの`sub`と`accounts.id`を同じUUIDにするが、local DB再現性のため`auth.users`へDB FKを張らず、FastAPIが検証済みtokenとaccount状態を照合する。event、chat、notification、課金、user reviewは初回schemaへ入れない。

## DEC-055: 推薦順序と不正signal除外を確定する

- 日付: 2026-09-15
- 状態: 採用
- 決定内容: 閲覧1点、お気に入り5点に、任意の興味category 3点を追加する。閲覧は同一user・circleで30分に1回、最大20件または90日とし、自団体manager / operator、停止account、非公開・削除circleのsignalを公開人気から除外する。上位10件はscore、お気に入り数、公開日時、UUIDで安定sortし、11件目以降はuser・JST日付・filterによる決定的shuffleにする。
- 決定理由: 議事録の推薦意図を維持しつつ、連打による操作、DB都合の同点変動、毎回randomで比較できないUXを避けるため。
- 旧方針: 同点、重複click、random固定期間、履歴保持、異常操作を要確認としていた状態。
- 根拠: `docs/data-dictionary.md`、`docs/requirements.md`。

異常signalはrankingから一時除外し、利用者へは「最近見たカテゴリ」「興味」「人気」等の説明を表示する。将来の有料順位は自然順位へ混ぜず、広告表示と別decisionを必要とする。

## DEC-056: manager確認の証拠、期限、異議申立て、保持を確定する

- 日付: 2026-09-15
- 状態: 採用
- 決定内容: 公式確認可能、公開情報はあるが公式確認不可、非公開で既存managerあり、非公開の初回managerの4区分で確認強度を変える。団体存在と申請者権限を別判定し、controlled channelへのone-time challenge、既存manager招待、member 2名確認等を組み合わせる。完全資料から5営業日、追加情報14日、30日無応答で失効、異議申立て30日、回答10営業日とする。
- 決定理由: Google loginや公式掲載だけの低コスト自動承認を避けつつ、全申請へ重い身分証確認を要求せず、学生2名のチームが継続運用できるため。
- 旧方針: 初回手動確認・追加managerの運営最終承認までは決めたが、証拠種類、SLA、appeal、保持期限、複数確認条件が未確定だった状態。
- 根拠: `docs/authentication.md`、`docs/data-dictionary.md`、DEC-039～041。

学生証は標準要件にしない。証拠原本は判断・異議申立て終了から30日、絶対上限90日で削除し、判断metadataと監査は関係終了後365日保持する。非公開等の初回manager、最後のmanager解除、operator権限操作は別担当者確認を記録する。

## DEC-057: Sign in with AppleをiOS初期要件へ変更する

- 日付: 2026-09-15
- 状態: 採用
- 決定内容: 一般Google loginを提供するiOS版ではSign in with Appleも初期提供し、release gateとする。Android版はGoogleとemail/passwordを初期提供し、Apple loginを必須にしない。
- 決定理由: App Store Review Guideline 4.8は、primary accountのthird-party loginを提供するappへ同等のprivacy-preserving login optionを求める。本製品は大学発行accountを必須にしないため、教育機関accountの例外を前提にできない。
- 旧方針: DEC-033 / DEC-047でApple loginを将来候補・要確認とした状態。
- 根拠: Apple App Review Guidelines 4.8、`docs/authentication.md`。

Apple identityもAuthenticationだけを行い、circle manager権限は付与しない。private email relayを許容し、実emailの追加提出を強制しない。

## DEC-058: 初期非機能目標値を正式採用する

- 日付: 2026-09-15
- 状態: 採用
- 決定内容: iOS 16.4以上、Android 10 / API 29以上、cold start TTID p75 3.0秒、API GET p95 500ミリ秒、月間availability 99.5%、RPO 24時間、RTO 8時間、WCAG 2.2 AA相当、release時Critical / High脆弱性0件等を、測定条件と段階別gateを含めて正式採用する。
- 決定理由: 「速い」「安全」等の解釈差をなくし、2名規模でも測定・優先順位付けできる現実的な初期基準を置くため。
- 旧方針: DEC-036で旧数値をいったん未確定へ戻し、候補値としてreviewしていた状態。
- 根拠: `docs/non-functional-requirements.md`、Expo、Android、Apple、OWASP、Supabase公式資料。

月額上限額と有料planの契約は支払権限を持つ開発者の決定として残す。一般公開で99.5%と日次backupを満たせない場合は、要件を黙って下げず公開範囲を限定する。

## DEC-059: Pull Requestの標準merge方式をmerge commitとする

- 日付: 2026-09-17
- 状態: 採用
- 決定内容: Pull Requestは原則としてGitHubの `Create a merge commit` でmergeする。`Squash and merge` または `Rebase and merge` は対象Pull Requestごとの人間による明示承認を必要とする。CI成功やAI reviewだけではmergeせず、人間が `Files changed` と検証結果を確認して承認する。auto-mergeは使用しない。
- 決定理由: review済みcommitの境界とSHAを保持すると、意図の追跡、部分的な切り戻し、原因調査を行いやすい。小さく意味のあるcommitへ分割する本repositoryのbaseline運用とも整合し、人間の最終判断を自動化に置き換えないため。
- 旧方針: merge方式と最終承認条件をrepositoryの正式ルールとして明文化していなかった。
- 根拠: PR #1の人間reviewとmerge判断、GitHubのPull Request merge公式仕様、`AGENTS.md`、`CONTRIBUTING.md`、`docs/development-workflow.md`。

## DEC-060: 今後のcommitにGitHub noreply emailを使用する

- 日付: 2026-09-17
- 状態: 採用
- 決定内容: 今後のcommit author emailには、GitHub accountに対応するID-based noreply emailをrepository local Git設定で使用する。実際のaddressは追跡対象fileへ記載せず、共同開発者のglobal Git設定を変更しない。既存commitはemail変更だけを目的に書き換えない。
- 決定理由: GitHub上のauthor attributionを保ちながら、Public repositoryの新しいcommit metadataへ個人用email addressを公開しないため。repository local設定なら適用範囲が明確で、他projectや共同開発者へ影響せず、運用確認も容易である。既存履歴の書換えはcommit SHA、review、参照の安定性を損なうため行わない。
- 旧方針: 開発端末の通常email設定を継承し、repository単位のcommit email方針を定めていなかった。
- 根拠: GitHubのcommit email設定・email address公式仕様、`AGENTS.md`、`CONTRIBUTING.md`、`docs/development-workflow.md`。

## 要確認・次workへ引き継ぐ項目

- サービスの正式名称、大学名・公開情報の利用確認
- Googleとemail/passwordのidentity linkingのUI、重複accountのsupport手順
- categories / tagsの初期seed語彙と表記review
- service operatorの実在担当者、当番、初期付与、緊急連絡先
- eventの2026年度内release時期とlife cycle
- chat、notification、auto deletion、monetizationの個別要件
- Render / Supabase / EAS / Apple Developer / Google Play Console / Google Cloudのowner、budget、region、staging
- bundle identifier / package name、署名鍵、EAS project、store submission権限と復旧手順
- Privacy Policy、Support URL、store privacy申告の公開文面と必要に応じた法務確認
- custom SMTP、monitoring、analyticsのservice選定と費用
- Next.js technical verificationのarchiveまたは削除時期
- Notionの議事録ページ更新をrepository docsへ同期する担当、確認頻度、差分レビューの運用

大学Google Workspace限定OAuthの検証は引き継がない。一般Google OAuthとiOSのSign in with Appleはinitial認証として実装対象である。
