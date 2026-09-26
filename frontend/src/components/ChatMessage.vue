<script setup>
import { computed } from 'vue'
import ProductImage from './ProductImage.vue'
import { formatPrice } from '../utils/format.js'

const props = defineProps({
  message: { type: Object, required: true },
})

const isUser = computed(() => props.message.role === 'user')

// The cart panel already shows the cart, so drop the textual cart summary the backend appends
const CART_SUMMARY_SEPARATOR = '\n\nCart ('
const displayText = computed(() => {
  const text = props.message.text || ''
  return props.message.role === 'assistant' ? text.split(CART_SUMMARY_SEPARATOR)[0] : text
})
const time = computed(() => {
  if (!props.message.timestamp) return ''
  return new Date(props.message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
})
</script>

<template>
  <li class="message" :class="[`message--${message.role}`, message.status && `message--${message.status}`]">
    <div v-if="!isUser" class="message__avatar" aria-hidden="true">
      <svg viewBox="0 0 24 24">
        <rect x="4" y="7" width="16" height="12" rx="4" /><path d="M12 3v4M9 12h.01M15 12h.01M9.5 15.5h5" />
      </svg>
    </div>
    <div class="message__body">
      <span class="visually-hidden">{{ isUser ? 'You said:' : 'Assistant said:' }}</span>
      <div class="message__bubble">
        <p class="message__text">{{ displayText }}</p>
        <div v-if="message.product" class="message__product">
          <ProductImage :src="message.product.image_url" :name="message.product.name" size="sm" />
          <div>
            <strong>{{ message.product.name }}</strong>
            <span>{{ formatPrice(message.product.price) }} · Qty {{ message.product.quantity }}</span>
          </div>
          <span class="message__product-badge">In cart</span>
        </div>
      </div>
      <time v-if="time" class="message__time" :datetime="message.timestamp">{{ time }}</time>
    </div>
  </li>
</template>

<style scoped>
.message {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  animation: message-in 220ms ease;
}

.message--user {
  justify-content: flex-end;
}

.message__avatar {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--color-primary-soft);
}

.message__avatar svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.message__body {
  display: flex;
  flex-direction: column;
  max-width: 85%;
  min-width: 0;
}

.message--user .message__body {
  align-items: flex-end;
}

.message__bubble {
  padding: 10px 14px;
  border-radius: 16px 16px 16px 4px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  overflow-wrap: anywhere;
}

.message--user .message__bubble {
  border-radius: 16px 16px 4px 16px;
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.message--success .message__bubble {
  border-color: #b9e6d2;
}

.message--warning .message__bubble {
  background: var(--color-warning-soft);
  border-color: #f2dca6;
}

.message--error .message__bubble {
  background: var(--color-danger-soft);
  border-color: #f5c2c2;
  color: var(--color-danger);
}

.message__text {
  margin: 0;
  white-space: pre-line;
  font-size: 14.5px;
}

.message__product {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  padding: 8px;
  border-radius: var(--radius-md);
  background: var(--color-success-soft);
}

.message__product div {
  display: flex;
  flex-direction: column;
  min-width: 0;
  font-size: 13px;
}

.message__product strong {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message__product-badge {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-success);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.message__time {
  margin-top: 4px;
  padding: 0 4px;
  font-size: 11px;
  color: var(--color-text-muted);
}

@keyframes message-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
}
</style>
