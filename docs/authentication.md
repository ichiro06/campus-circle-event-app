# 認証・認可仕様

- 状態: 正式仕様
- 初回決定日: 2026-07-25
- 最終更新日: 2026-09-15
- 対象: ホウクル初期実装

## 1. 結論

- 認証基盤: Supabase Auth
- 初期ログイン: 一般Googleアカウント、email/password、iOS版のSign in with Apple
- 大学Googleアカウント必須: なし
- 大学domain制限・大学SSO: なし
- login UI: 一般学生とサークル管理者で共通
- account種別: 一般学生、サークル管理者希望
- サークル管理資格: account作成とは別に、サークル単位で確認・承認する
- サービス運営者権限: public signupから取得不可
- 将来候補: LINE login、Android版のApple login
- session: ExpoアプリでSupabase Authのaccess / refresh tokenを扱うmobile session
- authorization: FastAPIでtokenとPostgreSQL上のcircle membershipを確認する
- 管理者権限の初回付与: サービス運営者による確認・承認
- 追加管理者: 既存管理者による推薦・招待を受け付けるが、最終承認はサービス運営者
- 管理者権限の単位: ユーザー全体ではなく、`user_id` と `circle_id` の組み合わせ
- 初期のサークル内role: `manager` だけ。`owner` / `editor` の分割は行わない

議事録の「Google」は一般のGoogle OAuthとして実装する。大学発行Googleアドレスであることを要求せず、大学所属やサークル管理資格の証明にも使わない。

Googleログインの成功はAuthentication（Googleアカウントを操作できること）の確認であり、Authorization（特定サークルを管理してよいこと）の確認ではない。Googleログインだけで、いかなるサークルの管理者権限も付与しない。

## 2. 用語と本人確認の範囲

| 概念 | 確認できること | 確認できないこと |
| --- | --- | --- |
| Google login | Google accountを操作できること、Google側の認証済みidentity | 大学所属、実名、サークル担当者、特定サークルの管理権限 |
| email確認 | 登録emailを受信できること | 実名、大学所属、サークル担当者であること |
| profile情報 | 利用者が任意入力した大学・学年 | 内容が真実であること。追加確認なしでは自己申告。生年月日は初期収集しない |
| サークル存在確認 | 公式サイト・公式一覧等に団体が存在すること | 申請者がその団体を管理できること |
| サークル管理者確認 | 申請者が特定サークルを管理してよいこと | 他サークルやサービス全体を管理してよいこと |
| サービス運営者付与 | サービス全体の確認業務を行ってよいこと | public signupでは取得できない |

認証、profile、サークル管理資格、サービス運営者資格を同じbooleanやemail domainだけで表現しない。

Googleのemail、表示名、プロフィール画像は、管理者権限の判定キーにしない。内部の利用者識別にはSupabase Authの`user_id`を使い、Googleのprovider identityはログイン手段として管理する。

## 3. ユーザー区分と権限

### 3.1 未ログイン利用者

- 公開サークルのhome、search、card、detailを利用できる。
- favorite、report、profile、history、circle editは利用できない。
- 認証必須操作を押した場合はloginへ誘導する。

### 3.2 一般学生ユーザー

- Google、email/password、iOSではAppleのいずれかでloginする。
- favorite、report、profile、interest、view historyを利用できる。
- account作成だけではcircle edit権限を持たない。

### 3.3 サークル管理者希望

- 新規登録時または登録後に、サークル管理者を希望できる。
- 希望は特定のサークルへの申請として作成する。ユーザー全体に管理者roleを付けない。
- 確認完了までは一般学生ユーザーと同じ権限とする。
- 希望選択だけでサークルの非公開情報を閲覧・変更できない。
- 申請対象のサークルを変更する場合は、新しい申請を作成し、元の申請を取り消す。

### 3.4 サークル管理者

