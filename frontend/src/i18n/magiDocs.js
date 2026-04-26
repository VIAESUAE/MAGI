/**
 * User guide and disclaimer strings for zh / en / ja (merged in App.vue I18N).
 */
export const magiDocs = {
  zh: {
    userGuideButton: '使用說明',
    guideModalTitle: '使用說明',
    guideBody: `如何使用 MAGI

本介面不會向 MAGI 後端上傳你的可識別個人資料；API Key 與模型等設定僅儲存在本機瀏覽器（localStorage）。請保護好你的裝置與瀏覽器存取權限。

一、註冊 OpenRouter 並取得 API Key
OpenRouter 為第三方模型聚合服務。請至官網註冊與登入：
https://openrouter.ai/
可使用 Google、GitHub 或 Email 建立帳號。登入後前往「API Keys」，點「Create」建立金鑰（有免費與付費等方案）。金鑰全文通常僅在建立當下完整顯示一次，請立即複製並儲存於你信任的位置；若遺失需重新建立。

二、在 MAGI 內填寫金鑰與模型
將金鑰貼到本頁「MAGI API Key」欄位。點「拉取 OpenRouter 模型」取得可用清單，再為三個節點（Melchior、Balthasar、Casper）各選一個模型。免費模型中，實測相對穩定者包括 gpt-oss-120b、Google Gemma 等；實際可用性隨 OpenRouter 與供應商而變，請自測。

三、分析流程
依 Architect（架構師）引導補足題目、背景與限制條件；描述越具體，產出之參考價值越高。在提訴—決議階段完成後，點「報告」可檢視完整內容。`,
    disclaimerModalTitle: '免責聲明',
    disclaimerBody: `本軟體（MAGI）僅作為多模型輔助討論與參考用途之實驗性介面，不構成任何法律、醫療、投資、稅務或其他專業意見，亦不保證輸出之正確性、完整性或即時性。

人工智慧產生之內容可能包含錯誤、偏見或過時資訊。你應自行判斷並承擔使用本軟體之全部風險與後果。開發者與相關授權方對你因使用或無法使用本軟體所造成之任何直接、間接、附帶或衍生性損害不負任何責任，於法所允之最大範圍內如此聲明。

你透過本介面所使用之服務、模型、計費與資料處理，以 OpenRouter 及各家模型供應商之條款為準。請你遵守 OpenRouter 之使用政策與金鑰安全建議。若不同意上述內容，請勿使用本介面。`,
    disclaimerFooterLink: '查看免責聲明'
  },
  en: {
    userGuideButton: 'User Guide',
    guideModalTitle: 'User Guide',
    guideBody: `How to use MAGI

This app does not upload identifiable personal data to MAGI servers. API keys and settings are stored only in your browser (localStorage). Protect access to your device and browser.

1) Sign in to OpenRouter and create a key
OpenRouter is a third-party model gateway. Create an account and sign in at:
https://openrouter.ai/
You can use Google, GitHub, or email. In API Keys, click Create to generate a key (free and paid options exist). The full key is often shown only once when created—copy it immediately and store it somewhere you trust; if you lose it, create a new key.

2) Configure MAGI
Paste the key into MAGI API Key, click Fetch OpenRouter Models, then choose one model for each of the three nodes (Melchior, Balthasar, Casper). Some free models (e.g. gpt-oss-120b, Google Gemma) have been reliable in our tests, but availability changes—verify what works for you on OpenRouter.

3) Run the flow
Follow the Architect to clarify your question, context, and constraints. More detail usually yields more useful output. When the Indictment–Resolution stage is done, open Report for the full result.`,
    disclaimerModalTitle: 'Disclaimer',
    disclaimerBody: `MAGI is an experimental front end for multi-model discussion and must not be treated as legal, medical, financial, tax, or other professional advice. AI-generated content may be wrong, biased, or outdated. No warranty is made as to accuracy, completeness, or timeliness.

You are solely responsible for how you use this software. To the maximum extent permitted by law, the developers and their licensors disclaim all liability for any direct, indirect, incidental, or consequential damages arising from use or inability to use the software.

Your use of OpenRouter and each model is governed by their respective terms, pricing, and policies. You must comply with OpenRouter’s requirements and keep your key secure. If you do not accept these terms, do not use this app.`,
    disclaimerFooterLink: 'View disclaimer'
  },
  ja: {
    userGuideButton: 'ご利用案内',
    guideModalTitle: 'ご利用案内',
    guideBody: `MAGI の使い方

MAGI サーバーに個人を特定できる情報を送信する仕組みではありません。API Key や各種設定はブラウザの localStorage に保存されます。端末とブラウザの管理にご注意ください。

1) OpenRouter に登録し API Key を発行
OpenRouter は第三者のモデルゲートウェイです。次の URL でアカウント登録とログインを行います。
https://openrouter.ai/
Google、GitHub、メール等で登録可能です。ログイン後、API Keys から Create でキーを発行します（無償・有償の区分あり）。表示全文は多くの場合、発行時に一度限りのため、直ちにコピーし信頼できる場所に保管してください。紛失した場合は新規に発行します。

2) MAGI への反映
「MAGI API Key」欄に貼り付け、「OpenRouter モデル取得」で一覧を取得し、3 ノード（Melchior / Balthasar / Casper）それぞれにモデルを割り当てます。無償モデルでは gpt-oss-120b や Google Gemma 等が比較的安定しやすい例がありますが、利用可否は OpenRouter 側の状況で変動するため、必ず自己確認してください。

3) 作業の流れ
アーキテクトの案内に沿って、課題・背景・制約条件を具体化します。記述が詳しいほど有用なまとまりになりやすいです。提訴—決議の流れの後、「レポート」で全体を確認できます。`,
    disclaimerModalTitle: '免責事項',
    disclaimerBody: `本ソフトウェア（MAGI）は、複数モデルによる補助的な検討用の実験的なインターフェースであり、法的助言、医療、投資、税務等の専門的意見を構成しません。AI 出力の正確性・完全性・最新性を保証するものではありません。

生成結果には誤り、偏り、古い情報が含まれる可能性があります。利用は自己責任であり、本ソフトの利用又は利用不能に起因するいかなる損害についても、法的に認められる最大限の範囲で開発者およびライセンサーは一切責任を負いません。

OpenRouter 及び各モデル提供元の提供条件・料金・取扱いに従ってください。OpenRouter の方針とキーの取り扱いを遵守してください。本内容に同意できない場合は、本インターフェースを利用しないでください。`,
    disclaimerFooterLink: '免責事項を表示'
  }
}
