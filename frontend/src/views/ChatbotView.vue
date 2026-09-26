<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import ProductList from '../components/ProductList.vue'
import CartSummary from '../components/CartSummary.vue'
import ChatWindow from '../components/ChatWindow.vue'
import { useCartStore } from '../stores/cart.js'
import { chatContext } from '../config.js'
import { formatPrice } from '../utils/format.js'

const cart = useCartStore()
const { itemCount, totalPrice } = storeToRefs(cart)

function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// Hide the floating chat button while the chat is already on screen
const chatVisible = ref(false)
let chatObserver = null

onMounted(() => {
  // The backend cart survives page refreshes; load it on start
  cart.load()
  const chatElement = document.getElementById('chat')
  if (chatElement && 'IntersectionObserver' in window) {
    chatObserver = new IntersectionObserver(([entry]) => { chatVisible.value = entry.isIntersecting }, { threshold: 0.25 })
    chatObserver.observe(chatElement)
  }
})

onBeforeUnmount(() => chatObserver?.disconnect())
</script>

<template>
  <div class="layout">
    <header class="topbar">
      <div class="topbar__brand">
        <span class="topbar__logo" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M4 5h2.5l2.2 10h9.1l2-7H8" /><circle cx="10" cy="19" r="1.5" /><circle cx="17" cy="19" r="1.5" /></svg>
        </span>
        <div>
          <h1>ShopBot</h1>
          <p>AI shopping assistant · {{ chatContext.store_id }}</p>
        </div>
      </div>
      <button type="button" class="topbar__cart" :aria-label="`Cart: ${itemCount} items, ${formatPrice(totalPrice)}`" @click="scrollToSection('cart')">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h2.5l2.2 10h9.1l2-7H8" /><circle cx="10" cy="19" r="1.5" /><circle cx="17" cy="19" r="1.5" /></svg>
        <span class="topbar__cart-total">{{ formatPrice(totalPrice) }}</span>
        <span class="topbar__badge" aria-hidden="true">{{ itemCount }}</span>
      </button>
    </header>

    <main class="content">
      <div class="content__products">
        <ProductList />
      </div>
      <aside class="content__side" aria-label="Cart and assistant">
        <CartSummary class="content__cart" />
        <ChatWindow class="content__chat" />
      </aside>
    </main>

    <button
      v-show="!chatVisible"
      type="button"
      class="chat-fab"
      aria-label="Open chat assistant"
      @click="scrollToSection('chat')"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 18l-1 3 4-2h9a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3H7a3 3 0 0 0-3 3v9" /></svg>
    </button>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 clamp(16px, 3vw, 32px);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--color-border);
}

.topbar__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.topbar__logo {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
}

.topbar svg {
  width: 22px;
  height: 22px;
  fill: none;
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.topbar__logo svg {
  stroke: #fff;
}

h1 {
  margin: 0;
  font-size: 18px;
  line-height: 1.1;
}

.topbar__brand p {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.topbar__cart {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 42px;
  padding: 0 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  font-weight: 700;
  transition: border-color var(--transition), box-shadow var(--transition);
}

.topbar__cart:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.topbar__cart svg {
  stroke: var(--color-primary);
}

.topbar__badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: var(--color-primary);
  color: #fff;
  font-size: 12px;
}

.content {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  gap: clamp(16px, 2vw, 28px);
  max-width: 1440px;
  margin: 0 auto;
  padding: 20px clamp(16px, 3vw, 32px) 32px;
}

.content__side {
  position: sticky;
  top: calc(var(--header-height) + 20px);
  height: calc(100vh - var(--header-height) - 40px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.content__cart {
  flex: 0 1 auto;
  max-height: 38%;
}

.content__chat {
  flex: 1 1 0;
}

.chat-fab {
  display: none;
}

/* Tablet and mobile: Products, Cart, Chat stacked */
@media (max-width: 1023px) {
  .content {
    grid-template-columns: minmax(0, 1fr);
  }

  .content__side {
    position: static;
    height: auto;
  }

  .content__cart {
    max-height: none;
  }

  .content__chat {
    height: min(78vh, 680px);
    flex: none;
  }

  .chat-fab {
    position: fixed;
    right: 16px;
    bottom: calc(16px + env(safe-area-inset-bottom, 0px));
    z-index: 30;
    width: 56px;
    height: 56px;
    display: grid;
    place-items: center;
    border: none;
    border-radius: 50%;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    box-shadow: var(--shadow-lg);
  }

  .chat-fab svg {
    width: 26px;
    height: 26px;
    fill: none;
    stroke: #fff;
    stroke-width: 1.9;
    stroke-linecap: round;
    stroke-linejoin: round;
  }
}

@media (max-width: 480px) {
  .topbar__brand p {
    display: none;
  }

  .topbar__cart-total {
    display: none;
  }

  .content__chat {
    height: calc(100vh - var(--header-height) - 24px);
    height: calc(100dvh - var(--header-height) - 24px);
  }
}
</style>
