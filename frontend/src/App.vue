<template>
  <div class="app-container">
    <WelcomeView
      v-if="showWelcome"
      :title="t('welcomeTitle')"
      :subtitle="t('welcomeSubtitle')"
      :hint="t('welcomeHint')"
      @dismiss="dismissWelcome"
    />
    <div class="lang-switcher">
      <label class="lang-label">{{ t('language') }}</label>
      <select v-model="locale" class="lang-select">
        <option value="zh">{{ t('lang.zh') }}</option>
        <option value="en">{{ t('lang.en') }}</option>
        <option value="ja">{{ t('lang.ja') }}</option>
      </select>
      <button type="button" class="lang-guide-btn" @click="openUserGuide">
        {{ t('userGuideButton') }}
      </button>
    </div>
    <DocModal
      v-if="showGuideModal"
      :title="t('guideModalTitle')"
      :body="t('guideBody')"
      :close-label="t('close')"
      @close="closeUserGuide"
    />
    <DocModal
      v-if="showDisclaimerModal"
      :title="t('disclaimerModalTitle')"
      :body="t('disclaimerBody')"
      :close-label="t('close')"
      @close="closeDisclaimer"
    />
    <component
      :is="currentView"
      v-bind="viewProps"
      @transition="handleTransition"
      @architect-submit="onArchitectSubmit"
      @abort-stream="onAbortStream"
      @validate-start="onValidateStart"
      @view-report="onViewReport"
      @open-disclaimer="openDisclaimer"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { getInitialLocale } from './utils/localeDetect.js'
import { magiDocs } from './i18n/magiDocs.js'
import DocModal from './components/DocModal.vue'
import WelcomeView from './views/WelcomeView.vue'
import StandbyView from './views/StandbyView.vue'
import ArchitectAnalysisView from './views/ArchitectAnalysisView.vue'
import TriCoreProcessingView from './views/TriCoreProcessingView.vue'
import ResolutionView from './views/ResolutionView.vue'
import { consumeMagiStream } from './api/magiStream.js'
import { preflightMagi } from './api/magiApi.js'

