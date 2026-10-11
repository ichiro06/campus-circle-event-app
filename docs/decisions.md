Warning: truncated output (original token count: 21506)
Total output lines: 990

# 技術・設計上の決定

最終更新日: 2026-10-11（DEC-065: Cloudflare security-audit skillの導入を記録）

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
- 推薦・不正対策: DEC-055（favorite集計のeligible条件・不正検知の段階導入・most_favorited専用の順序とpaginationはDEC-061）
- manager確認の証拠・SLA・保持: DEC-056
- iOS Sign in with Apple: DEC-057
- 非機能目標: DEC-058
- Pull Requestのmerge方式: DEC-059
- commit author email: DEC-060
- most_favoritedの集計対象・段階的不正対策・安定順序・pagination: DEC-061
- サークル評価項目（5項目のrating + 男女比カテゴリ）: DEC-062
- S5検索のrating除外・男女比filterのUI選択肢・離散値chip複数選択: DEC-063
- Claude Codeのsecurity audit skill: DEC-065
- Codex local / Cloudのsecurity audit skill利用: DEC-066

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
- 根拠: 2026-08-23の読み取り…9506 tokens truncated…nation挙動の解釈差をなくすため。D1はschemaの挙動ではなくHumanが採用したproduct behaviorとして記録する。D2は未承認の閾値を正式仕様にしないため段階導入とし、release gateで実装漏れを防ぐ。D3は新しく公開されたCircleを同数時に優先する。
- 旧方針: deletion_pending等のfavorite扱い、異常signalの閾値、most_favorited専用tie-break、ranking変動中のcursor挙動、favorite全0時の順序、account削除時のfavoriteを未決としていた状態（DEC-055の2026-10-04 clarification）。
- 根拠: Notion DEC-061（意思決定ログ）、FR-002、FR-005、API設計、DEC-055（2026-10-04 clarificationを含む）。

### D1 Account lifecycleとfavorite集計

- 公開人気および`GET /api/v1/circles?sort=most_favorited`のfavorite集計では、favoriteの所有者が現在`active`なaccountであることをeligible条件とする。

| account状態 | favoriteの集計 |
| --- | --- |
| `active` | eligible（集計する） |
| `suspended` | excluded（集計しない） |
| `deletion_pending` | excluded（集計しない） |
| `deleted` | excluded（集計しない） |

- 削除処理が完了する前でも、accountが`deletion_pending`になった時点から、そのaccountのfavoriteを公開人気のsignalとして使用しない。
- accountをphysical deleteした場合、現行schemaの`ON DELETE CASCADE`によりfavoriteもphysical deleteする方式を、初期実装のproduct behaviorとして採用する。schemaの挙動を仕様とみなすのではなく、Human Decisionとして「physical delete + favorite delete」を採用したことを記録する。
- favorite ownerを匿名化してfavoriteだけを保持する方式は、初期実装では採用しない。
- A1の除外条件（対象Circleの現在activeなmanager、現在のservice operator）は、上記eligible条件に加えて引き続き別途適用する。他Circleのmanagerのfavoriteは、別の除外条件に該当しない限りeligibleである。

### D2 Fraud / abnormal favorite signalの段階導入

- DEC-055の「不正signalを公開人気から除外する」原則は維持する。削除も弱体化もしない。
- 初回のmost_favorited backend capabilityでは、fraud / abnormal favorite detectionを実装しない。
- repository文書に存在した候補値（favorite toggleが1日30回を超える場合、24時間のranking除外など）は、Human Approvedな正式閾値として採用しない。
- Release gate（OPEN）: 次のどちらか早い時点より前に、fraud exclusionの具体仕様を別Human Decisionとして確定し、実装する。
  - Home recommendationをproduction-readyとして完了扱いする前
  - external beta / production releaseを開始する前
- 別Human Decisionで最低限決める対象: 検知rule、閾値、観測window、event / data source、除外期間、解除条件、保存期間、query / write-pathの責任境界。本Decisionではこれらの具体値を決めない。

### D3 most_favoritedの完全順序

- 完全順序は`favorite_count DESC, published_at DESC NULLS LAST, id DESC`とする。favorite_countはeligible favorite count（D1とA1による）、idはcircle idである。
- favorite countが同数の場合は、新しく公開されたCircleを優先する。
- favorite countが全Circleで0の場合、結果は実質的に`published_at DESC NULLS LAST, id DESC`となり、既存の`newest`と同じtie-break方向になる。
- この順序はcursor paginationにも使用する。
- この順序は`GET /api/v1/circles?sort=most_favorited`のCircle一覧専用である。FR-002のHome推薦の上位10件のtie-break（score、お気に入り数、公開日時、UUID）は変更せず、両者を同一のsort contractとして扱わない。
- favoriteCountをAPI response fieldとして公開するかは本Decisionで決めない（H10、未決）。

