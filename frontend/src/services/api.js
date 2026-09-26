/**
 * Backend API client. All HTTP calls go through here.
 *
 * Failures are normalised into ApiError with a user-friendly `userMessage`;
 * technical details are kept on the error (and logged by callers) but never
 * shown to the user.
 */
import { API_BASE_URL, API_TIMEOUT_MS, PRODUCTS_PAGE_SIZE, chatContext } from '../config.js'

export class ApiError extends Error {
  /**
   * @param {'network'|'timeout'|'http'|'malformed'} kind
   * @param {string} userMessage  Safe to show in the UI
   * @param {object} [details]    Technical details for logging
   */
  constructor(kind, userMessage, details = {}) {
    super(`${kind}: ${details.detail || userMessage}`)
    this.name = 'ApiError'
    this.kind = kind
    this.userMessage = userMessage
    this.status = details.status
    this.detail = details.detail
  }
}

function messageForStatus(status, detail) {
  if (status === 400 && typeof detail === 'string') return detail
  if (status === 404) return 'The requested item was not found.'
  if (status === 422) return 'The request was invalid. Please check your input.'
  if (status === 429) return 'Too many requests. Please wait a moment and try again.'
  if (status >= 500) return 'The shopping service is temporarily unavailable. Please try again.'
  return "Sorry, I couldn't complete that request. Please try again."
}

async function request(path, { method = 'GET', body, query, timeoutMs = API_TIMEOUT_MS } = {}) {
  const url = new URL(`${API_BASE_URL}${path}`)
  Object.entries(query || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value)
  })

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let response
  try {
    response = await fetch(url, {
      method,
      headers: { accept: '*/*', ...(body ? { 'Content-Type': 'application/json' } : {}) },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new ApiError('timeout', 'The request took too long. Please try again.', { detail: `Timed out after ${timeoutMs}ms` })
    }
    throw new ApiError('network', "Can't reach the shopping service. Please check that the backend is running.", {
      detail: error.message,
    })
  } finally {
    clearTimeout(timer)
  }

  let data
  try {
    data = await response.json()
  } catch {
    throw new ApiError(response.ok ? 'malformed' : 'http', messageForStatus(response.status), {
      status: response.status,
      detail: 'Response body is not valid JSON',
    })
  }

  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : JSON.stringify(data?.detail ?? data)
    throw new ApiError('http', messageForStatus(response.status, data?.detail), { status: response.status, detail })
  }
  return data
}

function isCart(value) {
  return value && typeof value === 'object' && Array.isArray(value.items)
}

/**
 * Send a natural-language query. The user/store/session context is added here.
 * @returns {Promise<{response: string, success: boolean, intent: object|null, cart_state: object|null, error: string|null}>}
 */
export async function sendChat(query) {
  const data = await request('/api/chat', { method: 'POST', body: { query, ...chatContext } })
  if (typeof data?.response !== 'string' || typeof data?.success !== 'boolean') {
    throw new ApiError('malformed', 'Received an unexpected response. Please try again.', {
      detail: `Unexpected chat response: ${JSON.stringify(data).slice(0, 200)}`,
    })
  }
  if (data.cart_state !== null && data.cart_state !== undefined && !isCart(data.cart_state)) {
    data.cart_state = null
  }
  return data
}

/** Browse products with keyword search and pagination. */
export async function fetchProducts({ q = '', page = 1, pageSize = PRODUCTS_PAGE_SIZE } = {}) {
  const data = await request('/api/products', {
    query: { store_id: chatContext.store_id, q: q.trim(), page, page_size: pageSize },
  })
  if (!Array.isArray(data?.items) || typeof data?.total_pages !== 'number') {
    throw new ApiError('malformed', 'Could not load products. Please try again.', { detail: 'Unexpected products response' })
  }
  return data
}

/** The user's current cart (shared with the chatbot). */
export async function fetchCart() {
  const data = await request('/api/cart', {
    query: { user_id: chatContext.user_id, store_id: chatContext.store_id },
  })
  if (!isCart(data)) throw new ApiError('malformed', 'Could not load your cart.', { detail: 'Unexpected cart response' })
  return data
}

/** Set the absolute quantity of a product in the cart; 0 removes it. */
export async function setCartItemQuantity(productId, quantity) {
  const data = await request(`/api/cart/items/${encodeURIComponent(productId)}`, {
    method: 'PUT',
    body: { user_id: chatContext.user_id, store_id: chatContext.store_id, quantity },
  })
  if (!isCart(data?.cart)) throw new ApiError('malformed', 'Could not update your cart.', { detail: 'Unexpected cart update response' })
  return data.cart
}