const I18N = {
  zh: {
    language: '語言',
    'lang.zh': '繁體中文',
    'lang.en': 'English',
    'lang.ja': '日本語',
    statusApprove: '承認',
    statusDeny: '否決',
    statusPending: '審議中',
    statusStandby: '待機',
    minimalConfirmFallback: '當前資訊不足。如果問題複雜程度較低，可以生成最小決議草案，是否確認？',
    minimalConfirmCancelled: '已取消最小決議草案。請補充關鍵資訊後再繼續。',
    preflightError: '模型連通性檢測失敗，請檢查 key／模型設定後重試。',
    traceArchitectStart: '架構師階段啟動',
    traceNeedClarify: '需要補充資訊',
    traceDraftReady: '判定草案已生成',
    traceTriStart: '第一輪三核盲審啟動',
    traceNodeStarted: '節點開始分析',
    traceNodeCompleted: '節點完成分析',
    traceRound2Start: '第二輪會審啟動',
    traceRound2NodeCompleted: '第二輪節點完成',
    traceBusReady: '中轉彙總已生成',
    traceSynthesisDone: '仲裁完成',
    traceCompleted: '流程完成',
    confirm: '確認',
    cancel: '取消',
    close: '關閉',
    back: '返回',
    processing: '處理中...',
    abort: '中止',
    report: '報告',
    again: '再次開始',
    exit: '退出',
    unknown: '未知',
    agree: '同意',
    disagree: '反對',
    finalResolution: '最終決議',
    consensusAnalysis: '共識分析',
    vote: '票型',
    nodeDiagnostics: '節點診斷',
    noNodeReport: '未返回節點報告。',
    rulingExplanation: '裁決說明',
    reviewWorkflow: '回顧整體流程',
    workflowReview: '流程回顧',
    draftSnapshot: '商議草案快照',
    finalSummary: '最終總結',
    timeline: '流程時間線',
    noDraftSnapshot: '未找到草案快照。',
    minimalDraftConfirmTitle: '當前資訊不足，如果問題複雜程度較低，可以生成最小決議草案，是否確認？',
    architectInputPlaceholder: '請輸入你的需求...',
    architectDefaultMessage: '架構師正在準備引導問題，請先輸入你的初始需求。',
    standbyTitle: 'MAGI 系統初始化',
    standbySubtitle: '多智能體共識框架',
    configApiCredentials: '配置 API 憑證',
    frontendDebugMode: '前端調試模式（斷開後端）',
    advanced: '高級',
    defaultApiKeyLabel: 'MAGI API Key（預設作用於三節點）',
    openrouterKeyPlaceholder: 'OpenRouter key...',
    melchiorModel: 'Melchior-1 模型',
    balthasarModel: 'Balthasar-2 模型',
    casperModel: 'Casper-3 模型',
    saveConfig: '保存配置',
    loadingModels: '正在載入模型...',
    fetchOpenrouterModels: '拉取 OpenRouter 模型',
    pingingModels: '檢測模型中...',
    startDebugFlow: '啟動調試流程',
    startAnalysis: '開始分析',
    ok: 'OK',
    fail: '失敗',
    standbyFooterTip: '配置會保存在 localStorage。調試模式下不會請求後端，只用於流程預覽。',
    advancedKeyRouting: '高級 Key 路由',
    melchiorApiOverride: 'Melchior-1 API Key（可選覆蓋）',
    balthasarApiOverride: 'Balthasar-2 API Key（可選覆蓋）',
    casperApiOverride: 'Casper-3 API Key（可選覆蓋）',
    leaveEmptyUseDefault: '留空則使用預設 key',
    configSaved: '配置已保存',
    missingApiKeyAlert: '開始前請先配置預設 API key（或 3 個高級覆蓋 key）。',
    fillApiBeforeFetch: '請先填寫至少一個 API key 再拉取模型列表。',
    emptyModelList: 'OpenRouter 返回了空模型列表。',
    triTitleLeft: '提 訴',
    triTitleRight: '決 議',
    nodeEventsFromBackend: '來自後端的節點事件',
    welcomeTitle: 'MAGI 戰略共識介面',
    welcomeSubtitle: '多智能體戰略決策｜戰術作戰支援',
    welcomeHint: '點擊畫面或按任意鍵開始',
    ...magiDocs.zh
  },
  en: {
    language: 'Language',
    'lang.zh': 'Chinese',
    'lang.en': 'English',
    'lang.ja': 'Japanese',
    statusApprove: 'APPROVED',
    statusDeny: 'DENIED',
    statusPending: '審議中',
    statusStandby: 'STANDBY',
    minimalConfirmFallback: 'Current information is insufficient. If this is a low-complexity question, a minimal draft can be generated. Confirm?',
    minimalConfirmCancelled: 'Minimal draft generation cancelled. Please provide key details to continue.',
    preflightError: 'Model connectivity check failed. Please verify key/model settings and retry.',
    traceArchitectStart: 'Architect phase started',
    traceNeedClarify: 'More information required',
    traceDraftReady: 'Resolution draft prepared',
    traceTriStart: 'Round-1 tri-core review started',
    traceNodeStarted: 'Node started',
    traceNodeCompleted: 'Node completed',
    traceRound2Start: 'Round-2 review started',
    traceRound2NodeCompleted: 'Round-2 node completed',
    traceBusReady: 'Bus summary prepared',
    traceSynthesisDone: 'Synthesis completed',
    traceCompleted: 'Workflow completed',
    confirm: 'Confirm',
    cancel: 'Cancel',
    close: 'Close',
    back: 'Back',
    processing: 'Processing...',
    abort: 'Abort',
    report: 'Report',
    again: 'Again',
    exit: 'Exit',
    unknown: 'Unknown',
    agree: 'Agree',
    disagree: 'Disagree',
    finalResolution: 'Final Resolution',
    consensusAnalysis: 'Consensus Analysis',
    vote: 'Vote',
    nodeDiagnostics: 'Node Diagnostics',
    noNodeReport: 'No node report returned.',
    rulingExplanation: 'Ruling Explanation',
    reviewWorkflow: 'Review Whole Workflow',
    workflowReview: 'Workflow Review',
    draftSnapshot: 'Draft Snapshot',
    finalSummary: 'Final Summary',
    timeline: 'Timeline',
    noDraftSnapshot: 'No draft snapshot found.',
    minimalDraftConfirmTitle: 'Current information is insufficient. If this is a low-complexity question, a minimal draft can be generated. Confirm?',
    architectInputPlaceholder: 'Please describe your request...',
    architectDefaultMessage: 'The architect is preparing guidance. Please enter your initial request.',
    standbyTitle: 'MAGI System Initialization',
    standbySubtitle: 'Multi-Agent Consensus Framework',
    configApiCredentials: 'Configure API Credentials',
    frontendDebugMode: 'Frontend Debug Mode (disconnect backend)',
    advanced: 'Advanced',
    defaultApiKeyLabel: 'MAGI API Key (default for all three nodes)',
    openrouterKeyPlaceholder: 'OpenRouter key...',
    melchiorModel: 'Melchior-1 Model',
    balthasarModel: 'Balthasar-2 Model',
    casperModel: 'Casper-3 Model',
    saveConfig: 'Save Config',
    loadingModels: 'Loading Models...',
    fetchOpenrouterModels: 'Fetch OpenRouter Models',
    pingingModels: 'Pinging Models...',
    startDebugFlow: 'Start Debug Flow',
    startAnalysis: 'Start Analysis',
    ok: 'OK',
    fail: 'Fail',
    standbyFooterTip: 'Keys/config are stored in localStorage. Debug mode runs local flow preview only.',
    advancedKeyRouting: 'Advanced Key Routing',
    melchiorApiOverride: 'Melchior-1 API Key (optional override)',
    balthasarApiOverride: 'Balthasar-2 API Key (optional override)',
    casperApiOverride: 'Casper-3 API Key (optional override)',
    leaveEmptyUseDefault: 'leave empty to use default key',
    configSaved: 'Config saved successfully',
    missingApiKeyAlert: 'Configure a default API key (or 3 advanced overrides) before starting.',
    fillApiBeforeFetch: 'Fill at least one API key before fetching model list.',
    emptyModelList: 'OpenRouter returned an empty model list.',
    triTitleLeft: '提 訴',
    triTitleRight: '決 議',
    nodeEventsFromBackend: 'Node events from backend',
    welcomeTitle: 'MAGI CONSENSUS',
    welcomeSubtitle: 'Strategic interface · multi-agent alignment',
    welcomeHint: 'Click or press any key to start',
    ...magiDocs.en
  },
  ja: {
    language: '言語',
    'lang.zh': '中国語',
    'lang.en': '英語',
    'lang.ja': '日本語',
    statusApprove: '承認',
    statusDeny: '否決',
    statusPending: '審議中',
    statusStandby: '待機',
    minimalConfirmFallback: '現在の情報は不足しています。問題が低複雑度なら最小決議ドラフトを生成できます。実行しますか？',
    minimalConfirmCancelled: '最小決議ドラフトの生成をキャンセルしました。続行するには情報を補足してください。',
    preflightError: 'モデル接続チェックに失敗しました。キー/モデル設定を確認して再試行してください。',
    traceArchitectStart: 'アーキテクト段階を開始',
    traceNeedClarify: '追加情報が必要',
    traceDraftReady: '決議ドラフトを生成',
    traceTriStart: '第1ラウンド三核審議を開始',
    traceNodeStarted: 'ノード分析開始',
    traceNodeCompleted: 'ノード分析完了',
    traceRound2Start: '第2ラウンド審議を開始',
    traceRound2NodeCompleted: '第2ラウンドノード完了',
    traceBusReady: '中継サマリー生成完了',
    traceSynthesisDone: '統合裁定完了',
    traceCompleted: 'ワークフロー完了',
    confirm: '確認',
    cancel: 'キャンセル',
    close: '閉じる',
    back: '戻る',
    processing: '処理中...',
    abort: '中止',
    report: 'レポート',
    again: '再実行',
    exit: '終了',
    unknown: '不明',
    agree: '賛成',
    disagree: '反対',
    finalResolution: '最終決議',
    consensusAnalysis: '合意分析',
    vote: '票数',
    nodeDiagnostics: 'ノード診断',
    noNodeReport: 'ノードレポートがありません。',
    rulingExplanation: '裁定説明',
    reviewWorkflow: '全体フローを振り返る',
    workflowReview: 'フロー回顧',
    draftSnapshot: '審議ドラフト',
    finalSummary: '最終まとめ',
    timeline: 'タイムライン',
    noDraftSnapshot: 'ドラフト情報がありません。',
    minimalDraftConfirmTitle: '情報が不足しています。問題が低複雑度の場合、最小決議ドラフトを生成できます。実行しますか？',
    architectInputPlaceholder: '要件を入力してください...',
    architectDefaultMessage: 'アーキテクトが案内を準備中です。初期要件を入力してください。',
    standbyTitle: 'MAGI システム初期化',
    standbySubtitle: 'マルチエージェント合意フレームワーク',
    configApiCredentials: 'API 認証情報の設定',
    frontendDebugMode: 'フロントエンドデバッグモード（バックエンド切断）',
    advanced: '詳細設定',
    defaultApiKeyLabel: 'MAGI API Key（3ノード共通）',
    openrouterKeyPlaceholder: 'OpenRouter key...',
    melchiorModel: 'Melchior-1 モデル',
    balthasarModel: 'Balthasar-2 モデル',
    casperModel: 'Casper-3 モデル',
    saveConfig: '設定保存',
    loadingModels: 'モデル読込中...',
    fetchOpenrouterModels: 'OpenRouter モデル取得',
    pingingModels: 'モデル確認中...',
    startDebugFlow: 'デバッグフロー開始',
    startAnalysis: '解析開始',
    ok: 'OK',
    fail: '失敗',
    standbyFooterTip: '設定は localStorage に保存されます。デバッグモードはローカル表示確認専用です。',
    advancedKeyRouting: '詳細キー振り分け',
    melchiorApiOverride: 'Melchior-1 API Key（任意上書き）',
    balthasarApiOverride: 'Balthasar-2 API Key（任意上書き）',
    casperApiOverride: 'Casper-3 API Key（任意上書き）',
    leaveEmptyUseDefault: '空欄なら既定キーを使用',
    configSaved: '設定を保存しました',
    missingApiKeyAlert: '開始前に既定 API key（または3つの上書きキー）を設定してください。',
    fillApiBeforeFetch: 'モデル取得前に少なくとも1つの API key を入力してください。',
    emptyModelList: 'OpenRouter から空のモデル一覧が返されました。',
    triTitleLeft: '提 訴',
    triTitleRight: '決 議',
    nodeEventsFromBackend: 'バックエンドからのノードイベント',
    welcomeTitle: 'MAGI コンセンサス',
    welcomeSubtitle: 'マルチエージェント戦略インターフェース',
    welcomeHint: '画面をクリックするか、任意のキーで開始',
    ...magiDocs.ja
  }
}

