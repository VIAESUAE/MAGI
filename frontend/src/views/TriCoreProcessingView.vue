<template>
  <div class="tri-page">
    <div class="magi-frame">
      <div class="header">
        <div class="title-group">
          <div class="decoration-lines" />
          <div class="title-text">{{ tt('triTitleLeft') }}</div>
          <div class="decoration-lines" />
        </div>
        <div class="title-group">
          <div class="decoration-lines" />
          <div class="title-text">{{ tt('triTitleRight') }}</div>
          <div class="decoration-lines" />
        </div>
      </div>

      <div class="diag-text diag-text-left">
        <div>CODE: 258</div>
        <div>FILE:</div>
        <div>MAGI.SYS</div>
        <div>EXTENTION:</div>
        <div>4096</div>
        <div>EX_MODE:</div>
        <div>OFF</div>
        <div>PRIORITY:</div>
        <div>DEFAULT</div>
      </div>

      <div class="diag-text diag-text-right">
        <div>Layer 3:</div>
        <div>Connection control:</div>
        <div>Q.931</div>
        <div>Layer 2:</div>
        <div>Data Link:</div>
        <div>Q.921 - LAPD</div>
        <div>Layer 1:</div>
        <div>Phisical Connection:</div>
        <div>L431 - Basic Interface</div>
      </div>

      <div class="status-box" :class="{ breathing: streamActive && !finalVerdict }">
        {{ statusText }}
      </div>

      <div class="core-container">
        <svg class="magi-connector" viewBox="0 0 920 420" preserveAspectRatio="none">
          <line class="connector-line" x1="400" y1="220" x2="360" y2="280" />
          <line class="connector-line" x1="520" y1="220" x2="560" y2="280" />
          <line class="connector-line" x1="520" y1="340" x2="400" y2="340" />
        </svg>

        <div class="node-wrapper balthasar" :class="nodeClass('balthasar')">
          <div class="node-content" style="clip-path: inherit;">
            <div class="label">BALTHASAR-2</div>
            <div class="name">{{ nodeStatus('balthasar') }}</div>
          </div>
        </div>

        <div class="central-hub">MAGI</div>

        <div class="node-wrapper casper" :class="nodeClass('casper')">
          <div class="node-content" style="clip-path: inherit;">
            <div class="label">CASPER-3</div>
            <div class="name">{{ nodeStatus('casper') }}</div>
          </div>
        </div>

        <div class="node-wrapper melchior" :class="nodeClass('melchior')">
          <div class="node-content" style="clip-path: inherit;">
            <div class="label">MELCHIOR-1</div>
            <div class="name">{{ nodeStatus('melchior') }}</div>
          </div>
        </div>
      </div>

      <div class="control-row">
        <div class="meta-text">LIVE SSE: {{ streamActive ? 'ON' : 'OFF' }}</div>
        <div class="actions">
          <button v-if="canOpenReport" class="btn report" @click="viewReport">{{ tt('report') }}</button>
          <button class="btn abort" @click="abort">{{ tt('abort') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  triNodes: {
    type: Object,
    required: true
  },
  streamActive: {
    type: Boolean,
    default: false
  },
  finalVerdict: {
    type: String,
    default: null
  },
  canOpenReport: {
    type: Boolean,
    default: false
  },
  nodeReveal: {
    type: Object,
    default: () => ({ melchior: false, balthasar: false, casper: false })
  },
  locale: { type: String, default: 'zh' },
  i18n: { type: Object, required: true }
})

const emit = defineEmits(['abort-stream', 'view-report'])

function tt(key) {
  return props.i18n?.[props.locale]?.[key] ?? props.i18n?.zh?.[key] ?? key
}

const statusText = computed(() => {
  if (props.finalVerdict === 'APPROVED') return tt('statusApprove')
  if (props.finalVerdict === 'DENIED') return tt('statusDeny')
  return props.streamActive ? tt('statusPending') : tt('statusStandby')
})

function nodeStatus(key) {
  return props.triNodes?.[key]?.status ?? '—'
}

function nodeVisualState(key) {
  const report = props.triNodes?.[key]?.report
  const revealed = !!props.nodeReveal?.[key]
  if (!revealed) return props.streamActive && !props.finalVerdict ? 'processing' : 'idle'
  if (!report || report.status !== 'OK') return 'neutral'
  if (report.opinion === true) return 'approved'
  if (report.opinion === false) return 'denied'
  return 'neutral'
}

function nodeClass(key) {
  return `is-${nodeVisualState(key)}`
}

function abort() {
  emit('abort-stream')
}

function viewReport() {
  emit('view-report')
}
</script>

<style scoped>
.tri-page {
  --magi-orange: #fb6000;
  --magi-teal: #00ffd5;
  --magi-bg: #000000;
  --approved: #2d9bff;
  --denied: #d63232;
  --neutral: #b4732b;

  width: 100%;
  min-height: 100vh;
  background-color: var(--magi-bg);
  color: var(--magi-orange);
  font-family: "Microsoft YaHei", sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px;
  box-sizing: border-box;
}

.magi-frame {
  --right-info-top: 256px;
  border: 4px double var(--magi-orange);
  padding: 37.5px;
  position: relative;
  box-sizing: border-box;
  width: min(1440px, 96vw);
  aspect-ratio: 915 / 510;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
}

.title-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 26px;
}

.title-text {
  font-size: clamp(72px, 9.8vw, 136px);
  font-weight: 900;
  letter-spacing: 0;
  padding: 0;
  line-height: 1;
}

