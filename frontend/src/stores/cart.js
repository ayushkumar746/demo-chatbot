/**
 * Cart store — the single source of cart state in the UI.
 *
 * The backend cart is authoritative: chat responses (`cart_state`) and cart
 * API responses replace local state via `syncFromServer`. Quantity changes are
 * applied optimistically, sent to the backend one at a time (so rapid +/-
 * clicks can't race), and reconciled with the server cart when the queue drains.
 * The cart always holds exactly one line per product_id.
 */
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchCart, setCartItemQuantity } from '../services/api.js'
import { MAX_QUANTITY_PER_ITEM } from '../config.js'

/** Merge any duplicate lines by product_id and recompute totals. */
export function normalizeCart(cart) {
  const byId = new Map()
  for (const item of cart?.items ?? []) {
    if (!item?.product_id || !(item.quantity > 0)) continue
    const existing = byId.get(item.product_id)
    if (existing) {
      existing.quantity += item.quantity
    } else {
      byId.set(item.product_id, { ...item })
    }
  }
  const items = [...byId.values()].map((item) => ({ ...item, total_price: item.price * item.quantity }))
  return {
    ...cart,
    items,
    total_items: items.reduce((sum, item) => sum + item.quantity, 0),
    total_price: items.reduce((sum, item) => sum + item.total_price, 0),
  }
}

export const useCartStore = defineStore('cart', () => {
  const cart = ref(normalizeCart({ items: [] }))
  const loading = ref(false)
  const error = ref('')
  const pendingOperations = ref(0)
  let queue = Promise.resolve()

  const items = computed(() => cart.value.items)
  const itemCount = computed(() => cart.value.total_items)
  const totalPrice = computed(() => cart.value.total_price)
  const isSyncing = computed(() => pendingOperations.value > 0)

  function quantityOf(productId) {
    return cart.value.items.find((item) => item.product_id === productId)?.quantity ?? 0
  }

  /** Replace local state with the backend's cart. */
  function syncFromServer(serverCart) {
    if (serverCart && Array.isArray(serverCart.items)) {
      cart.value = normalizeCart(serverCart)
    }
  }

  async function load() {
    loading.value = true
    error.value = ''
    try {
      syncFromServer(await fetchCart())
    } catch (err) {
      console.error('[cart] load failed', err)
      error.value = err.userMessage || 'Could not load your cart.'
    } finally {
      loading.value = false
    }
  }

  function applyLocalQuantity(product, quantity) {
    const others = cart.value.items.filter((item) => item.product_id !== product.product_id)
    const next = quantity > 0 ? [...others, { ...product, quantity }] : others
    // Keep the original position of an existing line
    const order = cart.value.items.map((item) => item.product_id)
    next.sort((a, b) => {
      const ai = order.indexOf(a.product_id)
      const bi = order.indexOf(b.product_id)
      return (ai === -1 ? Infinity : ai) - (bi === -1 ? Infinity : bi)
    })
    cart.value = normalizeCart({ ...cart.value, items: next })
  }

  /**
   * Set a product's quantity (0 removes it). `product` needs product_id, name,
   * price and optionally image_url. Quantity is clamped to [0, max].
   */
  function setQuantity(product, requestedQuantity) {
    const maxAllowed = Math.min(MAX_QUANTITY_PER_ITEM, product.inventory ?? MAX_QUANTITY_PER_ITEM)
    const quantity = Math.max(0, Math.min(Math.floor(requestedQuantity), maxAllowed))
    if (quantity === quantityOf(product.product_id)) return queue

    error.value = ''
    applyLocalQuantity(product, quantity)
    pendingOperations.value += 1

    queue = queue
      .then(async () => {
        const serverCart = await setCartItemQuantity(product.product_id, quantity)
        if (pendingOperations.value === 1) syncFromServer(serverCart)
      })
      .catch(async (err) => {
        console.error('[cart] update failed', err)
        error.value = err.userMessage || 'Could not update your cart.'
        // Recover the real state after a rejected change
        try {
          syncFromServer(await fetchCart())
        } catch (reloadError) {
          console.error('[cart] reload failed', reloadError)
        }
      })
      .finally(() => {
        pendingOperations.value -= 1
      })
    return queue
  }

  function increment(product) {
    return setQuantity(product, quantityOf(product.product_id) + 1)
  }

  function decrement(product) {
    return setQuantity(product, quantityOf(product.product_id) - 1)
  }

  function clearError() {
    error.value = ''
  }

  return {
    cart, items, itemCount, totalPrice, loading, error, isSyncing,
    quantityOf, syncFromServer, load, setQuantity, increment, decrement, clearError,
  }
})