const WELCOME_KEY = 'magi_welcome_seen'
const GUIDE_DISMISSED_KEY = 'magi_user_guide_dismissed'
const showWelcome = ref(
  typeof sessionStorage === 'undefined' ? true : !sessionStorage.getItem(WELCOME_KEY)
)
const showGuideModal = ref(false)
const showDisclaimerModal = ref(false)

function openUserGuide() {
  showGuideModal.value = true
}

function closeUserGuide() {
  showGuideModal.value = false
  if (typeof sessionStorage !== 'undefined') {
    try {
      sessionStorage.setItem(GUIDE_DISMISSED_KEY, '1')
    } catch {
      /* ignore */
    }
  }
}

function openDisclaimer() {
  showDisclaimerModal.value = true
}

function closeDisclaimer() {
  showDisclaimerModal.value = false
}

function dismissWelcome() {
  if (typeof sessionStorage !== 'undefined') {
    try {
      sessionStorage.setItem(WELCOME_KEY, '1')
    } catch {
      /* ignore */
    }
  }
  showWelcome.value = false
  nextTick(() => {
    let shouldOpen = true
    if (typeof sessionStorage !== 'undefined') {
      try {
        if (sessionStorage.getItem(GUIDE_DISMISSED_KEY)) shouldOpen = false
      } catch {
        shouldOpen = true
      }
    }
    if (shouldOpen) showGuideModal.value = true
  })
}