- サービス運営者に確認された担当サークルだけを管理できる。
- 複数サークルを管理する場合も、サークルごとに関係を記録する。
- サークルごとのmembership状態が`active`の場合だけ編集できる。
- サークル情報を編集し、公開確認へ提出できる。
- 公開状態、確認中、差し戻し理由を確認できる。
- 他サークルを変更できない。
- 追加管理者の推薦・招待を開始できるが、推薦だけで権限は発生しない。
- 自分の管理者権限の辞退を申請できる。

初期実装では `owner` / `editor` の権限分割を行わず、確認済みの`manager`を複数登録できるようにする。代表者・主連絡先の表示が必要な場合も、権限の強いowner roleではなく、別の連絡先属性として扱う。

### 3.5 サービス運営者

- サークルとサークル管理者を確認する。
- 公開、差し戻し、非公開化、違反報告対応を行う。
- 初回管理者の承認、追加管理者の最終承認、管理者権限の解除を行う。
- 公開signup、profile field、モバイルアプリからのrequestだけで権限を取得できない。
- 初期付与、追加、解除、緊急停止を保護された運用手順で行う。
- 管理者権限の判断理由と根拠の参照先を監査ログへ残す。

### 3.6 権限モデル

| 権限 | 対象範囲 | 付与方法 | 主な操作 |
| --- | --- | --- | --- |
| 未ログイン | 公開データのみ | 自動 | 公開サークルの検索・閲覧 |
| 一般ユーザー | 自分のaccountと公開データ | Google、Appleまたはemail/passwordで認証 | profile、お気に入り、履歴、通報 |
| 管理者申請中 | 自分の申請だけ | 申請作成 | 申請状況の確認、追加情報の提出 |
| サークル管理者（`manager`） | 承認済みの特定circleだけ | サービス運営者が承認 | 担当circleの編集、確認提出、管理者推薦 |
| サービス運営者 | サービス全体 | 非公開の運用手順 | 審査、公開・非公開、管理者付与・解除、通報対応 |

権限はデータベース上の関係と状態から毎回判定する。クライアントから送られた`role`、`circle_id`、`is_manager`等を権限の根拠にしない。

## 4. login画面

一般学生とサークル管理者でlogin画面の基本UXを共通にする。login後、DB上の現在のaccount状態と担当サークルに応じて利用可能な画面を表示する。

初期画面に次を提供する。

- Googleで続ける
- Appleで続ける（iOSのみ）
- email addressとpasswordでlogin
- 新規account作成
- email addressを忘れた場合
- passwordを忘れた場合

service operator専用のpublic login種別を表示しない。同じ認証基盤を使う場合も、service operator権限はserver側の現在値で判定する。

## 5. Google login

### 5.1 対象

- 一般のGoogle accountを利用できる。
- 大学発行accountである必要はない。
- `hosei.ac.jp` 等のdomain制限を行わない。
- Google Workspace管理者の許可を、一般利用者全員の前提にしない。

### 5.2 flow

1. 利用者が「Googleで続ける」を選ぶ。
2. Supabase Authを通じてsystem browserまたはnative provider flowでGoogleへ進む。
3. Googleから許可済みcallbackとdeep linkを経由してアプリへ戻る。
4. Authorization Code / PKCE等の正式flowでcodeをmobile sessionへ交換する。
5. アプリがaccess tokenをFastAPIへ送り、FastAPIがtokenとaccount状態を確認する。
6. 初回の場合はprofile onboardingへ進む。

OAuthのAuthorization Code / PKCEとSupabase・ExpoのReact Native向け手順を使用する。redirect URL、URL scheme、Universal Links / App Linksはlocal、preview、productionでallow listを分ける。

### 5.3 dataとscope

- loginに必要な最小scopeだけを要求する。
- Google Calendar、Drive、Gmail等のaccessを要求しない。
- Google API利用目的がないため、Google provider token / refresh tokenを保存しない。
- Googleから得たemailを大学所属確認に使わない。