### D4 Mutable rankingのpagination

- most_favoritedでは、初期実装としてlive keyset paginationを採用する。
- cursorは少なくとも`favoriteCount`、`publishedAt`、`circleId`をsort keyとして含む。既存のcursor contract（opaque、signed、sort bound、filter bound、24時間期限）は維持する。
- snapshot rankingは保証しない。page取得の間にfavorite countが変動した場合、順位移動によるskipまたはduplicateが起こりうることを初期contractとして許容する。
- refresh / 明示的な再読み込み時は、既存cursorを破棄して先頭から再取得する。
- 初期実装では、frozen ranking snapshot、ranking version、ranking変動によるcursor invalidationは採用しない。
- cursorが`favoriteCount`を内部のsort keyとして含むことは、`favoriteCount`をAPI response fieldとして公開することを意味しない。

### 本Decisionで決めないもの（未決）

推薦shuffleにおけるfilterの意味、view記録のtrigger、cold-startの順序制御、将来のrolling-window集計、favoriteCountのAPI response公開（H10）、cache / preaggregationのfreshness、most_favoritedのNFR分類（GET p95 500ミリ秒／検索・書込みp95 800ミリ秒のどちらか）、fraud検知の具体rule・閾値（D2のrelease gateで別途決定）、閲覧signalに対するmanager / operatorの除外scope、Home推薦の上位10件のtie-break（FR-002）。本Decisionの順序はCircle一覧の`sort=most_favorited`に適用する。

## DEC-062: サークル評価項目（FR-017）を5項目のrating + 男女比カテゴリに確定する

- 日付: 2026-10-06
- 状態: 採用（Notion意思決定ログ上のステータスは、同DBに「採用」optionがないため既存の完了系option「決定」である）
- 決定内容: Human Decision（2026-10-06 JST、承認者: 一朗、Human Approved: YES）。サークルの評価項目は、5項目のratingと男女比categoryとする。決定するのはratingの保持・表示仕様と男女比のcategory仕様だけであり、5 ratingの検索filter / sort / rankingへの利用は決めない。
- 決定理由: FR-017（8項目）、FR-004および議事録の検索節（6項目）、current repository（5 rating + 男女比category）の3者が不一致だったため、保持・表示仕様を1つに確定する。主観性の高い項目と既存tagと重複する項目を除外し、男女比は段階評価ではなくcategorical valueとして扱う。検索・並び替え・rankingは影響範囲が別であるため本Decisionに混ぜず、別Human Decisionとして分離する。
- 旧方針: Notion FR-017は8項目（飲み会頻度、賑やかさ、仲の良さ、初心者歓迎度、本気度、出席自由度、ガクチカ度、男女比）、Notion FR-004と議事録の検索節は6項目を5段階の検索条件として扱っていた。`docs/requirements.md`は5 ratingを「検索条件として扱う」と記載していた。これらはDEC-062で置換する。
- 根拠: Notion DEC-062（意思決定ログ）、Notion FR-017、Notion FR-004、第1回要件定義議事録（過去記述への`[過去]`置換注記）。本repositoryへの同期は新しいHuman Decisionではない。

### Background / Conflict

- 議事録は雰囲気・特徴を「5段階評価で表現する」とした。評価の主体、尺度、未回答、更新方法はFR-017・FR-004の「対象外・要確認」として未確定だった。
- 本Decision前は、評価項目の定義がNotion FR-017（8項目）、Notion FR-004・議事録の検索節（6項目）、current repository（5 rating + 男女比category）の3か所で一致していなかった。
- W4 Public Circle Sliceは公開read範囲を部分実装済みである。

### 採用するrating（5項目）

1. 飲み会頻度（`drinking_frequency_rating`）
2. 賑やかさ（`liveliness_rating`）
3. 本気度（`commitment_rating`）
4. 出席自由度（`attendance_flexibility_rating`）
5. ガクチカにつながる度（`career_opportunity_rating`）

- 団体による自己申告とする。利用者評価や平均ではない。
- integer 1〜5とする。
- `null`は未回答を表す。`null`を0や3等で補完しない。
- ratingに非公開状態は設けない。

### 男女比はcategorical value

