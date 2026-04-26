<template>
  <Teleport to="body">
    <div class="doc-modal-mask" @click.self="onClose">
      <div
        class="doc-modal-card"
        role="dialog"
        :aria-labelledby="titleId"
        tabindex="-1"
        @click.stop
      >
        <h2 :id="titleId" class="doc-modal-title">{{ title }}</h2>
        <div class="doc-modal-body">{{ body }}</div>
        <div class="doc-modal-actions">
          <button type="button" class="doc-modal-btn" @click="onClose">
            {{ closeLabel }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

defineProps({
  title: { type: String, default: '' },
  body: { type: String, default: '' },
  closeLabel: { type: String, default: 'Close' }
})

const emit = defineEmits(['close'])

const titleId = `doc-modal-title-${Math.random().toString(16).slice(2, 10)}`

function onClose() {
  emit('close')
}

let prevBodyOverflow = ''

function onKey(e) {
  if (e.key === 'Escape') {
    e.preventDefault()
    onClose()
  }
}

onMounted(() => {
  prevBodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  document.body.style.overflow = prevBodyOverflow
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.doc-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 16px;
  background: rgba(0, 0, 0, 0.75);
  box-sizing: border-box;
}

.doc-modal-card {
  max-width: 560px;
  max-height: min(84vh, 640px);
  width: 100%;
  display: flex;
  flex-direction: column;
  border: 2px solid #e67e22;
  background: #070707;
  box-shadow: inset 0 0 0 1px rgba(230, 126, 34, 0.35);
  font-family: 'JetBrains Mono', 'Consolas', ui-monospace, 'MatissePro', sans-serif;
}

.doc-modal-title {
  margin: 0;
  padding: 16px 18px 10px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: #e67e22;
  border-bottom: 1px solid rgba(230, 126, 34, 0.45);
  flex-shrink: 0;
}

.doc-modal-body {
  padding: 14px 18px 16px;
  overflow-y: auto;
  color: rgba(220, 220, 220, 0.92);
  font-size: 12px;
  line-height: 1.65;
  letter-spacing: 0.04em;
  white-space: pre-line;
  word-break: break-word;
  flex: 1 1 auto;
  min-height: 0;
}

.doc-modal-actions {
  flex-shrink: 0;
  padding: 0 18px 16px;
  display: flex;
  justify-content: flex-end;
}

.doc-modal-btn {
  border: 1px solid #e67e22;
  background: rgba(0, 0, 0, 0.6);
  color: #e67e22;
  padding: 8px 20px;
  font-size: 12px;
  letter-spacing: 0.1em;
  cursor: pointer;
  font-family: inherit;
}

.doc-modal-btn:hover {
  background: rgba(230, 126, 34, 0.15);
}
</style>