Supabase Authのcallbackを通じて受け取るGoogle OIDC identityは、issuer、signature、audience、expiration等を検証したものだけをsessionへ結び付ける。Googleのprovider固有の安定した`sub`とSupabaseの`user_id`をidentityの対応付けに使い、email文字列を主キーや管理者判定に使わない。大学domain制限を採用しないため、`hd` claimの一致をAuthorization条件にしない。

### 5.4 Sign in with Apple

- iOS版でGoogleを主要loginとして提供するため、App Store Review Guideline 4.8に対応するSign in with Appleを初期提供する。
- 本サービスは大学発行accountを必須にしないため、教育機関向け例外を前提にしない。
- Apple identityもAuthenticationだけを行い、circle manager権限を付与しない。
- Appleの非公開email relayを正式なlogin identityとして扱い、実emailの提出を追加で強制しない。
- nonce、state、authorization code、callback、credential stateを検証し、失効・転送停止時の回復案内を用意する。
- Android版でApple loginは初期必須とせず、一般Googleとemail/passwordを提供する。

## 6. email/password account

### 6.1 新規作成

1. 利用者がemail address、password、password確認を入力する。
2. 一般学生またはサークル管理者希望を選ぶ。
3. 利用規約・プライバシーポリシーの確認と同意を行う。
4. Supabase Authへaccountを作成する。
5. email所有確認を行う。
6. 確認後にprofile onboardingへ進む。

サークル管理者希望を選んだ場合も、この時点では編集権限を付与しない。

### 6.2 password

- passwordと確認入力が一致した場合だけ設定できる。
- passwordの平文または独自hashを業務DBへ保存しない。
- Supabase Authがhash化と検証を担当する。
- passwordをlog、analytics、error reportへ送らない。
- passwordは15文字以上とし、少なくとも64文字までのUnicodeを受け付ける。
- 大文字・小文字・数字・記号の画一的な組合せruleや定期変更を要求しない。
- よく使われるpassword・漏えいpasswordのblocklistを利用可能なprovider機能またはserver-side確認で拒否する。
- password manager、自動入力、pasteを許可し、入力失敗はrate limitする。

### 6.3 login

- emailとpasswordをSupabase Authで検証する。
- error responseからaccountの存在、Google登録かemail登録かを第三者が判定できないようにする。
- login、再送、resetへ用途別のrate limitを設ける。

## 7. profile onboarding

初期onboardingでは、次を扱う。

| 項目 | 必須 | 公開 | 用途・保持 |
| --- | :---: | :---: | --- |
| nickname | 完了時必須 | 公開 | profile、将来chat。account削除まで |
| profile image | 任意 | 公開 | profile表示。差替え・削除可 |
| email | 認証方式による | 非公開 | login、所有確認、重要通知。Supabase Authを正とし業務DBへ複製しない |
| university | 任意 | 非公開 | 検索初期値・将来の大学別表示。認証・管理権限確認には使わない |
| school year | 任意 | 非公開 | profile補助。初期推薦scoreには使わない |
| interests | 任意 | 非公開 | cold-start推薦、検索初期値。本人が変更・消去可 |
| view history | 任意 | 非公開 | 説明後の明示操作で開始。20件または90日の早い方 |

birth dateは初期収集しない。本人確認、email address照会、password reset、manager確認、初期推薦にも使わない。将来、年齢要件が必要になった場合は、正確な日付より少ない情報で目的を達成できないかを先に再設計する。

## 8. Googleとemail/passwordのaccount統合

1つのサービスaccountに、Google identityとemail/password identityを複数紐付けることは可能とする。ただし、同じemail addressであることだけを理由に自動統合しない。

