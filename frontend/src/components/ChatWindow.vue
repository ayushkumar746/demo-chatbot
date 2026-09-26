<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import ChatMessage from './ChatMessage.vue'
import { useChat } from '../composables/useChat.js'

const SUGGESTIONS = [
  'Add cold drink which have less price 100 RS',
  'Add a mango drink',
  'Add a beer under 100',
]

const { messages, pending, send, clearHistory } = useChat()
const draft = ref('')
const listRef = ref(null)
const inputRef = ref(null)

async function scrollToBottom() {
  await nextTick()
  const list = listRef.value
  if (list) list.scrollTop = list.scrollHeight
}

async function submit(text = draft.value) {
  const query = text.trim()
  if (!query || pending.value) return
  draft.value = ''
  await send(query)
  inputRef.value?.focus()
}

watch(() => messages.value.length, scrollToBottom)
watch(pending, scrollToBottom)
onMounted(scrollToBottom)
</script>

<template>
  <section id="chat" class="chat card" aria-labelledby="chat-heading">
    <header class="chat__header">
      <div class="chat__avatar" aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <rect x="4" y="7" width="16" height="12" rx="4" /><path d="M12 3v4M9 12h.01M15 12h.01M9.5 15.5h5" />
        </svg>
      </div>
      <div class="chat__title">
        <h2 id="chat-heading">Shopping Assistant</h2>
        <p><span class="chat__status-dot" aria-hidden="true" /> Powered by Gemini</p>
      </div>
      <button type="button" class="chat__clear" title="Clear conversation" aria-label="Clear conversation" @click="clearHistory">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" /></svg>
      </button>
    </header>

    <ol ref="listRef" class="chat__messages" aria-live="polite" aria-relevant="additions">
      <ChatMessage v-for="message in messages" :key="message.id" :message="message" />
      <li v-if="pending" class="chat__typing" role="status">
        <span>Assistant is thinking</span>
        <span class="chat__dots" aria-hidden="true"><i /><i /><i /></span>
      </li>
    </ol>

    <div v-if="messages.length <= 1" class="chat__suggestions">
      <button
        v-for="suggestion in SUGGESTIONS"
        :key="suggestion"
        type="button"
        class="chat__chip"
        :disabled="pending"
        @click="submit(suggestion)"
      >
        {{ suggestion }}
      </button>
    </div>

    <form class="chat__composer" @submit.prevent="submit()">
      <label for="chat-input" class="visually-hidden">Type your shopping request</label>
      <input
        id="chat-input"
        ref="inputRef"
        v-model="draft"
        type="text"
        placeholder="Type your request…"
        autocomplete="off"
        maxlength="500"
        enterkeyhint="send"
      />
      <button type="submit" class="btn-primary chat__send" :disabled="pending || !draft.trim()">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12 20 4l-5 16-3-7-8-1Z" /></svg>
        <span>{{ pending ? 'Sending' : 'Send' }}</span>
      </button>
    </form>
  </section>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  scroll-margin-top: calc(var(--header-height) + 12px);
}

.chat__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border);
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: #fff;
}

.chat__avatar {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
}

.chat__avatar svg,
.chat__clear svg {
  width: 22px;
  height: 22px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.chat__title {
  flex: 1;
  min-width: 0;
}

.chat__title h2 {
  margin: 0;
  font-size: 16px;
}

.chat__title p {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  opacity: 0.9;
}

.chat__status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4ade80;
}

.chat__clear {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: #fff;
}

.chat__clear:hover {
  background: rgba(255, 255, 255, 0.18);
}

.chat__messages {
  flex: 1;
  min-height: 0;
  margin: 0;
  padding: 16px;
  list-style: none;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: var(--color-surface-muted);
  overscroll-behavior: contain;
}

.chat__typing {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  align-self: flex-start;
  padding: 10px 14px;
  border-radius: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 13px;
}

.chat__dots {
  display: inline-flex;
  gap: 4px;
}

.chat__dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: bounce 1.2s infinite ease-in-out;
}

.chat__dots i:nth-child(2) {
  animation-delay: 0.15s;
}

.chat__dots i:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

.chat__suggestions {
  display: flex;
  gap: 8px;
  padding: 10px 16px 0;
  overflow-x: auto;
  background: var(--color-surface);
}

.chat__chip {
  flex-shrink: 0;
  padding: 6px 12px;
  border: 1px solid #d6d3ff;
  border-radius: 999px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  transition: background var(--transition);
}

.chat__chip:hover:not(:disabled) {
  background: #e0e3ff;
}

.chat__composer {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
}

.chat__composer input {
  flex: 1;
  min-width: 0;
  height: 46px;
  padding: 0 16px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface-muted);
  transition: border-color var(--transition), box-shadow var(--transition);
}

.chat__composer input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-soft);
  background: var(--color-surface);
}

.chat__send {
  height: 46px;
  padding: 0 18px;
  border-radius: 999px;
}

.chat__send svg {
  width: 18px;
  height: 18px;
  fill: currentColor;
}

@media (max-width: 420px) {
  .chat__send span {
    display: none;
  }

  .chat__send {
    width: 46px;
    padding: 0;
  }
}
</style>