const uiState = ref('STANDBY')
const locale = ref(getInitialLocale())

onMounted(() => {
  try {
    if (typeof localStorage === 'undefined') return
    if (!localStorage.getItem('magi_locale')) {
      localStorage.setItem('magi_locale', locale.value)
    }
  } catch {
    /* ignore */
  }
})

const tokens = ref({ claude: '', grok: '', gemini: '' })
const selectedModels = ref({ claude: '', grok: '', gemini: '' })
const accumulatedInput = ref('')
const architectMessage = ref('')
const minimalDraftConfirmPending = ref(false)
const streamError = ref(null)
const abortController = ref(null)
const streamActive = ref(false)
const preflightBusy = ref(false)
const preflightError = ref(null)
const preflightChecks = ref([])
const processTrace = ref([])

const triNodes = ref({
  melchior: { progress: 0, status: 'INITIALIZING', report: null },
  balthasar: { progress: 0, status: 'INITIALIZING', report: null },
  casper: { progress: 0, status: 'INITIALIZING', report: null }
})

const resolutionPayload = ref(null)
const triFinalVerdict = ref(null)
const triReportReady = ref(false)
const debugMode = ref(false)
const triStartAtMs = ref(0)
const nodeReveal = ref({ melchior: false, balthasar: false, casper: false })

