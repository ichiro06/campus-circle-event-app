# UI / UX Design Guidelines

- 状態: 正式なプロジェクト共通方針
- 用途: 将来のUI実装・UXレビュー・visual refinementの基準
- 対象: iOS / Android向けCampus Circle Event App
- この文書の性格: docs-onlyの設計方針。画面実装、デザイン変更、依存追加、製品要件の確定を行う文書ではない。

## 1. Purpose

この文書は、構造・機能の実装がある程度進み、UIのvisual polishとUX refinementを本格的に検討する段階で参照する基準を定める。

本プロジェクトでは、Apple Human Interface Guidelines（HIG）とMaterial Design 3（M3）を主要な公式リファレンスとして使用する。ただし、公式資料の見た目や文章をそのままコピーすることを目的としない。次の設計判断を行うための一次資料として使う。

- platform convention
- navigation
- component behavior
- layout
- typography
- spacing
- interaction
- feedback
- motion
- accessibility
- system integration

この文書は、正式なproduct requirement、security・privacy要件、API契約、認証・認可、非機能要件を置き換えない。具体的な画面の採否や仕様変更が必要になった場合は、既存の正式文書とHuman Decisionを優先する。

## 2. 適用するDesign Phase

この方針は、次の条件がそろった後のdesign refinement phaseで本格適用する。

- 主要screenとnavigationがそろっている
- 主要featureの構造が安定している
- API contractと主要data flowが安定している
- functional vertical sliceがある程度完成している
- visual polish・UX refinementへ移る判断ができる

現在の実装を、デザイン目的だけで大規模refactorしない。先に機能・API・認証・認可を安定させ、デザイン作業が既存の受入条件や安全境界を壊さないようにする。

デザインを先行して検討する場合も、既存画面を「最終デザイン完成」とは扱わず、仮の構造・状態を検討するための材料として扱う。

## 3. Official References