.decoration-lines {
  width: clamp(220px, 40vw, 420px);
  height: 10px;
  border-top: 3px solid var(--magi-teal);
  border-bottom: 3px solid var(--magi-teal);
}

.status-box {
  position: absolute;
  right: 280px;
  top: var(--right-info-top);
  border: 2px solid var(--magi-orange);
  padding: 5px 15px;
  font-size: clamp(16px, 2.8vw, 28px);
  letter-spacing: 2px;
  z-index: 5;
  min-width: 120px;
  text-align: center;
  transform: none;
}

.status-box.breathing {
  animation: blinker 2.2s ease-in-out infinite;
}

@keyframes blinker {
  50% {
    opacity: 0.2;
  }
}

.core-container {
  position: absolute;
  top: 20px;
  left: 20px;
  right: 20px;
  bottom: 20px;
}

.magi-connector {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.connector-line {
  stroke: var(--magi-orange);
  stroke-width: 12;
  fill: none;
}

.node-wrapper {
  background: var(--magi-orange);
  padding: 4px;
  position: absolute;
  z-index: 2;
}

.node-content {
  background: var(--magi-bg);
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  transition: background 0.35s ease, color 0.35s ease, filter 0.35s ease;
}

.balthasar {
  width: 315px;
  height: 390px;
  top: 37.5px;
  left: 50%;
  transform: translateX(-50%);
  clip-path: polygon(0 0, 100% 0, 100% 81%, 67% 100%, 33% 100%, 0 81%);
}

.casper {
  width: 480px;
  height: 270px;
  bottom: 52.5px;
  left: 135px;
  clip-path: polygon(61% 0, 100% 40%, 100% 100%, 0 100%, 0 0);
}

.melchior {
  width: 480px;
  height: 270px;
  bottom: 52.5px;
  right: 135px;
  clip-path: polygon(39% 0, 100% 0, 100% 100%, 0 100%, 0 40%);
}

.central-hub {
  position: absolute;
  top: 65%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 36px;
  font-weight: bold;
  z-index: 3;
}

.diag-text {
  position: absolute;
  color: var(--magi-orange);
  text-transform: uppercase;
  letter-spacing: 1.2px;
  line-height: 1.18;
  z-index: 3;
  pointer-events: none;
}

.diag-text-left {
  left: 52px;
  top: 178px;
  max-width: 170px;
  font-size: clamp(11px, 0.95vw, 15px);
  transform: translateY(70%);
}

.diag-text-right {
  right: 52px;
  top: var(--right-info-top);
  max-width: 230px;
  text-align: left;
  font-size: clamp(10px, 0.85vw, 13px);
  transform: none;
}

.label {
  font-size: clamp(16px, 2.2vw, 28px);
  margin-bottom: 5px;
}

.name {
  font-size: clamp(14px, 1.8vw, 20px);
  font-weight: bold;
  letter-spacing: 1px;
}

.node-wrapper.is-idle .node-content {
  background: var(--magi-bg);
  color: var(--magi-orange);
}

.node-wrapper.is-processing .node-content {
  background: rgba(251, 96, 0, 0.9);
  color: #1f0800;
  animation: nodePulse 1.8s ease-in-out infinite;
}

.node-wrapper.is-approved .node-content {
  background: var(--approved);
  color: #051a2d;
}

.node-wrapper.is-denied .node-content {
  background: var(--denied);
  color: #2b0505;
}

.node-wrapper.is-neutral .node-content {
  background: var(--neutral);
  color: #1b0d00;
}

@keyframes nodePulse {
  0%,
  100% {
    filter: brightness(0.82);
  }
  50% {
    filter: brightness(1.1);
  }
}

.control-row {
  position: absolute;
  left: 20px;
  right: 20px;
  bottom: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 4;
}

.meta-text {
  font-size: 12px;
  letter-spacing: 1px;
}

.actions {
  display: flex;
  gap: 8px;
}

.btn {
  border: 2px solid var(--magi-orange);
  background: var(--magi-bg);
  color: var(--magi-orange);
  padding: 6px 14px;
  font-size: 12px;
  letter-spacing: 1px;
  cursor: pointer;
}

.btn.report {
  border-color: var(--approved);
  color: var(--approved);
}

.btn.abort {
  border-color: #cf3a2f;
  color: #cf3a2f;
}

@media (max-width: 1000px) {
  .title-text {
    font-size: clamp(48px, 8vw, 104px);
  }

  .decoration-lines {
    width: clamp(160px, 30vw, 300px);
  }

  .diag-text-left,
  .diag-text-right {
    display: none;
  }

  .status-box {
    right: 64px;
    top: 196px;
    min-width: 98px;
  }

  .casper,
  .melchior {
    width: 280px;
    height: 160px;
  }

  .casper {
    left: 35px;
  }

  .melchior {
    right: 35px;
  }
}

@media (max-width: 768px) {
  .magi-frame {
    aspect-ratio: auto;
    min-height: 86vh;
  }

  .header {
    margin-bottom: 20px;
  }

  .status-box {
    right: 18px;
    top: 142px;
    min-width: 88px;
  }

  .central-hub {
    font-size: 28px;
  }

  .balthasar {
    width: 44%;
    height: 42%;
    top: 18%;
  }

  .casper,
  .melchior {
    width: 40%;
    height: 30%;
    bottom: 16%;
  }

  .casper {
    left: 4%;
  }

  .melchior {
    right: 4%;
  }

  .control-row {
    bottom: 8px;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