- 男女比はratingではなくcategorical valueとし、`gender_balance_code`は`women_majority`、`balanced`、`men_majority`、`mixed_or_other`、`not_disclosed`のいずれかとする。
- 男女比のcategorical filter化はFR-004に反映された。具体仕様（選択UI、複数選択、`null`と`not_disclosed`の検索上の扱い）は別Human Decisionとする。
- 個人単位のgender情報、男女別人数、割合推定値は収集・保存・表示しない。割合の閾値は決めない。

### nullとnot_disclosedの意味

| 値 | 意味 |
| --- | --- |
| rating `null` | 団体が未回答 |
| `gender_balance_code` `null` | 団体が未回答 |
| `gender_balance_code` = `not_disclosed` | 団体が明示的に非公開を選択した（男女比category専用の値） |
| `gender_balance_code` = `mixed_or_other` | 回答済みのその他・多様な構成 |

`null`と`not_disclosed`は必ず区別し、相互変換しない。`null`を`not_disclosed`へ補完せず、`not_disclosed`を`null`へ変換しない。

### 初期ratingから除外した項目

| 項目 | 除外理由 |
| --- | --- |
| 仲の良さ | 主観性が高く、安定した評価基準を定義しにくい |
| 初心者歓迎度 | 既存の「初心者歓迎」tagと意味が重複する |

再導入するかどうかは本Decisionでは決めない。

### 検索への利用の境界

- 男女比（`gender_balance_code`）: categorical filterとして扱う。
- 5 rating: 検索filter、検索sort、rankingへの利用は**UNRESOLVED**とし、別Human Decisionで決める。`docs/requirements.md`を含む正式文書で、5 ratingを検索条件として確定済みと扱わない。
- [過去] 本Decisionが未決として分離した、男女比categorical filterの具体仕様と5 ratingの検索利用は、DEC-063（2026-10-07）でS5 MVPについて確定した。本Decisionの当時の記述として保持する。

### 既存実装への影響

- W4 Public Circle Sliceはrollbackしない。W4は`COMPLETE`（public read partial implementation）を維持し、FR-017全体は`PARTIAL`を維持する。DEC-062の成立はFR-017全体の完了ではない。
- Notion側の確認時点で、current repositoryはHuman確認済みの範囲で既に5 rating + 男女比category構成である。本Decisionのrepository同期はdocsだけを更新し、code・DB schema・OpenAPI・mobileは変更しない。

### 本Decisionで決めないもの（未決）

5 ratingの検索filter・sort・ranking利用と方式（UNRESOLVED）、男女比categorical filterの具体仕様、ratingの各段階の意味とUI最終文言、manager editとAPI write、実データの投入方法、男女比の割合閾値、ratingの非公開状態、除外項目（仲の良さ・初心者歓迎度）の再導入可否。

## DEC-063: S5検索のrating除外・男女比filter公開範囲・離散filter UIを確定する

- 日付: 2026-10-07
- 状態: 採用（Notion意思決定ログ上のステータスは、同DBに「採用」optionがないため既存の完了系option「決定」である。DEC-062と同じ扱い）
- 決定内容: Human Decision（2026-10-07、承認者: 一朗、Human Approved: YES）。S5検索について、(D1) 5 ratingをS5 MVPのsearch filter / sort / rankingに使わない、(D2) 男女比filterのSearch UI選択肢を回答済み4 categoryに限る、(D3) 合宿・規模・活動頻度のSearch UIを離散値のchip複数選択にする、の3点を確定する。
- 決定理由: rating尺度の具体的意味はprovisional / non-normativeであり、現時点でfilter方式を固定すると将来の尺度確定時にAPI / UI / data semanticsの再設計が発生し得る。回答済み4 categoryと離散値filterは既存backendのfilter contractでそのまま利用できる。
- 旧方針: DEC-062は5 ratingの検索filter / sort / ranking利用を**UNRESOLVED**とし、男女比categorical filterの具体仕様（選択UI、複数選択、`null`と`not_disclosed`の扱い）を別Human Decisionとしていた。第1回要件定義議事録は合宿・規模・活動頻度をレンジスライダーとしていた。これらのS5 MVPにおける扱いはDEC-063で置換する。DEC-062・議事録の当時の記述は履歴として保持する。
- 根拠: Notion DEC-063（意思決定ログ）、Notion FR-004、Notion FR-017（本文変更なし。関連Decision relationのみ追加）、第1回要件定義議事録（`[過去]`注記のみ追加）。本repositoryへの同期は新しいHuman Decisionではない。

### Background

- DEC-062で、5 rating field set、integer 1～5、`null`の意味、団体による自己申告、男女比categoryまでは決定済みだった。
- 次の3点は未決だった。
  - 5 ratingのsearch / filter / sort / ranking利用
  - 男女比categorical filterの具体仕様
  - 合宿・規模・活動頻度のUI形式
