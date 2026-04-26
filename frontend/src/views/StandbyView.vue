<template>
  <div class="standby-layout">
    <div class="outer-frame">
      <div class="inner-frame">
        
        <div class="welcome-section">
          <div class="title">{{ tt('standbyTitle') }}</div>
          <p class="subtitle">{{ tt('standbySubtitle') }}</p>
        </div>

        <div class="input-section">
          <div class="form-title">{{ tt('configApiCredentials') }}</div>
          <div class="mode-row">
            <label class="mode-label">
              <input v-model="debugMode" type="checkbox" class="mode-check">
              {{ tt('frontendDebugMode') }}
            </label>
            <button class="advanced-btn" @click="showAdvanced = true">{{ tt('advanced') }}</button>
          </div>

          <div class="form-group">
            <label>{{ tt('defaultApiKeyLabel') }}</label>
            <input
              v-model="defaultApiKey"
              type="password"
              :placeholder="tt('openrouterKeyPlaceholder')"
              class="input-field"
            >
          </div>

          <div class="form-group">
            <label>{{ tt('melchiorModel') }}</label>
            <select v-model="models.claude" class="input-field select-field">
              <option v-for="m in modelOptions" :key="`m-${m}`" :value="m">{{ m }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>{{ tt('balthasarModel') }}</label>
            <select v-model="models.grok" class="input-field select-field">
              <option v-for="m in modelOptions" :key="`g-${m}`" :value="m">{{ m }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>{{ tt('casperModel') }}</label>
            <select v-model="models.gemini" class="input-field select-field">
              <option v-for="m in modelOptions" :key="`c-${m}`" :value="m">{{ m }}</option>
            </select>
          </div>

          <div class="button-group">
            <button class="save-btn" @click="saveConfig">{{ tt('saveConfig') }}</button>
            <button class="save-btn" @click="loadModelsFromOpenRouter" :disabled="modelLoading || !openRouterProbeToken">
              {{ modelLoading ? tt('loadingModels') : tt('fetchOpenrouterModels') }}
            </button>
            <button class="start-btn" @click="startAnalysis" :disabled="validating">
              {{ validating ? tt('pingingModels') : (debugMode ? tt('startDebugFlow') : tt('startAnalysis')) }}
            </button>
          </div>
          <div v-if="modelError" class="validation-error">{{ modelError }}</div>

          <div v-if="validationError" class="validation-error">{{ validationError }}</div>
          <div v-if="preflightChecks.length" class="preflight-result">
            <div
              v-for="item in preflightChecks"
              :key="item.node"
              class="preflight-line"
              :class="{ ok: item.ok, bad: !item.ok }"
            >
              {{ item.node }} / {{ item.model }} / {{ item.ok ? tt('ok') : tt('fail') }} / {{ item.detail }}
            </div>
          </div>
        </div>

        <div class="footer-text">
          <p>{{ tt('standbyFooterTip') }}</p>
          <p class="disclaimer-wrap">
            <button type="button" class="disclaimer-link" @click="emit('open-disclaimer')">
              {{ tt('disclaimerFooterLink') }}
            </button>
          </p>
        </div>

      </div>
    </div>

    <div v-if="showAdvanced" class="modal-mask">
      <div class="modal-card">
        <div class="modal-title">{{ tt('advancedKeyRouting') }}</div>
        <div class="form-group">
          <label>{{ tt('melchiorApiOverride') }}</label>
          <input v-model="advancedTokens.claude" type="password" class="input-field" :placeholder="tt('leaveEmptyUseDefault')">
        </div>
        <div class="form-group">
          <label>{{ tt('balthasarApiOverride') }}</label>
          <input v-model="advancedTokens.grok" type="password" class="input-field" :placeholder="tt('leaveEmptyUseDefault')">
        </div>
        <div class="form-group">
          <label>{{ tt('casperApiOverride') }}</label>
          <input v-model="advancedTokens.gemini" type="password" class="input-field" :placeholder="tt('leaveEmptyUseDefault')">
        </div>
        <div class="button-group">
          <button class="save-btn" @click="showAdvanced = false">{{ tt('close') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { fetchOpenRouterModels } from '../api/magiApi.js'

const props = defineProps({
  validating: { type: Boolean, default: false },
  validationError: { type: String, default: null },
  preflightChecks: { type: Array, default: () => [] },
  locale: { type: String, default: 'zh' },
  i18n: { type: Object, required: true }
})

const emit = defineEmits(['transition', 'validate-start', 'open-disclaimer'])
const defaultApiKey = ref('')
const advancedTokens = ref({ claude: '', grok: '', gemini: '' })
const models = ref({
  claude: 'openrouter/openai/gpt-oss-20b:free',
  grok: 'openrouter/openai/gpt-oss-120b:free',
  gemini: 'openrouter/openai/gpt-oss-120b:free'
})
const debugMode = ref(false)
const modelOptions = ref([
  'openrouter/openai/gpt-oss-20b:free',
  'openrouter/openai/gpt-oss-120b:free',
  'openrouter/meta-llama/llama-3.1-8b-instruct:free'
])
const modelLoading = ref(false)
const modelError = ref(null)
const showAdvanced = ref(false)

function tt(key) {
  return props.i18n?.[props.locale]?.[key] ?? props.i18n?.zh?.[key] ?? key
}

const openRouterProbeToken = computed(() => advancedTokens.value.claude || defaultApiKey.value)

const saveConfig = () => {
  localStorage.setItem('magi_default_token', defaultApiKey.value)
  localStorage.setItem('magi_advanced_tokens', JSON.stringify(advancedTokens.value))
  localStorage.setItem('magi_models', JSON.stringify(models.value))
  localStorage.setItem('magi_debug_mode', JSON.stringify(debugMode.value))
  alert(tt('configSaved'))
}

const buildTokens = () => ({
  claude: advancedTokens.value.claude || defaultApiKey.value,
  grok: advancedTokens.value.grok || defaultApiKey.value,
  gemini: advancedTokens.value.gemini || defaultApiKey.value
})

const startAnalysis = () => {
  const tokens = buildTokens()
  if (!debugMode.value && (!tokens.claude || !tokens.grok || !tokens.gemini)) {
    alert(tt('missingApiKeyAlert'))
    return
  }
  emit('validate-start', {
    tokens,
    models: { ...models.value },
    debugMode: debugMode.value
  })
}

const loadModelsFromOpenRouter = async () => {
  if (!openRouterProbeToken.value) {
    modelError.value = tt('fillApiBeforeFetch')
    return
  }
  modelLoading.value = true
  modelError.value = null
  try {
    const ids = await fetchOpenRouterModels(openRouterProbeToken.value)
    if (!ids.length) {
      modelError.value = tt('emptyModelList')
      return
    }
    modelOptions.value = ids
    for (const key of ['claude', 'grok', 'gemini']) {
      if (!ids.includes(models.value[key])) {
        models.value[key] = ids[0]
      }
    }
  } catch (e) {
    modelError.value = e.message || String(e)
  } finally {
    modelLoading.value = false
  }
}

const loadTokens = () => {
  const savedDefault = localStorage.getItem('magi_default_token')
  if (savedDefault) defaultApiKey.value = savedDefault
  const savedAdv = localStorage.getItem('magi_advanced_tokens')
  if (savedAdv) advancedTokens.value = { ...advancedTokens.value, ...JSON.parse(savedAdv) }
  const savedModels = localStorage.getItem('magi_models')
  if (savedModels) models.value = { ...models.value, ...JSON.parse(savedModels) }
  const savedDebug = localStorage.getItem('magi_debug_mode')
  if (savedDebug) debugMode.value = JSON.parse(savedDebug)
}

onMounted(() => {
  loadTokens()
})
</script>

<style scoped>
.standby-layout {
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
  padding: clamp(30px, 5%, 50px);
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  gap: clamp(20px, 4%, 40px);
  justify-content: flex-start;
  overflow-y: auto;
}

.welcome-section {
  text-align: center;
  border-bottom: clamp(1px, 0.2vw, 3px) solid #e67e22;
  padding-bottom: clamp(15px, 3%, 30px);
  flex: 0 0 auto;
}

.title {
  font-size: clamp(28px, 4.5vw, 48px);
  color: #e67e22;
  letter-spacing: clamp(2px, 0.5vw, 6px);
  font-weight: bold;
  margin-bottom: clamp(5px, 1%, 15px);
}

.subtitle {
  color: #00ff00;
  font-size: clamp(12px, 2vw, 18px);
  letter-spacing: clamp(1px, 0.3vw, 2px);
  margin: 0;
}

.input-section {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
}

.form-title {
  color: #e67e22;
  font-size: clamp(14px, 2vw, 20px);
  letter-spacing: clamp(1px, 0.3vw, 2px);
  margin-bottom: clamp(12px, 2%, 20px);
  border-left: clamp(2px, 0.3vw, 4px) solid #27ae60;
  padding-left: clamp(8px, 1%, 15px);
}

.form-group {
  margin-bottom: clamp(12px, 2%, 20px);
}

.form-group label {
  display: block;
  color: #00ff00;
  font-size: clamp(11px, 1.5vw, 14px);
  letter-spacing: clamp(0.5px, 0.2vw, 1px);
  margin-bottom: clamp(5px, 1%, 10px);
  font-weight: bold;
}

.select-field {
  margin-top: 8px;
  appearance: none;
}

.mode-row {
  margin-bottom: clamp(10px, 1.5%, 16px);
}

.mode-label {
  color: #00ff00;
  font-size: clamp(11px, 1.4vw, 14px);
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-check {
  accent-color: #e67e22;
}

.advanced-btn {
  border: 1px solid #e67e22;
  color: #e67e22;
  background: rgba(230, 126, 34, 0.08);
  padding: 6px 10px;
  cursor: pointer;
  font-size: 12px;
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99;
}

.modal-card {
  width: min(90vw, 640px);
  border: 1px solid #e67e22;
  background: #080808;
  padding: 18px;
}

.modal-title {
  color: #e67e22;
  font-size: 18px;
  margin-bottom: 12px;
}

.input-field {
  width: 100%;
  padding: clamp(8px, 1.5%, 15px);
  background: rgba(0, 255, 0, 0.05);
  border: clamp(1px, 0.2vw, 2px) solid #00ff00;
  color: #00ff00;
  font-family: 'MatissePro', monospace;
  font-size: clamp(11px, 1.3vw, 14px);
  letter-spacing: clamp(0.5px, 0.2vw, 1px);
  border-radius: 0;
}

.input-field::placeholder {
  color: rgba(0, 255, 0, 0.3);
}

.input-field:focus {
  outline: none;
  box-shadow: inset 0 0 10px rgba(0, 255, 0, 0.2);
  border-color: #00ff00;
}

.button-group {
  display: flex;
  gap: clamp(10px, 2%, 20px);
  margin-top: clamp(20px, 3%, 30px);
  flex-wrap: wrap;
}

.save-btn,
.start-btn {
  flex: 1 1 auto;
  min-width: clamp(120px, 35%, 300px);
  padding: clamp(10px, 1.5%, 15px);
  border: clamp(1px, 0.3vw, 2px) solid #e67e22;
  background: rgba(230, 126, 34, 0.1);
  color: #e67e22;
  cursor: pointer;
  font-size: clamp(12px, 1.5vw, 16px);
  letter-spacing: clamp(1px, 0.3vw, 2px);
  font-weight: bold;
  transition: all 0.3s ease;
}

.save-btn:hover {
  background: rgba(230, 126, 34, 0.2);
  box-shadow: 0 0 15px rgba(230, 126, 34, 0.5);
}

.start-btn {
  border-color: #00ff00;
  color: #00ff00;
  background: rgba(0, 255, 0, 0.1);
}

.start-btn:hover {
  background: rgba(0, 255, 0, 0.2);
  box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
}

.start-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.validation-error {
  margin-top: 12px;
  color: #ff4d4d;
  border: 1px solid rgba(255, 77, 77, 0.5);
  padding: 8px 10px;
  font-size: clamp(11px, 1.2vw, 13px);
}

.preflight-result {
  margin-top: 12px;
  border: 1px solid rgba(230, 126, 34, 0.35);
  padding: 8px 10px;
  background: rgba(230, 126, 34, 0.04);
}

.preflight-line {
  font-size: clamp(10px, 1.1vw, 12px);
  line-height: 1.55;
  word-break: break-word;
}

.preflight-line.ok {
  color: #00ff00;
}

.preflight-line.bad {
  color: #ff6666;
}

.footer-text {
  text-align: center;
  color: rgba(230, 126, 34, 0.7);
  font-size: clamp(10px, 1.2vw, 13px);
  letter-spacing: clamp(0.3px, 0.1vw, 0.8px);
  border-top: clamp(1px, 0.2vw, 2px) solid rgba(230, 126, 34, 0.3);
  padding-top: clamp(12px, 2%, 20px);
  margin-top: auto;
  flex: 0 0 auto;
}

.footer-text p {
  margin: 0;
  line-height: 1.6;
}

.disclaimer-wrap {
  margin-top: clamp(8px, 1.2vw, 14px);
}

.disclaimer-link {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: rgba(0, 255, 0, 0.75);
  font-size: inherit;
  font-family: inherit;
  letter-spacing: inherit;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.disclaimer-link:hover {
  color: #00ff00;
}

.footer-text code {
  color: rgba(0, 255, 0, 0.85);
  font-size: 0.95em;
}

@media (max-width: 768px) {
  .inner-frame {
    padding: clamp(15px, 3%, 25px);
    gap: clamp(15px, 2%, 20px);
  }

  .title {
    font-size: clamp(24px, 5vw, 36px);
  }

  .button-group {
    flex-direction: column;
  }

  .save-btn,
  .start-btn {
    width: 100%;
  }
}
</style>