- provider emailが同じという理由だけで、独自にaccountをmergeしない。
- Google login済みの本人がaccount設定からlinkを開始し、現在のsessionを確認する。
- email/passwordを追加する場合は、新しいemailの所有確認とpassword設定を完了する。
- Google identityを追加する場合は、OAuthのstate / PKCEとcallbackを検証し、現在のsessionに対して明示的にlinkする。
- 既存の別accountを自動mergeしない。重複accountの統合が必要になった場合は、本人確認と影響範囲を確認するsupport対応へ分離する。
- unlink後にlogin手段が0件にならないようにする。
- account linking・unlink・mergeは管理者権限を変更しないが、監査ログと本人通知の対象にする。

## 9. email address変更

- login済み利用者が変更を開始する。
- 現在のsessionとSupabase Authの再認証要件を確認する。
- 新しいemailの所有確認が終わるまで変更完了としない。
- サークル管理資格をemail文字列ではなくSupabase user IDへ結び付ける。
- email変更後も、既存のサークルmembershipを別ユーザーへ移さない。
- 重要な変更として通知とaudit対象にする。

Google / Appleだけのaccountでは、providerが管理するemailまたはrelay addressを表示し、変更はprovider側または別のemail/password identityを本人がlinkするflowへ案内する。provider emailの直接書換えで別accountをmergeしない。

## 10. password reset

password忘れpageではemailだけを入力し、Supabase Authのreset案内を送る。universityとbirth dateは入力・照合しない。

- 一致・不一致にかかわらず「該当するアカウントがある場合は案内を送りました」という共通表示にし、応答時間も極端に変えない。
- reset linkはone-time、有効期限30分とする。成功・期限切れ・使用済みを区別して安全な再要求を案内する。
- normalized emailのHMAC単位で1時間3回、IP単位で1時間10回を初期上限とし、異常時だけCAPTCHA等を追加する。plain emailをrate-limit keyとしてlogへ残さない。
- reset完了後は全端末のrefresh sessionを失効し、本人へ通知する。
- service operatorが利用者の現在passwordやreset tokenを閲覧・取得できないようにする。
- accountの存在確認、manager権限移譲、email開示をpassword reset supportと結び付けない。

## 11. email addressを忘れた場合

議事録のnickname、university、birth date一致から登録emailを表示する方式は、2026-09-15のsecurity判断で置き換える。3項目はaccount所有を証明せず、完全表示もmasked表示も第三者へ登録有無を漏らすためである。

回復画面は次の順に案内する。

1. GoogleまたはAppleで登録した可能性があれば、そのproviderでloginを試す。
2. 心当たりのあるemailを入力し、存在有無を明かさない共通応答でreset送信を要求する。
3. 既にlogin済みの別端末、link済みの確認済みidentity、登録emailへのaccessがある場合だけsupportで回復を補助する。
4. いずれも確認できない場合、emailを開示せず、新規account作成を案内する。旧membershipの移譲はmanager確認flowを別に通す。

support担当者も完全・一部email、provider種別、account存在を質問者へ開示しない。回復失敗だけを理由に本人確認資料を長期収集しない。

## 12. サークル管理者登録と確認

### 12.1 基本原則

管理者確認は、次の2つを別々に確認する。

1. **サークルの存在・掲載内容の確認**: その団体が存在し、登録情報が妥当か。
2. **申請者の管理権限の確認**: そのユーザーが、そのサークルを代表して情報を編集してよいか。

公式サイトや大学の公開一覧は1を補強するが、2を自動的には証明しない。Googleログイン、email確認、大学名の自己申告も2の代わりにならない。

### 12.2 申請フロー

1. 利用者がloginし、管理したい既存サークルを選ぶか、新しいサークルを登録する。
2. サークルとの関係、連絡可能な公式窓口、公開URL、既存管理者の有無を申告する。
3. 申請を`pending`として保存する。申請中は一般ユーザー権限のままとする。
4. サービス運営者がサークルの存在と申請者の管理権限を確認する。
5. 不足があれば`evidence_requested`として追加情報を求める。
6. 承認時に、対象`circle_id`と申請者の`user_id`のmembershipを`active`にする。
7. 却下、取消し、期限切れの場合はmembershipを作成せず、理由と再申請可否を記録する。

