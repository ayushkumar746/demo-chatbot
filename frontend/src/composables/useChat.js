/**
 * Chat state and behaviour, kept separate from the UI components.
 *
 * Messages persist in sessionStorage for the current browser session. Every
 * assistant reply that carries a `cart_state` synchronises the cart store.
 */
import { ref } from 'vue'
import { sendChat } from '../services/api.js'
import { useCartStore } from '../stores/cart.js'

const STORAGE_KEY = 'demo-chatbot:messages'
const MAX_STORED_MESSAGES = 100
const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  text: 'Hi! I can find products and add them to your cart. Try "Add cold drink which have less price 100 RS".',
  status: 'info',
}

function loadMessages() {
  try {
    const stored = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(stored) && stored.length ? stored : [WELCOME_MESSAGE]
  } catch {
    return [WELCOME_MESSAGE]
  }
}

function saveMessages(messages) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-MAX_STORED_MESSAGES)))
  } catch {
    // Storage unavailable (private mode, quota); history simply isn't persisted
  }
}

let nextId = Date.now()
function createMessage(role, text, extra = {}) {
  nextId += 1
  return { id: `${role}-${nextId}`, role, text, timestamp: new Date().toISOString(), ...extra }
}

// Shared across components so the chat survives re-renders
const messages = ref(loadMessages())
const pending = ref(false)

export function useChat() {
  const cartStore = useCartStore()

  function push(message) {
    messages.value = [...messages.value, message]
    saveMessages(messages.value)
  }

  /** Send a query. Ignored while a request is pending or when empty. */
  async function send(rawQuery) {
    const query = (rawQuery || '').trim()
    if (!query || pending.value) return false

    pending.value = true
    push(createMessage('user', query))
    try {
      const data = await sendChat(query)
      if (data.cart_state) cartStore.syncFromServer(data.cart_state)
      if (!data.success) console.warn('[chat] request not completed:', data.error)

      const addedItem = data.success && data.intent?.action === 'ADD_TO_CART'
        ? findChangedItem(data.cart_state, data.response)
        : null
      push(createMessage('assistant', data.response, {
        status: data.success ? 'success' : 'warning',
        intent: data.intent?.action ?? null,
        product: addedItem,
      }))
    } catch (err) {
      console.error('[chat] request failed', err)
      push(createMessage('assistant', err.userMessage || "Sorry, I couldn't complete that request. Please try again.", {
        status: 'error',
      }))
    } finally {
      pending.value = false
    }
    return true
  }

  function clearHistory() {
    messages.value = [WELCOME_MESSAGE]
    saveMessages(messages.value)
  }

  return { messages, pending, send, clearHistory }
}

/** The cart line the assistant's reply is about (matched by product name). */
function findChangedItem(cartState, responseText) {
  const items = cartState?.items ?? []
  return items.find((item) => responseText.startsWith(item.name)) ?? null
}