const NODE_KEY = {
  'Melchior-1': 'melchior',
  'Balthasar-2': 'balthasar',
  'Casper-3': 'casper'
}

function t(key) {
  return I18N[locale.value]?.[key] ?? I18N.zh[key] ?? key
}

watch(locale, (next) => {
  try {
    if (typeof localStorage !== 'undefined') localStorage.setItem('magi_locale', next)
  } catch {
    /* private mode / blocked storage: ignore */
  }
})

function pushTrace(titleKey, detail = '', level = 'info') {
  processTrace.value = [
    ...processTrace.value,
    {
      id: `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
      title: t(titleKey),
      detail,
      level,
      timestamp: new Date().toISOString()
    }
  ]
}

function resetTriNodes() {
  triNodes.value = {
    melchior: { progress: 0, status: 'INITIALIZING', report: null },
    balthasar: { progress: 0, status: 'INITIALIZING', report: null },
    casper: { progress: 0, status: 'INITIALIZING', report: null }
  }
  nodeReveal.value = { melchior: false, balthasar: false, casper: false }
}

function mapReportStatus(status) {
  if (status === 'OK') return 'COMPLETE'
  if (status === 'TIMEOUT') return 'TIMEOUT'
  if (status === 'ACCESS_DENIED') return 'ACCESS_DENIED'
  return 'ERROR'
}

function patchTriNode(nodeId, patch) {
  const key = NODE_KEY[nodeId]
  if (!key) return
  const cur = triNodes.value[key]
  triNodes.value[key] = { ...cur, ...patch }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function revealNodesCeremonially() {
  const elapsed = Date.now() - triStartAtMs.value
  const minPulse = 1200
  if (elapsed < minPulse) await sleep(minPulse - elapsed)

  const order = ['melchior', 'balthasar', 'casper'].sort(() => Math.random() - 0.5)
  for (const key of order) {
    await sleep(500 + Math.floor(Math.random() * 500))
    nodeReveal.value = { ...nodeReveal.value, [key]: true }
  }
  triReportReady.value = true
}

function handleStreamEvent(evt) {
  if (evt.event === 'done') {
    streamActive.value = false
    abortController.value = null
    if (evt.status === 'needs_clarification') {
      uiState.value = 'ARCHITECT_ANALYSIS'
    }
    return
  }

  if (evt.event === 'error') {
    streamError.value = typeof evt.detail === 'string' ? evt.detail : JSON.stringify(evt.detail)
    pushTrace('traceCompleted', streamError.value, 'error')
    return
  }

  if (evt.event === 'ARCHITECT_ANALYSIS') {
    if (evt.phase === 'started') {
      architectMessage.value = evt.message || ''
      streamError.value = null
      pushTrace('traceArchitectStart', evt.message || '')
    }
    if (evt.phase === 'needs_clarification') {
      architectMessage.value = evt.message || (evt.architect?.questions || []).join('\n')
      minimalDraftConfirmPending.value = !!evt.architect?.confirmation_required
      pushTrace('traceNeedClarify', architectMessage.value)
    }
    if (evt.phase === 'draft_ready') {
      architectMessage.value = evt.message || ''
      minimalDraftConfirmPending.value = false
      resetTriNodes()
      triStartAtMs.value = Date.now()
      const draft = evt.architect?.resolution_draft
      const draftDesc = draft ? `core_request=${draft.core_request}` : ''
      pushTrace('traceDraftReady', draftDesc)
      uiState.value = 'TRI_CORE_PROCESSING'
    }
    return
  }

  if (evt.event === 'TRI_CORE_PROCESSING') {
    if (evt.phase === 'started') {
      pushTrace('traceTriStart', evt.message || '')
    }
    if (evt.phase === 'node_started') {
      patchTriNode(evt.node, { progress: 30, status: 'ROUND1_REQUESTING', report: null })
      pushTrace('traceNodeStarted', evt.node)
    }
    if (evt.phase === 'node_completed') {
      const r = evt.report
      patchTriNode(r.node, {
        progress: 65,
        status: `ROUND1_${mapReportStatus(r.status)}`,
        report: r
      })
      pushTrace('traceNodeCompleted', `${r.node} / ${r.status}`)
    }
    if (evt.phase === 'round_two_started') {
      for (const nodeId of ['Melchior-1', 'Balthasar-2', 'Casper-3']) {
        patchTriNode(nodeId, { progress: 80, status: 'ROUND2_REQUESTING' })
      }
      pushTrace('traceRound2Start', evt.message || '')
    }
    if (evt.phase === 'round_two_node_completed') {
      const r = evt.report
      patchTriNode(r.node, {
        progress: 100,
        status: `ROUND2_${mapReportStatus(r.status)}`,
        report: r
      })
      pushTrace('traceRound2NodeCompleted', `${r.node} / ${r.status}`)
    }
    return
  }

  if (evt.event === 'SYNTHESIS') {
    if (evt.phase === 'bus_report_ready') {
      pushTrace('traceBusReady', (evt.bus_report || '').slice(0, 160))
    }
    if (evt.phase === 'completed') {
      pushTrace('traceSynthesisDone', evt.synthesis?.vote_ratio || '')
    }
    return
  }

  if (evt.event === 'completed') {
    resolutionPayload.value = evt.response
    triFinalVerdict.value = evt.response?.synthesis?.verdict ?? null
    triReportReady.value = false
    streamActive.value = false
    abortController.value = null
    pushTrace('traceCompleted', evt.response?.synthesis?.verdict || '')
    revealNodesCeremonially()
  }
}

async function runResolveStream({ allowMinimalDraft = false } = {}) {
  if (!accumulatedInput.value?.trim()) return

  streamError.value = null
  streamActive.value = true
  abortController.value = new AbortController()
  triFinalVerdict.value = null
  triReportReady.value = false

  try {
    if (debugMode.value) {
      await runMockFlow(accumulatedInput.value)
      return
    }
    await consumeMagiStream(
      {
        user_input: accumulatedInput.value,
        tokens: tokens.value,
        models: selectedModels.value,
        allow_minimal_draft: allowMinimalDraft,
        locale: locale.value
      },
      {
        signal: abortController.value.signal,
        onEvent: handleStreamEvent
      }
    )
  } catch (e) {
    if (e.name === 'AbortError') return
    streamError.value = e.message || String(e)
  } finally {
    streamActive.value = false
    abortController.value = null
  }
}

async function onArchitectSubmit(payload) {
  const action = typeof payload === 'object' ? payload?.action : 'submit'
  if (action === 'confirm-minimal-draft') {
    await runResolveStream({ allowMinimalDraft: true })
    return
  }
  if (action === 'cancel-minimal-draft') {
    minimalDraftConfirmPending.value = false
    architectMessage.value = t('minimalConfirmCancelled')
    return
  }

  const text = typeof payload === 'string' ? payload : payload?.text
  const trimmed = text?.trim()
  if (!trimmed) return
  if (accumulatedInput.value) {
    accumulatedInput.value = `${accumulatedInput.value}\n\n${trimmed}`
  } else {
    accumulatedInput.value = trimmed
  }
  minimalDraftConfirmPending.value = false
  try {
    await runResolveStream()
  } catch (e) {
    streamError.value = e?.message || String(e)
    streamActive.value = false
    abortController.value = null
  }
}

async function runMockFlow(trimmed) {
  const mockMsg = locale.value === 'en'
    ? `Input received: "${trimmed}". Entering offline debug flow.`
    : locale.value === 'ja'
      ? `入力を受信しました：「${trimmed}」。オフラインデバッグフローに入ります。`
      : `已接收輸入：「${trimmed}」。正在進入離線調試流程。`
  architectMessage.value = mockMsg
  uiState.value = 'TRI_CORE_PROCESSING'
  resetTriNodes()
  streamActive.value = true
  triStartAtMs.value = Date.now()
  triFinalVerdict.value = null
  triReportReady.value = false

  const makeReport = (node, opinion, summary) => ({
    node,
    provider: 'DebugMock',
    status: 'OK',
    opinion,
    summary,
    key_points: [
      locale.value === 'en'
        ? 'Debug mode result; backend is not called.'
        : locale.value === 'ja'
          ? 'デバッグモード結果（バックエンド未接続）'
          : 'debug 模式結果，不呼叫後端'
    ],
    raw_text: null
  })

  const mockSummaries = {
    zh: ['離線模式下判斷：可執行。', '離線模式下判斷：現實約束不足。', '離線模式下判斷：個體價值可接受。'],
    en: ['Offline verdict: executable.', 'Offline verdict: real-world constraints are insufficient.', 'Offline verdict: individual value is acceptable.'],
    ja: ['オフライン判定：実行可能。', 'オフライン判定：現実制約が不足。', 'オフライン判定：個人価値は許容範囲。']
  }
  const langMock = mockSummaries[locale.value] || mockSummaries.zh
  const seq = [
    ['Melchior-1', true, langMock[0]],
    ['Balthasar-2', false, langMock[1]],
    ['Casper-3', true, langMock[2]]
  ]

  for (const [node, opinion, summary] of seq) {
    patchTriNode(node, { progress: 100, status: 'ROUND2_COMPLETE', report: makeReport(node, opinion, summary) })
    await new Promise((r) => setTimeout(r, 500))
  }

  const reports = Object.values(triNodes.value).map((n) => n.report).filter(Boolean)
  const approve = reports.filter((r) => r.opinion === true).length
  const deny = reports.filter((r) => r.opinion === false).length
  const verdict = approve > deny ? 'APPROVED' : 'DENIED'
  resolutionPayload.value = {
    status: 'completed',
    architect: { requires_clarification: false, questions: [], resolution_draft: null },
    reports,
    synthesis: {
      verdict,
      vote_ratio: `${approve}:${deny}`,
      consensus_summary: locale.value === 'en'
        ? 'Offline debug mode: result is for frontend visual verification only.'
        : locale.value === 'ja'
          ? 'オフラインデバッグモード：この結果はフロント表示確認専用です。'
          : '離線調試模式，結果僅供前端視覺驗證。',
      disagreement_summary: locale.value === 'en'
        ? 'Offline debug mode does not use real models.'
        : locale.value === 'ja'
          ? 'オフラインデバッグモードでは実モデルを使用しません。'
          : '離線調試模式未接入真實模型。',
      ruling_explanation: locale.value === 'en'
        ? 'Offline debug mode: this result is generated by frontend simulation.'
        : locale.value === 'ja'
          ? 'オフラインデバッグモード：この結果はフロント側シミュレーションです。'
          : '離線調試模式：該結果由前端模擬生成。',
      degraded_mode: false
    }
  }
  triFinalVerdict.value = verdict
  streamActive.value = false
  await revealNodesCeremonially()
}

function abortStream() {
  abortController.value?.abort()
  streamActive.value = false
}

function onAbortStream() {
  abortStream()
  streamError.value = null
  triFinalVerdict.value = null
  triReportReady.value = false
  minimalDraftConfirmPending.value = false
  uiState.value = 'STANDBY'
}

function onViewReport() {
  if (!triReportReady.value || !resolutionPayload.value) return
  uiState.value = 'RESOLUTION'
}

async function onValidateStart(payload) {
  const nextTokens = payload?.tokens || {}
  const nextModels = payload?.models || {}
  const nextDebugMode = !!payload?.debugMode
  debugMode.value = nextDebugMode
  selectedModels.value = { ...selectedModels.value, ...nextModels }

  if (nextDebugMode) {
    streamActive.value = false
    abortController.value = null
    tokens.value = { ...nextTokens }
    accumulatedInput.value = ''
    architectMessage.value = ''
    resolutionPayload.value = null
    streamError.value = null
    triFinalVerdict.value = null
    triReportReady.value = false
    minimalDraftConfirmPending.value = false
    processTrace.value = []
    resetTriNodes()
    triStartAtMs.value = Date.now()
    uiState.value = 'ARCHITECT_ANALYSIS'
    return
  }

  preflightBusy.value = true
  preflightError.value = null
  preflightChecks.value = []

  try {
    const result = await preflightMagi(nextTokens, nextModels, locale.value)
    preflightChecks.value = result.checks || []
    if (!result.ok) {
      preflightError.value = t('preflightError')
      return
    }
    tokens.value = { ...nextTokens }
    streamActive.value = false
    abortController.value = null
    accumulatedInput.value = ''
    architectMessage.value = ''
    resolutionPayload.value = null
    streamError.value = null
    triFinalVerdict.value = null
    triReportReady.value = false
    minimalDraftConfirmPending.value = false
    processTrace.value = []
    resetTriNodes()
    uiState.value = 'ARCHITECT_ANALYSIS'
  } catch (e) {
    preflightError.value = e.message || String(e)
  } finally {
    preflightBusy.value = false
  }
}

const currentView = computed(() => {
  const views = {
    STANDBY: StandbyView,
    ARCHITECT_ANALYSIS: ArchitectAnalysisView,
    TRI_CORE_PROCESSING: TriCoreProcessingView,
    RESOLUTION: ResolutionView
  }
  return views[uiState.value] || StandbyView
})

const viewProps = computed(() => {
  switch (uiState.value) {
    case 'ARCHITECT_ANALYSIS':
      return {
        architectMessage: architectMessage.value,
        busy: streamActive.value,
        error: streamError.value,
        locale: locale.value,
        i18n: I18N,
        confirmationPending: minimalDraftConfirmPending.value
      }
    case 'TRI_CORE_PROCESSING':
      return {
        triNodes: triNodes.value,
        streamActive: streamActive.value,
        finalVerdict: triFinalVerdict.value,
        canOpenReport: triReportReady.value,
        nodeReveal: nodeReveal.value,
        locale: locale.value,
        i18n: I18N
      }
    case 'RESOLUTION':
      return {
        resolution: resolutionPayload.value,
        locale: locale.value,
        i18n: I18N,
        processTrace: processTrace.value
      }
    default:
      return {
        validating: preflightBusy.value,
        validationError: preflightError.value,
        preflightChecks: preflightChecks.value,
        locale: locale.value,
        i18n: I18N
      }
  }
})

function handleTransition(payload) {
  if (typeof payload === 'string') {
    if (payload === 'STANDBY') {
      abortStream()
      streamError.value = null
      triFinalVerdict.value = null
      triReportReady.value = false
      minimalDraftConfirmPending.value = false
    }
    if (payload === 'ARCHITECT_ANALYSIS') {
      abortStream()
      accumulatedInput.value = ''
      architectMessage.value = ''
      resolutionPayload.value = null
      streamError.value = null
      triFinalVerdict.value = null
      triReportReady.value = false
      minimalDraftConfirmPending.value = false
      processTrace.value = []
      resetTriNodes()
    }
    uiState.value = payload
    return
  }

  if (payload?.tokens) tokens.value = { ...payload.tokens }
  if (payload?.state) {
    uiState.value = payload.state
  }
}
</script>

<style scoped>
.app-container {
  width: 100%;
  height: 100%;
  background: #000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.lang-switcher {
  position: absolute;
  top: 12px;
  right: 18px;
  z-index: 400;
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  max-width: min(96vw, 420px);
  padding: 6px 10px;
  border: 1px solid rgba(230, 126, 34, 0.7);
  background: rgba(0, 0, 0, 0.9);
}

.lang-label {
  color: #e67e22;
  font-size: 11px;
  letter-spacing: 0.5px;
}

.lang-select {
  border: 1px solid #e67e22;
  background: #070707;
  color: #e67e22;
  padding: 4px 8px;
  font-size: 11px;
  outline: none;
}

.lang-guide-btn {
  border: 1px solid rgba(230, 126, 34, 0.65);
  background: #070707;
  color: #e67e22;
  padding: 4px 10px;
  font-size: 11px;
  letter-spacing: 0.04em;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
}

.lang-guide-btn:hover {
  background: rgba(230, 126, 34, 0.12);
}
</style>