申請対象のcircle、申請者、確認状態はサーバー側で固定する。画面から送られた`role=manager`だけでmembershipを作成しない。

### 12.3 公開サークルの確認

公開サークルは、外部から存在を確認できるかどうかで分ける。

#### 大学公認団体など、公式情報から存在を確認できる場合

- 公式サイト、大学公式一覧、公式SNS等のURLと取得日を記録する。
- 公式情報でサークルの存在・名称・公認区分を確認する。
- 可能な場合は、団体が管理する公式窓口へ一回限りの確認連絡を行い、申請者がその窓口を操作できることを確認する。
- 公開一覧に団体が載っているだけで、申請者を自動承認しない。
- 公式情報が古い、窓口がない、申請者との関係が確認できない場合は、未確認状態に戻して追加確認を求める。

#### 公開情報はあるが、申請者との関係を外部確認できない場合

- サークル情報は`unverified`または審査中として扱い、申請者に編集権限を与えない。
- 公式SNS・団体サイト・既存管理者など、団体と申請者を結び付ける別の確認経路を求める。
- それでも確認できない場合は、サークルの掲載申請だけ受け付け、管理者権限は付与しない。

### 12.4 非公開サークルの確認

外部公開情報がない団体では、公開URLや大学domainを前提にしない。次の優先順位で扱う。

1. **既存管理者がいる場合**: 既存の`active`管理者が、ログイン済みの申請者をサークル単位で推薦・招待する。その後、サービス運営者が最終承認する。
2. **既存管理者がいない場合**: 初回管理者登録として、サービス運営者が申請者と団体の関係を個別に確認する。申請者が示す連絡先、活動実態、団体メンバーからの確認など、団体と申請者を結び付ける根拠を記録する。
3. **確認根拠が不足する場合**: サークルを仮登録または審査中に留め、編集権限を付与しない。推測で承認しない。

学生証や個人情報の提出は標準要件にしない。どうしても必要な場合は、目的、閲覧者、保存期間、マスキング、削除を事前に決める。

### 12.5 方式比較と採用判断

| 方式 | セキュリティ | 実装コスト | 運用負荷 | ユーザー体験 | 判断 |
| --- | --- | --- | --- | --- | --- |
| Google account / 大学domain一致 | サークル権限の証明にならず低い | 低 | 低 | 良い | 不採用 |
| 大学・公式サイト掲載だけで承認 | 団体の存在は確認できるが、申請者の権限は不明 | 低 | 低 | 良い | 単独では不採用 |
| 初回からサービス運営者が手動確認 | 根拠を確認できれば高い | 中 | 高 | 普通 | 初回登録に採用 |
| 既存管理者だけが追加承認 | 乗っ取り・誤承認時の影響が大きい | 低 | 低 | 良い | 単独では不採用 |
| 既存管理者の推薦・招待＋サービス運営者の最終承認 | 団体内の関係と第三者確認を組み合わせられる | 中 | 中 | 良い | 追加管理者に採用 |
| 共有パスワード・合言葉 | 漏えい・使い回し・退任時の回収が難しい | 低 | 中 | 良い | 不採用 |

本サービスでは、**初回はサービス運営者の手動確認、追加は既存管理者の推薦・招待を受けたサービス運営者の最終承認**を正式方式とする。既存管理者だけの承認やGoogle domain一致だけでは、管理者権限を付与しない。

### 12.6 追加管理者の招待

- 既存の`active`管理者は、候補者のログイン済みアカウントをサークル単位で推薦できる。
- 候補者が申請を受け入れても、membershipは`pending`のままとする。
- サービス運営者が確認してから`active`にする。
- 招待をメールリンクで実装する場合も、リンクだけで権限を付与せず、ログイン済みの対象accountへ結び付け、短い有効期限と一回限りの使用を設ける。
- 招待の作成・受諾・承認・取消しを全て監査ログへ記録する。

