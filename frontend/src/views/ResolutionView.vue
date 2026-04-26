<template>
  <div class="resolution-layout">
    <div class="outer-frame">
      <div class="inner-frame">
        
        <div class="header-area">
          <div class="resolution-title">{{ tt('finalResolution') }}</div>
        </div>

        <div class="content-area">
          <!-- 最终信号 -->
          <div
            class="signal-box"
            :class="{ approved: verdict === 'APPROVED', denied: verdict === 'DENIED', unknown: verdict !== 'APPROVED' && verdict !== 'DENIED' }"
          >
            <div class="signal-icon">
              {{ verdict === 'APPROVED' ? '✓' : '✗' }}
            </div>
            <div class="signal-text">
              {{ verdictLabel }}
            </div>
          </div>

          <!-- 共识分析 -->
          <div class="consensus-section">
            <div class="section-title">{{ tt('consensusAnalysis') }}</div>
            <div class="consensus-result">
              <div class="consensus-line">Melchior-1: {{ consensus.melchior }}</div>
              <div class="consensus-line">Balthasar-2: {{ consensus.balthasar }}</div>
              <div class="consensus-line">Casper-3: {{ consensus.casper }}</div>
            </div>
            <div class="consensus-ratio">
              {{ tt('vote') }}: {{ voteRatio }}
            </div>
          </div>

          <div class="diagnostics-section">
            <div class="section-title">{{ tt('nodeDiagnostics') }}</div>
            <div v-if="nodeDiagnostics.length" class="diagnostic-list">
              <div v-for="item in nodeDiagnostics" :key="item.node" class="diagnostic-item">
                <div class="diagnostic-head">
                  <span class="diagnostic-node">{{ item.node }}</span>
                  <span class="diagnostic-status" :class="item.statusClass">{{ item.status }}</span>
                </div>
                <div class="diagnostic-summary">{{ item.summary }}</div>
              </div>
            </div>
            <div v-else class="diagnostic-empty">{{ tt('noNodeReport') }}</div>
          </div>

          <!-- 裁决说明 -->
          <div class="ruling-section">
            <div class="section-title">{{ tt('rulingExplanation') }}</div>
            <div class="ruling-text">
              {{ rulingExplanation }}
            </div>
          </div>
        </div>

        <div class="button-group">
          <button class="again-btn" @click="showReview = true">{{ tt('reviewWorkflow') }}</button>
          <button class="again-btn" @click="goAgain">{{ tt('again') }}</button>
          <button class="exit-btn" @click="exit">{{ tt('exit') }}</button>
        </div>

      </div>
    </div>

    <div v-if="showReview" class="review-mask" @click.self="showReview = false">
      <div class="review-panel">
        <div class="review-head">
          <div class="section-title">{{ tt('workflowReview') }}</div>
          <button class="exit-btn tiny" @click="showReview = false">{{ tt('close') }}</button>
        </div>

        <div class="review-block">
          <div class="review-label">{{ tt('draftSnapshot') }}</div>
          <div class="review-text">{{ draftSnapshot }}</div>
        </div>

        <div class="review-block">
          <div class="review-label">{{ tt('finalSummary') }}</div>
          <div class="review-text">{{ rulingExplanation }}</div>
        </div>

        <div class="review-block">
          <div class="review-label">{{ tt('timeline') }}</div>
          <div class="trace-list">
            <div v-for="step in normalizedTrace" :key="step.id" class="trace-item" :class="step.level">
              <div class="trace-title">{{ step.title }}</div>
              <div class="trace-detail">{{ step.detail || '—' }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  resolution: {
    type: Object,
    default: null
  },
  locale: { type: String, default: 'zh' },
  i18n: { type: Object, required: true },
  processTrace: { type: Array, default: () => [] }
})

const emit = defineEmits(['transition'])
const showReview = ref(false)

function tt(key) {
  return props.i18n?.[props.locale]?.[key] ?? props.i18n?.zh?.[key] ?? key
}

const synthesis = computed(() => props.resolution?.synthesis ?? null)
const reports = computed(() => props.resolution?.reports ?? [])

const verdict = computed(() => synthesis.value?.verdict ?? null)

const verdictLabel = computed(() => {
  const v = verdict.value
  if (v === 'APPROVED') return tt('statusApprove')
  if (v === 'DENIED') return tt('statusDeny')
  return tt('unknown')
})

function formatNodeLine(report) {
  if (!report) return '—'
  if (report.status && report.status !== 'OK') return report.status
  if (report.opinion === true) return tt('agree')
  if (report.opinion === false) return tt('disagree')
  return tt('unknown')
}

const consensus = computed(() => {
  const out = {
    melchior: '—',
    balthasar: '—',
    casper: '—'
  }
  for (const r of reports.value) {
    if (r.node === 'Melchior-1') out.melchior = formatNodeLine(r)
    if (r.node === 'Balthasar-2') out.balthasar = formatNodeLine(r)
    if (r.node === 'Casper-3') out.casper = formatNodeLine(r)
  }
  return out
})