- FR-004の監査（Human提供の監査結果）で次を確認済みである。
  - backendには`genderBalanceCode` filterが既に存在する。
  - same-filter OR / different-filter ANDは既存API contractである。
  - 5 rating filterはbackend・mobileとも未実装である。
  - rating尺度はprovisional / non-normativeである。
  - 合宿・規模・活動頻度はbackend側に離散値filterが既に存在する。

### D1: 5 ratingのS5検索利用（HD-S1 = A）

- S5 MVPでは、5 rating（飲み会頻度、賑やかさ、本気度、出席自由度、ガクチカにつながる度）をsearch filter、sort、rankingに使わない。
- ratingは次までとする。
  - 保持
  - Circle Detailでの表示
- rating各段階の具体的尺度とUI最終文言を別Human Decisionで確定した後、検索利用を再検討する。
- 本Decisionは、rating fieldの削除、rating表示の削除、W4 rollbackを意味しない。

### D2: 男女比filter（HD-S2 = C）

- 男女比はcategorical filterとして提供する。
- Search UIで選択できるのは、回答済みの次の4 categoryだけである。

| 値 | UI表示（相当。最終文言は未確定） |
| --- | --- |
| `women_majority` | 女性が多い |
| `balanced` | おおむね均等 |
| `men_majority` | 男性が多い |
| `mixed_or_other` | 多様・その他 |

- UI表示は「相当」であり、最終表示文言は既存仕様との整合を確認して別途確定する。DEC-062のbalancedの意味記述は「均衡している」であり、上表の「おおむね均等」とは表記が異なる。この差は整合確認の対象であり、本Decisionでは統一しない。
- Search UIのfilter optionに出さない値: `not_disclosed`、`null`。
- `not_disclosed`をenum・API・schemaから削除しない。`null`と`not_disclosed`を統合しない。DEC-062のsemantics（`null` = 団体が未回答、`not_disclosed` = 団体が明示的に非公開を選択、`mixed_or_other` = 回答済みのその他・多様な構成）は変更しない。
- filter未指定時は、`women_majority`、`balanced`、`men_majority`、`mixed_or_other`、`not_disclosed`、`null`のすべてを通常どおり検索対象に含める。`null`と`not_disclosed`のCircleを除外しない。
- filter指定時だけ、選択した回答済みcategoryへ絞る。
- 本Decisionが定めるのはproduct UIの選択肢の公開範囲（UI exposure）である。backend APIが`genderBalanceCode`として受理する値（API capability）は変更しない。`not_disclosed`をAPIが受理できることは、UIに出さないことと矛盾しない。

### D3: 合宿・規模・活動頻度のUI（HD-S3 = A）

- 次のSearch UIは、レンジスライダーではなく離散値のchip複数選択とする。
  - `campFrequencyCode`
  - `memberCountBand`
  - `activityFrequencyCode`
- レンジスライダーはS5 MVPでは採用しない。将来検討する場合は、bandとの対応規則を含めて別Human Decisionとする。
- 複数選択の意味は既存API contractどおり、same-filter OR / different-filter ANDとする。backendの既存離散値filter contractは変更せず、新しいfilter semanticsは作らない。

### Rationale

- D1: rating尺度の具体的意味はprovisional / non-normativeで、2・4等の意味も正式確定していない。現時点でfilter方式を固定すると、将来の尺度確定時にAPI / UI / data semanticsの再設計が発生し得るため、MVP検索から外す。
- D2: 回答済み4 categoryは既存backendの`genderBalanceCode` filterでそのまま利用できる。`null`検索には新API contractが必要になる。`not_disclosed`は団体が非公開を選んだ状態であり、それ自体を利用者向け検索軸にしないが、通常検索からは除外しない。
- D3: backendは既に離散値を受け取る。chip複数選択なら既存のOR / AND contractをそのまま使える。レンジスライダーではbandとの対応規則という追加仕様が必要になるため、S5 MVPでは採用しない。

### Existing Contract Not Re-Decided

次は既存の正式契約であり、本Decisionでは新しく決めていない。`docs/api-contract.md`を変更していない。

- same-filter: OR / different-filter: AND（`docs/api-contract.md`）
- cursor: normalized filter + sort bound、signed、opaque、24時間
- pagination: 既存API contractを維持
- `genderBalanceCode`: backend capability既存
- DEC-062: 5 rating + 男女比category contract（保持・表示）

### S5 Status

- 本Decisionで解消するHuman Decision: HD-S1、HD-S2、HD-S3。
- S5_SEARCH_ENTRY_GATE = **READY_WITH_SCOPE_LIMIT**を維持する。本Decisionだけを理由にS5全体をCOMPLETE / READY_ALLとしない。