### 12.7 不正取得の防止

- signup時にservice operatorやcircle managerを自己付与できない。
- `circle_id`、`user_id`、role、membership状態はサーバー側で再取得し、client入力を信用しない。
- 編集・公開提出のたびに、現在のsession、対象circle、`active` membership、公開状態を確認する。
- サークル管理者は担当していないcircleの行、画像、revision、申請情報を読めない・変更できない。
- 同一circleへの重複申請、短時間の大量申請、管理者変更の連続操作にrate limitと監視を設ける。
- 既存管理者へ新規申請・承認・解除を通知し、異議申立てを受け付ける。
- 認証証拠や連絡先を一般利用者・他サークルへ公開しない。
- 公開、非公開化、管理者付与、解除は再認証を要求し、サービス運営者のMFAを必須とする。

### 12.8 状態と権限の遷移

```text
申請者
  -> pending
  -> evidence_requested
  -> active（サービス運営者が承認）
  -> revoked / expired
```

`pending`、`evidence_requested`、`rejected`、`revoked`、`expired`は編集権限を持たない。`active`でも対象circle以外へのアクセスは認めない。

### 12.9 受け付ける確認根拠

団体の存在と申請者の権限を別の欄で判定する。

| 団体区分 | 存在確認 | 申請者の権限確認 | 追加条件 |
| --- | --- | --- | --- |
| 大学公認等、公式確認可能 | 大学公式一覧・公式siteを確認日から30日以内に取得 | 公式email / SNS / site等のcontrolled channelへのone-time challenge、大学・顧問の書面確認、既存active manager推薦のいずれか | 掲載だけでは承認しない |
| 公開情報はあるが公式確認不可 | 独立する2つの根拠。少なくとも1つは直近12か月 | controlled channel、または現役member 2名の確認と活動・役割資料 | 根拠不足なら掲載・権限とも審査中 |
| 非公開・外部確認困難、既存managerあり | 既存circle記録 | active managerのone-time招待と候補者のlogin受諾 | service operatorが最終承認 |
| 非公開・初回manager | 直近6か月の活動根拠 | controlled group channel、またはmember 2名の確認と役割資料 | 別operatorの確認を記録 |

one-time challengeは運営者が生成したcodeを、団体が既に管理する窓口から返してもらう。利用者が申請時に新設しただけの窓口は、単独の根拠にしない。学生証は標準提出物にせず、例外時は氏名・所属以外をmaskし、目的と期限を事前表示する。

### 12.10 期限・異議申立て・証拠削除

- 必要資料が揃った時点から5営業日以内に、承認、却下、追加情報要求のいずれかを通知する。
- 追加情報の提出期限は14日とし、通知後30日間応答がなければ申請を`expired`にする。
- 招待tokenはone-timeで7日間有効とする。
- 却下・解除への異議申立ては最終判断から30日以内、回答は受理から10営業日以内とする。可能なら元の判断者と別のoperatorが確認する。
- 証拠原本は最終判断または異議申立て終了から30日で削除し、処理遅延があっても提出から90日を超えて保持しない。
- 申請、判断根拠の要約、membership、付与・解除の監査は関係終了後365日保持する。事故・法的保全は理由、access、期限を記録して最大3年とする。
- 招待、承認、却下、解除は申請者と全active managerへ通知する。機微な証拠や他人のemailは通知へ含めない。

### 12.11 複数確認が必要な操作

通常申請は1名のoperatorが処理できる。次は誤付与時の影響が大きいため、別operatorの確認を記録する。

- 公開情報が弱い団体・非公開団体の初回manager付与
- 最後のactive managerの解除・移譲
- service operatorの付与、回復、解除
- 緊急時以外の大規模な公開停止