const voteRatio = computed(() => synthesis.value?.vote_ratio ?? '—')

const rulingExplanation = computed(() => synthesis.value?.ruling_explanation ?? '—')
const normalizedTrace = computed(() => props.processTrace || [])
const draftSnapshot = computed(() => {
  const draft = props.resolution?.architect?.resolution_draft
  if (!draft) return tt('noDraftSnapshot')
  const constraints = (draft.constraints || []).join(' / ')
  return `background=${draft.background} | core_request=${draft.core_request} | constraints=${constraints || '—'}`
})

const nodeDiagnostics = computed(() => {
  const order = ['Melchior-1', 'Balthasar-2', 'Casper-3']
  const rows = reports.value.map((r) => ({
    node: r.node,
    status: r.status ?? 'UNKNOWN',
    summary: r.summary ?? 'No summary available.',
    statusClass: r.status === 'OK' ? 'ok' : 'error'
  }))
  return rows.sort((a, b) => order.indexOf(a.node) - order.indexOf(b.node))
})

const goAgain = () => {
  emit('transition', 'ARCHITECT_ANALYSIS')
}

const exit = () => {
  emit('transition', 'STANDBY')
}
</script>

<style scoped>
.resolution-layout {
  width: 100%;
  height: 100vh;
  background-color: #000000;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: clamp(10px, 3%, 30px);
  font-family: 'MatissePro', sans-serif;
  overflow: hidden;
}

.outer-frame {
  border: clamp(1px, 0.3vw, 3px) solid #e67e22;
  padding: clamp(4px, 0.8vw, 12px);
  width: 100%;
  height: 100%;
  display: flex;
  box-shadow: inset 0 0 0 clamp(1px, 0.3vw, 3px) #e67e22;
  max-width: 1200px;
}

.inner-frame {
  border: clamp(1px, 0.3vw, 3px) solid #e67e22;
  width: 100%;
  height: 100%;
  padding: clamp(20px, 3%, 40px);
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  gap: clamp(15px, 2%, 25px);
  overflow: hidden;
}

.header-area {
  flex: 0 0 auto;
  border-bottom: clamp(1px, 0.2vw, 2px) solid rgba(230, 126, 34, 0.3);
  padding-bottom: clamp(10px, 1.5%, 15px);
}

.resolution-title {
  color: #e67e22;
  font-size: clamp(18px, 3vw, 28px);
  font-weight: bold;
  letter-spacing: clamp(1px, 0.3vw, 3px);
  text-align: center;
  text-shadow: 0 0 10px rgba(230, 126, 34, 0.3);
}

.content-area {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: clamp(12px, 2%, 20px);
  padding: clamp(8px, 1%, 15px) 0;
}

.signal-box {
  padding: clamp(15px, 2%, 25px);
  border-radius: 0;
  text-align: center;
  border: clamp(1px, 0.2vw, 3px) solid #00ff00;
  background: rgba(0, 255, 0, 0.05);
  flex: 0 0 auto;
}

.signal-box.approved {
  border-color: #00ff00;
  background: rgba(0, 255, 0, 0.05);
}

.signal-box.denied {
  border-color: #ff3333;
  background: rgba(255, 51, 51, 0.05);
}

.signal-box.unknown {
  border-color: #e67e22;
  background: rgba(230, 126, 34, 0.05);
}

.signal-icon {
  font-size: clamp(32px, 8vw, 56px);
  font-weight: bold;
  margin-bottom: clamp(8px, 1%, 15px);
  animation: pulse-scale 1s infinite;
}

.signal-box.approved .signal-icon {
  color: #00ff00;
  text-shadow: 0 0 20px rgba(0, 255, 0, 0.6);
}

.signal-box.denied .signal-icon {
  color: #ff3333;
  text-shadow: 0 0 20px rgba(255, 51, 51, 0.6);
}

.signal-box.unknown .signal-icon {
  color: #e67e22;
  text-shadow: 0 0 20px rgba(230, 126, 34, 0.5);
}