### Apple Human Interface Guidelines

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Apple Design Principles](https://developer.apple.com/design/human-interface-guidelines/design-principles)
- [Apple HIG: Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)

iOSのplatform-specificな設計では、HIGを第一参照とする。HIGの最新版、対象OS、対象componentの記載を、実装またはレビューの時点で確認する。このrepositoryにHIGの本文を大量に転載しない。

### Material Design 3

- [Material Design 3](https://m3.material.io/)
- [Material 3: Color system](https://m3.material.io/styles/color/the-color-system)
- [Material 3: Motion](https://m3.material.io/styles/motion)

Androidのplatform-specificな設計では、M3を第一参照とする。M3の最新版、対象Android version、対象componentの記載を、実装またはレビューの時点で確認する。このrepositoryにM3の本文を大量に転載しない。

### Referenceの更新方針

公式guidelineは更新される可能性がある。ここに記載したURLを固定的なcomponent仕様やpixel値として扱わず、design work開始時に公式資料の最新版を再確認する。参照先が移転・統合された場合は、URLと確認日だけを更新し、内容の大量転載は行わない。

## 4. Platform Strategy

### iOS

- HIGをplatform-specificな第一参照とする。
- tab、stack、back、sheet、dialog、system permissionなど、iOS利用者が期待するnavigationとsystem behaviorを尊重する。
- safe area、Dynamic Type、VoiceOver、system gesture、通知やshare等のOS連携を確認する。
- React Nativeで共通化できる場合でも、iOSの操作感を不自然にAndroid寄りへ寄せない。

### Android

- M3をplatform-specificな第一参照とする。
- Androidのback behavior、system navigation、permission、sheet、dialog、selection controlなどの慣例を尊重する。
- font scaling、TalkBack、contrast、touch target、端末サイズ差を確認する。
- React Nativeで共通化できる場合でも、Androidの操作感を不自然にiOS寄りへ寄せない。

### Shared Product Identity

iOSとAndroidで共通に保つ対象は、次のような「ホウクルとしての意味」とする。

- information architecture
- brand identity
- 主要content
- contentの優先順位
- terminology
- 状態の意味
- interactionの結果
- 基本的な色の役割
- spacing system
- Circle Cardの情報構成
- loading・empty・error・offlineの意味
- privacy・security上の注意や確認

共通性は、全platformで同じpixel配置・同じcomponent表現にすることを意味しない。

## 5. Design Principles

### 明確さ

利用者が「この画面で何ができるか」「次に何が起きるか」を理解できるようにする。装飾よりも、目的・情報・操作の関係を優先する。

### 情報を比較しやすくする

サークルを探し、比較し、詳細を確認する用途を中心に、一覧では重要情報を短時間で把握できるようにする。secondary informationは優先度を下げ、detailへ自然に遷移できるようにする。

### 既知の慣例を尊重する

新しい操作方法を作る前に、iOS・Androidで利用者が知っているnavigation、back、selection、feedbackを使えるか確認する。

### 一貫性と文脈適応を両立する

ブランド・用語・状態の意味は一貫させる一方、platformの操作慣例、system control、gesture、motionは必要に応じて変える。

### 安心して操作できること

loading、success、error、disabled、pressed、selected、retry、refreshの状態を明示する。重要な変更、削除、権限操作、通報では結果と取り消し・再確認の有無を説明する。

### アクセシビリティを後付けにしない

視覚、聴覚、運動、認知の違いを考慮し、font scaling、screen reader、contrast、tap target、focus orderを設計初期から確認する。

### プライバシーと安全性を見た目より優先する

情報を見せることが便利でも、公開範囲、個人情報、管理者権限、通報・審査状態を誤認させるUIを作らない。ユーザーに不要な秘密情報を表示しない。

## 6. Information Hierarchy

design reviewでは、各画面で次を確認する。

- この画面の最重要目的は何か
- 一覧で最初に見る情報は何か
- Circle Cardに何を表示し、何をdetailへ送るか
- detailで情報をどのgroupに分けるか
- primary actionとsecondary actionが区別されているか
- 関連性の低い情報・補足説明を適切に弱めているか
- 公開情報、申請状態、管理者だけの情報が視覚的に混ざっていないか
- loading・empty・error・offline時にも、利用者が次の行動を理解できるか

既存の画面構成、route、状態の意味は [screen-flow.md](screen-flow.md) を正とする。UI方針の検討だけで、4タブ、stack、認証境界、manager権限境界を変更しない。

## 7. Navigation and Interaction

### Navigation

現在の初期navigationは4タブとstackを基本とする。

- ホーム
- 検索
- お気に入り
- マイページ
- サークル詳細はstack
- manager・service operatorの保護画面はマイページから、serverの権限確認後に開く

design reviewでは、次をplatform別に確認する。

- tab navigationの役割と現在位置
- stack navigationとback behavior
- deep linkから開いた場合の戻り先
- modal / sheetを使う理由と閉じ方
- OSのback gesture・back buttonとの整合
- 失敗時に元のcontextへ戻れるか
- 重要な操作を画面上のbuttonを隠すだけで保護していないか

### Interaction

操作の結果は、画面の変化、status、feedbackで利用者に伝える。

- pressed、selected、disabled、focusedを区別する
- retry・refresh・cancelなどの操作可能な選択肢を明示する
- 二重送信や連続操作を防ぐ
- 失敗時に入力内容や直前の正常データを可能な範囲で保持する
- offline時に、送信済みと未送信を混同させない
- 権限不足、審査中、却下、公開済みを同じ見た目で表示しない

## 8. Components

将来のdesign system・component reviewでは、少なくとも次を対象にする。

- Circle Card
- buttons
- chips
- badges
- search controls
- filters
- lists
- forms
- dialogs
- sheets
- loading
- empty
- error
- offline state

componentは見た目だけでなく、次のbehaviorを定義してから実装する。

- semantic roleとaccessible label
- enabled / disabled / pressed / selected / focused
- loading中の操作可否
- success・error時のfeedback
- 長い日本語、空値、画像なし、複数行への耐性
- iOSとAndroidで変える部分、共通にする部分
- screen readerの読み上げ順序
- hit areaとgesture
- dataが未取得・取得済み・古い・失敗した状態

現時点では、特定のUI component library、デザイントークン、色値、font family、icon setを正式採用しない。実装時に選定が必要になった場合は、依存追加・保守・両platform対応を含む別の判断として記録する。

## 9. Typography and Layout

### Typography

- 見出し、本文、補足、状態、actionのhierarchyを明確にする。
- 長い日本語text、サークル名、活動説明、エラーメッセージの折り返しを確認する。
- Dynamic Type / font scaling、端末設定による拡大、最小文字サイズを確認する。
- font weightや色だけに頼らず、見出し・順序・spacingでもhierarchyを伝える。
- localizationや将来の文言変更でレイアウトが壊れない余白を確保する。

### Layout / spacing

- spacingは画面ごとに場当たり的な値を増やさず、共通systemとして検討する。
- safe area、status bar、home indicator、Android system barsを考慮する。
- 端末サイズ差、画面密度、縦向き、キーボード表示、orientation差を確認する。
- 情報密度を上げるために、tap target、行間、読みやすさを犠牲にしない。
- 画像・カード・リストの縦横比を固定しすぎず、欠損・長文・読み込み中に耐える。
- keyboard、sheet、dialogで重要な操作が隠れないようにする。

## 10. States and Feedback

既存の共通状態と画面受入条件は [screen-flow.md](screen-flow.md) を正とし、visual refinementでは次を確認する。

| 状態 | designで確認すること |
| --- | --- |
| loading | 何を待っているか、過剰な全画面spinnerになっていないか、既存データを残せるか |
| empty | データがない理由と、次にできる操作が分かるか |
| error | 原因を断定しすぎず、再試行・戻る・問い合わせ等の次の行動を示せるか |
| offline | network未接続、未送信、再取得待ちを区別できるか |
| disabled | なぜ操作できないか、回復方法が分かるか |
| success | 操作結果が確認でき、二重操作を誘発しないか |
| selected | 選択状態が色だけに依存していないか |
| permission / review | 未申請、審査中、承認、却下、失効を混同させないか |

300ms以内に終わる処理へ不要な全画面spinnerを出さない、再取得時に正常データを不必要に消さない等の具体的な状態契約は、screen-flowとAPI契約を優先する。visual designによって状態の意味を変えない。

## 11. Motion

- motionは必要な場面だけ使用し、操作理解・状態変化・navigationのcontextを助ける目的を優先する。
- 装飾のために、読み込み・入力・screen reader・低性能端末を妨げるアニメーションを追加しない。
- transition、sheet、refresh、selectionのmotionが、platform conventionと矛盾しないか確認する。
- Reduce MotionなどのOS設定と、利用者がmotionを減らしたい場合を考慮する。
- motion完了を待たないと操作できない設計にしない。
- duration、easing、physicsなどの具体値は、対象platformとcomponentを確認したdesign workで決める。

## 12. Accessibility

将来のUI実装・レビューでは、少なくとも次を確認する。

- VoiceOver（iOS）
- TalkBack（Android）
- Dynamic Type / font scaling
- color contrast
- tap target
- accessible label / role / hint
- focus order
- キーボードや外部入力を使う場合のfocus
- 色だけに依存しない状態表示
- 画像・アイコンの代替説明
- エラーを見た目だけでなく読み上げでも伝える
- 長文・拡大表示・画面回転や端末サイズ差への耐性
- Reduce Motion等のOS設定

アクセシビリティの具体的な受入値は [non-functional-requirements.md](non-functional-requirements.md) と対象platformの公式資料を参照する。デザイン上の都合で、確定済みのaccessibility要件を下げない。

## 13. Cross-platform Consistency

### 同一に保つ対象

- information architecture
- brand identity
- 主要content
- terminology
- 状態の意味
- interaction結果
- privacy・security上の説明
- 主要な情報優先順位

### platformごとに調整してよい対象

- component styling
- navigation convention
- system gesture
- back behavior
- motion
- sheet / dialog behavior
- native control appearance
- selection control
- platformのpermission・share・notification連携

iOSとAndroidで同じ情報を提供しても、同じcomponent、同じgesture、同じtransition、同じ配置に固定しない。逆に、platform差を理由にproduct terminologyや状態の意味を変えない。

## 14. Conflict / Decision Handling

設計判断が衝突した場合の優先順位は次のとおりとする。

1. 正式なproduct requirement / Human Decision
2. security / privacy / accessibility requirement
3. platform-specific guideline
   - iOS: Apple HIG
   - Android: Material Design 3
4. project共通design guideline
5. 個別画面のvisual preference

正式なproduct requirementとplatform guidelineに明確なUX上の衝突が見つかった場合、AIや実装担当者が勝手に要件を変更しない。衝突内容、影響、候補、必要な受入条件をHuman Decision候補として報告する。

この文書の追加・変更だけで、product requirement、screen-flow、API、DB schema、認証・認可、非機能要件を変更したことにはしない。変更が必要な場合は、対象の正式文書とdecision historyを同じ変更範囲で更新する。

## 15. Relationship to Current Implementation

現在のW4 Public Circle Sliceは、公開サークルreadを成立させるためのfunctional implementationである。この文書の追加によって、W4のscope、完了条件、API契約、実装済み判定を遡及的に変更しない。

現在のHome、Search、Circle Card、Circle Detail等を、次の状態とは扱わない。

- HIG完全準拠
- Material 3完全準拠
- final visual design完成
- すべてのaccessibility・native behavior確認済み

将来のdesign refinement phaseで、この文書と対象platformの公式資料に基づき、既存画面をレビュー・改善する。改善時も、まずfunctional behavior、API状態、権限境界、既存の受入条件を維持できるか確認する。

本書はUI実装の開始を意味しない。UI実装、デザイン変更、component library導入、Figma連携、画像・iconの追加は、別の明示されたworkで行う。

## 16. Review Checklist

将来のUI実装・visual refinement Pull Requestでは、対象範囲に応じて次を確認する。

### Product and scope

- [ ] 正式なproduct requirementと画面目的を確認した
- [ ] W4や対象workのscope・完了条件を遡及的に変更していない
- [ ] 未確定の要件をUI都合で確定していない
- [ ] platform guidelineとの衝突をHuman Decisionへ戻した
- [ ] UIだけで認証・認可を実装したことにしていない

### Platform behavior

- [ ] iOSでHIG上のplatform conventionを確認した
- [ ] AndroidでMaterial 3上のplatform conventionを確認した
- [ ] 両platformを無理に同一UIへしていない
- [ ] native back / navigation behaviorを確認した
- [ ] deep link、modal、sheet、dialogの戻り方を確認した
- [ ] system permission、share、notification等のOS連携を確認した
- [ ] Reduce MotionなどのOS設定を考慮した

### Information and components

- [ ] typography hierarchyが明確である
- [ ] spacingが一貫している
- [ ] Circle Cardの主要情報とsecondary informationが区別されている
- [ ] buttons、chips、badges、filters、formsの役割が明確である
- [ ] 長い日本語、空値、画像なし、複数行に耐える
- [ ] loading / empty / error / offlineを考慮した
- [ ] pressed / selected / disabled / focusedを区別した
- [ ] 二重送信や誤操作を防いだ

### Accessibility

- [ ] Dynamic Type / font scalingを確認した
- [ ] VoiceOverを確認した
- [ ] TalkBackを確認した
- [ ] accessible label / role / focus orderを確認した
- [ ] tap targetを確認した
- [ ] contrastを確認した
- [ ] 色だけで状態を伝えていない
- [ ] エラー、成功、選択、権限状態を読み上げでも理解できる
- [ ] 端末サイズ、safe area、キーボード表示を確認した

### Verification and documentation

- [ ] 対象iOS Simulator / Android Emulatorで確認した
- [ ] 必要な場合は実機でも確認した
- [ ] 実施しなかった確認と理由を報告した
- [ ] 公式HIG / M3の参照箇所をPRに記載した
- [ ] 仕様・構成・受入条件が変わる場合、関連docsとdecision historyを更新した