operatorが実在1名しかいない期間は当該操作を即時承認せず、共同開発者または事前登録した第二確認者が記録を確認できる体制を作ってから実施する。

## 13. サービス運営者

- 初期service operatorは、保護されたserver-side手順で付与する。
- public signupのaccount typeにservice operatorを含めない。
- roleの付与・解除をservice role keyだけに依存した手作業で常態化させない。
- production Dashboardへのaccessと、アプリ内service operator権限を分離する。
- service operatorにはMFAを必須とし、管理者権限の付与・解除や非公開化の前に再認証する。
- service operatorの人数、承認者、緊急停止、引継ぎを公開前に決める。
- 初期は少人数の運用を前提に、通常の申請を一人の担当者が処理できる。ただし、根拠が弱い初回申請、最後の管理者解除、サービス全体の緊急操作は、別担当者の確認を記録する運用を推奨する。
- 管理者付与の判断で使った根拠は、原本や秘密情報を丸ごと保存せず、出典URL、確認日、判断理由、担当者を監査ログに残す。

## 14. mobile sessionとtoken security

- Supabase Authのaccess tokenとrefresh tokenでmobile sessionを扱う。
- access tokenを`Authorization: Bearer` headerでFastAPIへ送り、query parameterへ入れない。
- FastAPIはSupabase Authの公開鍵・JWKS等で署名、issuer、audience、expirationを検証し、未検証のJWT payloadを信用しない。
- FastAPIはtokenの`sub`だけで処理せず、protected operationごとに現在のaccount状態、circle relationship、service operator roleをDBで再確認する。
- access tokenの有効期間は15分を初期値とする。refresh tokenはrotationを有効にし、再利用検知時はsessionを失効する。
- refresh tokenはExpo SecureStoreへ`WHEN_UNLOCKED_THIS_DEVICE_ONLY`相当で保存し、Android backupから除外する。平文の設定ファイル、AsyncStorage、log、analytics、crash reportへ保存しない。
- logout時はSupabase sessionを終了し、端末側のsessionを削除する。
- OAuth state、PKCE、deep link、redirect allow listを正しく検証する。
- malicious deep link、open redirect、token replay、端末紛失、backupからのtoken復元をsecurity testへ含める。
- auth token、reset link、OAuth codeをURL logやanalyticsへ残さない。

通常logoutは現在端末、password reset・account侵害・account削除は全端末sessionを失効する。同時session上限は有料plan依存のため初期強制要件にせず、重要操作でaccount状態と直近再認証をserverが確認する。

## 15. 多要素認証

議事録にはMFAの採否がない。本設計では、サービス全体へ影響するservice operatorにはMFAを必須とする。一般ユーザーとサークル管理者には初期から一律必須にせず、重要操作の再認証、通知、監査で運用する。

MFAを導入するservice operatorについては、enrollment、recovery code、端末紛失、管理者によるreset、step-up対象操作を同時に決める。サークル管理者へのMFA必須化は、運用負荷とアカウント侵害状況を見て別decisionで再評価する。

## 16. account管理・削除