### Out of Scope / Follow-up（本Decisionでは決めない）

- rating各段階の正式尺度、rating UI最終文言、ratingの将来のfilter方式、rating sort / rankingの将来仕様
- 男女比の割合閾値
- manager edit、API write、実データ投入
- S5に残る未決事項（FR-004）
  - area structured filter（都道府県・市区町村・沿線・駅）とarea filter API
  - annual cost filterとannual cost filter API
  - tag master endpoint / vocabulary
  - timeBand all_day / irregular semantics
- 男女比UIの最終表示文言と、DEC-062のbalanced意味記述との整合確認
- 5 ratingの尺度・UI最終文言を確定した後の検索利用の再検討
- personalized Home、recommendation、favorite / view、fraud、release NFR、media、auth、monetization

## DEC-065: Cloudflare security-audit skillをClaude Codeに導入する

- 日付: 2026-10-11
- 状態: 採用
- 決定内容: Cloudflare公式のsecurity-audit skill（https://github.com/cloudflare/security-audit-skill 、MIT）を無改変で `.claude/skills/security-audit/` に同梱し、ローカル・クラウドどちらのClaude Codeでも本repositoryを開けば使える状態にする。取得元commitと更新手順は同ディレクトリの `UPSTREAM.md` に記録する。vendored codeはルートESLintの対象外とする。あわせて、開発者のMacのuser-level（`~/.claude/skills/`）にも導入する。audit結果（脆弱性の詳細）は公開repositoryのcommit・Pull Request・Issueに載せず、本番・共有環境（Supabase / Render等）へのprobeは行わない。
- 決定理由: 脆弱性によるサイバー攻撃被害を防ぐため、実装の各段階でsource-firstのsecurity auditを繰り返し実行できるようにする。repositoryに同梱するとクラウドセッションでもcloneだけで読み込まれ、versionをPull Requestで管理できる。同梱scriptはNode標準moduleだけを使い外部送信がないことを確認した。本repositoryは公開のため、未修正の脆弱性情報を公開しない運用を併せて定める。
- 旧方針: Claude Code用のsecurity audit手順・skillを定めていなかった。
- 根拠: 一朗の依頼と承認（2026-10-11、Claude Projects thread）、PR #38、upstream README・LICENSE。

## DEC-066: Codex local / CloudでCloudflare security-audit skillを使う

- 日付: 2026-10-11
- 状態: 採用
- 決定内容: Cloudflare公式skillをCodex localとCodex Cloudの両方で使えるようにする。既存のcanonical copy `.claude/skills/security-audit/` を維持し、Codexのrepository skill discovery path `.agents/skills/security-audit/` から相対symlinkで公開する。二重管理はしない。Codexでは `$security-audit` で明示呼び出しでき、説明に合う依頼では自動選択の対象にもなる。Codex Cloudでは、この変更を含むrepository revisionを対象にしたtaskで利用する。
- 決定理由: Codexはrepository-level skillsを検出し、repository内のskillsはCloud tasksでも利用できる。local user-level skillsはCloudへ同期されないため、このアプリに限ったskillはrepository内で共有する。
- 旧方針: DEC-065はClaude Codeでの利用だけを対象としていた。
- 根拠: ユーザー依頼（2026-10-11）、[Codex Skills](https://developers.openai.com/codex/build-skills)、[Codex Cloud environments](https://developers.openai.com/codex/environments/cloud-environments)、DEC-065、Cloudflare official upstream commit `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`。
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
- fraud / abnormal favorite exclusionの具体仕様（別Human Decision。DEC-061 D2のrelease gate: Home recommendationのproduction-ready扱い前またはexternal beta / production release開始前の早い方より前）
- favoriteCountのAPI response公開（H10）、cursor payloadの機密性（現行codecは署名のみでpayloadはclientから読める。`docs/api-contract.md`参照。DEC-061では決めていない、別Human Decision候補）、most_favoritedのNFR分類
- 5 ratingの検索利用の将来方式（S5 MVPでは使用しない。DEC-063）、ratingの各段階の意味とUI最終文言、評価項目のmanager edit・API write、実データの投入方法
- S5検索の残課題（DEC-063では決めていない）: area structured filter、annual cost filter、tag master endpoint / vocabulary、timeBand all_day / irregular semantics、男女比UIの最終表示文言とDEC-062のbalanced意味記述の整合確認

大学Google Workspace限定OAuthの検証は引き継がない。一般Google OAuthとiOSのSign in with Appleはinitial認証として実装対象である。
