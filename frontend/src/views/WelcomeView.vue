<template>
  <div
    class="welcome-root"
    role="button"
    tabindex="0"
    :aria-label="hint"
    @click="dismiss"
    @touchstart.passive="dismiss"
  >
    <div class="welcome-vignette" aria-hidden="true" />
    <div class="welcome-grid" aria-hidden="true" />
    <div class="welcome-scale">
      <div class="welcome-inner">
        <div class="logo-wrap">
          <img
            class="nerv-logo"
            src="/nerv-logo.svg"
            width="120"
            height="120"
            alt=""
          />
        </div>
        <div class="welcome-copy">
          <h1 class="welcome-title">{{ title }}</h1>
          <p class="welcome-sub">{{ subtitle }}</p>
          <p class="welcome-hint">
            {{ hint }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

const props = defineProps({
  title: { type: String, default: 'MAGI' },
  subtitle: { type: String, default: '' },
  hint: { type: String, default: '' }
})

const emit = defineEmits(['dismiss'])

let keyHandler

function dismiss() {
  emit('dismiss')
}

onMounted(() => {
  keyHandler = (e) => {
    const t = (e.target?.tagName || '').toLowerCase()
    if (t === 'select' || t === 'input' || t === 'textarea' || e.target?.isContentEditable) {
      return
    }
    e.preventDefault()
    dismiss()
  }
  window.addEventListener('keydown', keyHandler, { passive: false })
})

onUnmounted(() => {
  if (keyHandler) window.removeEventListener('keydown', keyHandler)
})
</script>

<style scoped>
.welcome-root {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: #030305;
  overflow: visible;
  font-family: 'JetBrains Mono', 'Consolas', ui-monospace, monospace;
  outline: none;
  -webkit-tap-highlight-color: transparent;
}

.welcome-vignette {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 100% 100% at 50% 50%, transparent 0%, rgba(0, 0, 0, 0.55) 100%);
  pointer-events: none;
}

.welcome-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(230, 126, 34, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(230, 126, 34, 0.06) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 50%, black 20%, transparent 100%);
  pointer-events: none;
}

.welcome-scale {
  position: relative;
  z-index: 1;
  transform: scale(3.5);
  transform-origin: center center;
}

.welcome-inner {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 12px 16px 20px;
  max-width: 520px;
}

.logo-wrap {
  flex-shrink: 0;
  margin: 0 0 6px;
}

.nerv-logo {
  display: block;
  width: min(28vw, 120px);
  height: auto;
}

.welcome-copy {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  max-width: 100%;
}

.welcome-title {
  margin: 0;
  font-size: clamp(0.66rem, 2.1vw, 0.87rem);
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #ececec;
  line-height: 1.25;
}

.welcome-sub {
  margin: 0;
  font-size: 7px;
  line-height: 1.35;
  letter-spacing: 0.1em;
  color: rgba(200, 200, 200, 0.65);
}

.welcome-hint {
  margin: 2px 0 0;
  font-size: 7px;
  letter-spacing: 0.14em;
  color: #2ecc71;
  line-height: 1.3;
}

.welcome-copyright {
  position: fixed;
  bottom: 10px;
  left: 50%;
  z-index: 2;
  transform: translateX(-50%);
  font-size: 6px;
  letter-spacing: 0.25em;
  color: rgba(230, 126, 34, 0.35);
  margin: 0;
  pointer-events: none;
}
</style>