- 利用者はnickname、profile image、非公開profile、email、password、通知設定を管理できる。
- account削除前に影響と復元可否を表示し、再確認する。
- 削除時は現在の認証手段による再認証を要求する。
- auth user、private profile、interest、view history、favoriteを削除または匿名化する。
- 管理者membership、申請、招待はaccount削除時に失効させる。未処理の申請・招待も取り消す。
- 管理中circleの公開情報を個人accountと同時に自動削除しない。circleはユーザーaccountとは別の事業データとして扱う。
- 他に`active`管理者がいる場合は、そのcircleを継続し、削除するユーザーのmembershipだけを解除する。
- 最後の`active`管理者が削除する場合は、削除前の引継ぎを促す。引継ぎができない場合はcircleを未割当・編集停止にして、サービス運営者が再確認する。circleを自動削除しない。
- account削除後も、セキュリティ・審査に必要な監査記録は、個人情報を分離または匿名化したうえで必要期間だけ保持する。
- accountのemail変更やidentity linkingは、circle membershipを別ユーザーへ移す操作ではない。
- account停止・侵害対応では、membershipを即時`revoked`にし、必要に応じてsessionの失効と再確認を行う。
- Supabase Authのaccount削除はFastAPIの保護された処理から行う。JWTは発行済みtokenが有効期限まで残り得るため、削除済み・停止済みaccountの重要操作では現在のaccount状態とsessionをFastAPIで再確認する。
- アプリ内から削除を開始できるようにし、本人再認証後に直ちに`deletion_pending`として重要操作を停止する。
- personal dataはactive systemから7日以内、通常backupから30日以内に削除する。削除完了までのstatusと問い合わせ方法を表示する。

### 16.1 サークル管理者の追加・削除・交代

- 追加は12.6の推薦・招待・サービス運営者承認で行う。
- 自発的な辞退は、本人の再認証後に申請し、サービス運営者が`revoked`へ変更する。
- 退会・侵害・規約違反による解除は、理由、実施者、対象circle、時刻を監査する。
- 代表者交代では、新しい候補者が`active`になるまで旧管理者を削除しない。新管理者の承認後に旧管理者を解除する。
- 複数管理者がいる場合も、特定の一人だけが他の管理者を即時削除できない。推薦・異議申立て・運営者判断を経る。
- 最後の管理者を解除する場合は、circleを未割当状態にするか、後任を先に承認する。
- サークル自体を削除する場合は、管理者一人の操作だけで即時物理削除せず、サービス運営者が掲載根拠、通報、引継ぎを確認して非公開化または削除する。管理者membershipと招待は失効させ、監査履歴を残す。
- audit、不正対策、法的義務で保持する例外と期限をprivacy policyへ記載する。

## 17. 初期に含めない認証

- LINE login
- Android版のApple login
- 大学Google Workspace限定login
- university domain自動判定
- university SSO
- service operatorのpublic signup

一般Google loginは初期に含むため、この一覧には含めない。

iOS版のSign in with Appleは初期に含み、この一覧の対象外とする。

## 18. 要確認事項

1. email/password登録でemail確認を完了するまでの具体的な閲覧範囲
2. identity linkingの具体画面と重複account support担当
3. service operatorの実在担当者、当番、初期付与・緊急停止手順
4. service operator MFAのprovider、recovery code保管者、端末紛失時の第二確認者
5. circle managerへ将来MFAを要求する実測上の判断基準
6. circle削除・非公開化の復元可能期間と公開規約文面
7. custom SMTP、送信元domain、到達性監視と費用
8. bundle identifier / package name、Universal Links / App Links domain、OAuth callbackのenvironment別実値

Googleとemail/passwordのidentity linkingは、同じサービスaccountへ本人が明示的にlinkする方式を採用する。provider emailの一致だけによる自動mergeは行わない。

## 19. 参考にした公式仕様

- [Supabase Auth](https://supabase.com/docs/guides/auth)
- [Supabase User Management](https://supabase.com/docs/guides/auth/managing-user-data)
- [Supabase Users and identities](https://supabase.com/docs/guides/auth/users)
- [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase Auth with React Native](https://supabase.com/docs/guides/auth/quickstarts/react-native)
- [Supabase JWT](https://supabase.com/docs/guides/auth/jwts)
- [Supabase Google login](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [Supabase server package selection](https://supabase.com/docs/guides/auth/choosing-a-server-package)
- [Expo Linking](https://docs.expo.dev/linking/overview/)
- [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Google OpenID Connect ID token validation](https://developers.google.com/identity/openid-connect/openid-connect)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP MASVS](https://mas.owasp.org/MASVS/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
