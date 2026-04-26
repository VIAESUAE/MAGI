<template>
  <div class="architect-layout">
    <div class="outer-frame">
      <div class="inner-frame">
        
        <div class="header-area">
          <div class="architect-title">ARCHITECT ANALYSIS</div>
        </div>

        <div class="chat-area">
          <div class="message assistant">
            <span class="typewriter">{{ typedMessage }}</span>
          </div>
          <div v-if="busy" class="message assistant loading">
            <span class="dot">●</span><span class="dot">●</span><span class="dot">●</span>
          </div>
        </div>

        <div v-if="error" class="error-banner">{{ error }}</div>

        <div v-if="confirmationPending && !busy" class="confirm-section">
          <div class="confirm-tip">{{ confirmPrompt }}</div>
          <div class="confirm-actions">
            <button class="submit-btn" @click="confirmMinimalDraft">{{ tt('confirm') }}</button>
            <button class="back-btn" @click="cancelMinimalDraft">{{ tt('cancel') }}</button>
          </div>
        </div>

        <div v-else-if="!busy" class="input-section">
          <input 
            v-model="userInput" 
            type="text" 
            :placeholder="tt('architectInputPlaceholder')"
            @keyup.enter="submitArchitectAnalysis"
            class="architect-input"
          >
          <button @click="submitArchitectAnalysis" class="submit-btn" :disabled="!userInput.trim()">
            {{ tt('confirm') }}
          </button>
        </div>

        <div v-else class="progress-indicator">
          <span class="spinner">⟳</span> {{ tt('processing') }}
        </div>

        <div class="footer-area">
          <button class="back-btn" @click="goBack">← {{ tt('back') }}</button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  architectMessage: { type: String, default: '' },
  busy: { type: Boolean, default: false },
  error: { type: String, default: null },
  locale: { type: String, default: 'zh' },
  i18n: { type: Object, required: true },
  confirmationPending: { type: Boolean, default: false }
})

const emit = defineEmits(['transition', 'architect-submit'])

const typedMessage = ref('')
const userInput = ref('')
const confirmPrompt = computed(() => props.architectMessage?.trim() || tt('minimalDraftConfirmTitle'))

function buildPromptText() {
  if (props.architectMessage?.trim()) {
    return props.architectMessage
  }
  return tt('architectDefaultMessage')
}

function tt(key) {
  return props.i18n?.[props.locale]?.[key] ?? props.i18n?.zh?.[key] ?? key
}

async function typeMessage(text) {
  typedMessage.value = ''
  for (let i = 0; i < text.length; i++) {
    typedMessage.value += text[i]
    await new Promise((r) => setTimeout(r, 35))
  }
}

watch(
  () => [props.architectMessage, props.busy],
  () => {
    if (props.busy) {
      typedMessage.value = buildPromptText()
      return
    }
    typeMessage(buildPromptText())
  },
  { immediate: true, deep: true }
)

const submitArchitectAnalysis = async () => {
  if (!userInput.value.trim() || props.busy) return
  emit('architect-submit', { action: 'submit', text: userInput.value })
  userInput.value = ''
}

const confirmMinimalDraft = () => {
  emit('architect-submit', { action: 'confirm-minimal-draft' })
}

const cancelMinimalDraft = () => {
  emit('architect-submit', { action: 'cancel-minimal-draft' })
}

const goBack = () => {
  emit('transition', 'STANDBY')
}
</script>

<style scoped>
.architect-layout {
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

.architect-title {
  color: #e67e22;
  font-size: clamp(18px, 3vw, 28px);
  font-weight: bold;
  letter-spacing: clamp(1px, 0.3vw, 3px);
  text-align: center;
  text-shadow: 0 0 10px rgba(230, 126, 34, 0.3);
}

.chat-area {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: clamp(8px, 1%, 15px);
  padding: clamp(8px, 1%, 15px) 0;
}

.message {
  padding: clamp(8px, 1.5%, 15px);
  border-left: clamp(2px, 0.3vw, 4px) solid #00ff00;
  color: #00ff00;
  font-size: clamp(12px, 1.5vw, 16px);
  line-height: 1.6;
  word-wrap: break-word;
  background: rgba(0, 255, 0, 0.03);
}

.typewriter {
  display: inline-block;
}

.loading {
  justify-content: flex-start;
  align-items: center;
}

.dot {
  display: inline-block;
  animation: blink 1.4s infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0%,
  100% {
    opacity: 0.2;
  }
  50% {
    opacity: 1;
  }
}

.error-banner {
  color: #ff3333;
  border: 1px solid rgba(255, 51, 51, 0.5);
  padding: clamp(8px, 1.2%, 12px);
  font-size: clamp(11px, 1.3vw, 14px);
  line-height: 1.5;
}

.input-section {
  display: flex;
  gap: clamp(10px, 2%, 15px);
  flex-wrap: wrap;
  align-items: center;
}

.confirm-section {
  border: 1px solid rgba(230, 126, 34, 0.45);
  background: rgba(230, 126, 34, 0.05);
  padding: clamp(10px, 1.5%, 15px);
}

.confirm-tip {
  color: #e67e22;
  font-size: clamp(12px, 1.4vw, 15px);
  line-height: 1.6;
}

.confirm-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

.architect-input {
  flex: 1 1 220px;
  padding: clamp(8px, 1.5%, 15px);
  background: rgba(0, 255, 0, 0.05);
  border: clamp(1px, 0.2vw, 2px) solid #00ff00;
  color: #00ff00;
  font-family: 'MatissePro', monospace;
  font-size: clamp(12px, 1.5vw, 16px);
}

.architect-input:focus {
  outline: none;
  box-shadow: inset 0 0 10px rgba(0, 255, 0, 0.2);
}

.submit-btn {
  padding: clamp(8px, 1.5%, 15px) clamp(15px, 2%, 25px);
  border: clamp(1px, 0.3vw, 2px) solid #e67e22;
  background: rgba(230, 126, 34, 0.1);
  color: #e67e22;
  cursor: pointer;
  font-weight: bold;
  letter-spacing: clamp(1px, 0.3vw, 2px);
}

.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.progress-indicator {
  color: #e67e22;
  font-size: clamp(12px, 1.5vw, 16px);
  letter-spacing: clamp(0.5px, 0.2vw, 1px);
}

.spinner {
  display: inline-block;
  margin-right: 8px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.footer-area {
  flex: 0 0 auto;
  border-top: clamp(1px, 0.2vw, 2px) solid rgba(230, 126, 34, 0.3);
  padding-top: clamp(10px, 1.5%, 15px);
}

.back-btn {
  background: transparent;
  border: clamp(1px, 0.2vw, 2px) solid #e67e22;
  color: #e67e22;
  padding: clamp(8px, 1.5%, 15px) clamp(15px, 2%, 25px);
  cursor: pointer;
  font-weight: bold;
  letter-spacing: clamp(1px, 0.3vw, 2px);
}

.back-btn:hover {
  background: rgba(230, 126, 34, 0.15);
}
</style>