@keyframes pulse-scale {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.signal-text {
  font-size: clamp(16px, 2.5vw, 24px);
  font-weight: bold;
  letter-spacing: clamp(1px, 0.3vw, 2px);
}

.signal-box.approved .signal-text {
  color: #00ff00;
}

.signal-box.denied .signal-text {
  color: #ff3333;
}

.signal-box.unknown .signal-text {
  color: #e67e22;
}

.consensus-section,
.ruling-section,
.diagnostics-section {
  border: clamp(1px, 0.2vw, 2px) solid rgba(230, 126, 34, 0.3);
  padding: clamp(12px, 1.5%, 20px);
  border-radius: 0;
  background: rgba(230, 126, 34, 0.02);
  flex: 0 1 auto;
}

.section-title {
  color: #e67e22;
  font-size: clamp(12px, 1.5vw, 16px);
  font-weight: bold;
  letter-spacing: clamp(1px, 0.3vw, 1.5px);
  margin-bottom: clamp(8px, 1%, 12px);
  text-transform: uppercase;
  border-bottom: clamp(1px, 0.2vw, 2px) solid rgba(230, 126, 34, 0.3);
  padding-bottom: clamp(6px, 1%, 10px);
}

.consensus-result {
  display: flex;
  flex-direction: column;
  gap: clamp(4px, 0.5%, 8px);
  margin-bottom: clamp(8px, 1%, 12px);
}

.consensus-line {
  color: #00ff00;
  font-size: clamp(11px, 1.3vw, 14px);
  line-height: 1.5;
  letter-spacing: clamp(0.3px, 0.1vw, 0.5px);
}

.consensus-ratio {
  color: #e67e22;
  font-size: clamp(12px, 1.5vw, 16px);
  font-weight: bold;
  text-align: center;
  padding: clamp(8px, 1%, 12px);
  border: clamp(1px, 0.2vw, 2px) solid rgba(230, 126, 34, 0.5);
  border-radius: 0;
  background: rgba(230, 126, 34, 0.05);
}

.ruling-text {
  color: #00ff00;
  font-size: clamp(12px, 1.3vw, 14px);
  line-height: 1.7;
  word-wrap: break-word;
  text-align: justify;
}

.diagnostic-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.diagnostic-item {
  border: 1px solid rgba(230, 126, 34, 0.25);
  background: rgba(0, 0, 0, 0.2);
  padding: 10px;
}

.diagnostic-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.diagnostic-node {
  color: #e67e22;
  font-size: clamp(11px, 1.2vw, 14px);
  letter-spacing: 0.5px;
}

.diagnostic-status {
  font-size: clamp(10px, 1.1vw, 13px);
  font-weight: bold;
}

.diagnostic-status.ok {
  color: #00ff00;
}

.diagnostic-status.error {
  color: #ff3333;
}

.diagnostic-summary {
  margin-top: 6px;
  color: #00ff00;
  font-size: clamp(11px, 1.2vw, 13px);
  line-height: 1.6;
  word-break: break-word;
}

.diagnostic-empty {
  color: rgba(230, 126, 34, 0.8);
  font-size: clamp(11px, 1.2vw, 13px);
}

.button-group {
  display: flex;
  gap: clamp(10px, 1.5%, 15px);
  padding-top: clamp(10px, 1.5%, 15px);
  border-top: clamp(1px, 0.2vw, 2px) solid rgba(230, 126, 34, 0.3);
  flex: 0 0 auto;
  flex-wrap: wrap;
}

.again-btn,
.exit-btn {
  flex: 1 1 auto;
  min-width: clamp(100px, 30%, 200px);
  padding: clamp(10px, 1.5%, 15px);
  border: clamp(1px, 0.2vw, 2px) solid #e67e22;
  background: rgba(230, 126, 34, 0.05);
  color: #e67e22;
  cursor: pointer;
  border-radius: 0;
  transition: all 0.3s ease;
  font-weight: bold;
  letter-spacing: clamp(1px, 0.3vw, 1.5px);
  font-size: clamp(12px, 1.3vw, 14px);
}

.review-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.66);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 80;
}

.review-panel {
  width: min(960px, 92vw);
  max-height: 82vh;
  overflow-y: auto;
  overflow-x: hidden;
  border: 1px solid #e67e22;
  background: #070707;
  padding: 16px;
}

.review-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.exit-btn.tiny {
  flex: 0 0 auto;
  min-width: 90px;
  padding: 6px 10px;
}

.review-block {
  margin-top: 12px;
  border: 1px solid rgba(230, 126, 34, 0.35);
  padding: 10px;
}

.review-label {
  color: #e67e22;
  font-weight: bold;
  margin-bottom: 6px;
}

.review-text {
  color: #00ff00;
  font-size: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.trace-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.trace-item {
  border-left: 3px solid #e67e22;
  padding: 6px 8px;
  background: rgba(230, 126, 34, 0.03);
}

.trace-item.error {
  border-left-color: #ff3333;
}

.trace-title {
  color: #e67e22;
  font-size: 12px;
}

.trace-detail {
  margin-top: 4px;
  color: #00ff00;
  font-size: 11px;
  line-height: 1.5;
}

.again-btn:hover {
  background: rgba(230, 126, 34, 0.15);
  box-shadow: 0 0 12px rgba(230, 126, 34, 0.4);
}

.exit-btn {
  border-color: #ff3333;
  color: #ff3333;
  background: transparent;
}

.exit-btn:hover {
  background: rgba(255, 51, 51, 0.1);
  box-shadow: 0 0 12px rgba(255, 51, 51, 0.4);
}

@media (max-width: 768px) {
  .inner-frame {
    padding: clamp(15px, 2%, 20px);
    gap: clamp(10px, 1%, 15px);
  }

  .resolution-title {
    font-size: clamp(16px, 4vw, 22px);
  }

  .button-group {
    flex-direction: column;
  }

  .again-btn,
  .exit-btn {
    width: 100%;
  }
}
</style>
