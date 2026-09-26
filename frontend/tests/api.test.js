import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, fetchProducts, sendChat, setCartItemQuantity } from '../src/services/api.js'

function mockFetch(impl) {
  const fn = vi.fn(impl)
  vi.stubGlobal('fetch', fn)
  return fn
}

const jsonResponse = (status, body) => ({ ok: status < 400, status, json: async () => body })
const CHAT_OK = { response: 'Added', success: true, intent: null, cart_state: { items: [] }, error: null }

afterEach(() => vi.unstubAllGlobals())

describe('sendChat', () => {
  it('sends only the query plus the central user/store/session context', async () => {
    const fetchMock = mockFetch(async () => jsonResponse(200, CHAT_OK))
    await sendChat('Add cold drink which have less price 100 RS')

    const [url, options] = fetchMock.mock.calls[0]
    expect(String(url)).toBe('http://localhost:8000/api/chat')
    expect(options.method).toBe('POST')
    expect(options.headers).toMatchObject({ accept: '*/*', 'Content-Type': 'application/json' })
    expect(JSON.parse(options.body)).toEqual({
      query: 'Add cold drink which have less price 100 RS',
      user_id: 'user123',
      store_id: 'STORE_1',
      session_id: 'SESSION_1',
    })
  })

  it('classifies network failures', async () => {
    mockFetch(async () => { throw new TypeError('Failed to fetch') })
    await expect(sendChat('hi')).rejects.toMatchObject({ kind: 'network' })
  })

  it('classifies HTTP 5xx without leaking details', async () => {
    mockFetch(async () => jsonResponse(500, { detail: 'Traceback (most recent call last)...' }))
    const error = await sendChat('hi').catch((err) => err)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.kind).toBe('http')
    expect(error.userMessage).not.toContain('Traceback')
  })

  it('rejects malformed responses', async () => {
    mockFetch(async () => jsonResponse(200, { unexpected: true }))
    await expect(sendChat('hi')).rejects.toMatchObject({ kind: 'malformed' })
  })

  it('rejects non-JSON bodies', async () => {
    mockFetch(async () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('bad') } }))
    await expect(sendChat('hi')).rejects.toMatchObject({ kind: 'malformed' })
  })

  it('times out', async () => {
    vi.useFakeTimers()
    mockFetch((url, { signal }) => new Promise((resolve, reject) => {
      signal.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })))
    }))
    const pending = sendChat('hi').catch((err) => err)
    await vi.advanceTimersByTimeAsync(60000)
    expect(await pending).toMatchObject({ kind: 'timeout' })
    vi.useRealTimers()
  })
})

describe('product and cart endpoints', () => {
  it('passes search and pagination parameters', async () => {
    const fetchMock = mockFetch(async () => jsonResponse(200, { items: [], total: 0, total_pages: 1 }))
    await fetchProducts({ q: ' fanta ', page: 3 })
    const url = new URL(String(fetchMock.mock.calls[0][0]))
    expect(url.pathname).toBe('/api/products')
    expect(Object.fromEntries(url.searchParams)).toEqual({ store_id: 'STORE_1', q: 'fanta', page: '3', page_size: '12' })
  })

  it('surfaces 400 business-rule messages from the cart API', async () => {
    mockFetch(async () => jsonResponse(400, { detail: 'Maximum quantity per item is 10' }))
    await expect(setCartItemQuantity('P1', 11)).rejects.toMatchObject({ userMessage: 'Maximum quantity per item is 10' })
  })
})
