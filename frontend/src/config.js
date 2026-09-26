/**
 * Central frontend configuration.
 *
 * Values come from Vite env variables (see .env.example) with safe defaults,
 * so the user/store/session context lives in exactly one place.
 */
const env = import.meta.env ?? {}

function numberFromEnv(value, fallback) {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

export const API_BASE_URL = (env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '')

/** Sent automatically with every chat request; the user only types the query. */
export const chatContext = Object.freeze({
  user_id: env.VITE_DEFAULT_USER_ID || 'user123',
  store_id: env.VITE_DEFAULT_STORE_ID || 'STORE_1',
  session_id: env.VITE_DEFAULT_SESSION_ID || 'SESSION_1',
})

export const API_TIMEOUT_MS = numberFromEnv(env.VITE_API_TIMEOUT_MS, 60000)
export const PRODUCTS_PAGE_SIZE = numberFromEnv(env.VITE_PRODUCTS_PAGE_SIZE, 12)
export const MAX_QUANTITY_PER_ITEM = numberFromEnv(env.VITE_MAX_QUANTITY_PER_ITEM, 10)
export const SEARCH_DEBOUNCE_MS = 300
