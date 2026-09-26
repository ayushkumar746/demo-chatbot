import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('../src/services/api.js', () => ({
  fetchCart: vi.fn(),
  setCartItemQuantity: vi.fn(),
}))

const api = await import('../src/services/api.js')
const { normalizeCart, useCartStore } = await import('../src/stores/cart.js')

const FANTA = { product_id: 'PROD_005', name: 'Fanta 750ml', price: 40, image_url: '', inventory: 50 }
const COKE = { product_id: 'PROD_001', name: 'Coca Cola 750ml', price: 45, image_url: '', inventory: 50 }

function serverCart(lines) {
  const items = lines.map(([product, quantity]) => ({
    product_id: product.product_id, name: product.name, price: product.price,
    quantity, total_price: product.price * quantity,
  }))
  return {
    cart_id: 'CART_user123_STORE_1', user_id: 'user123', store_id: 'STORE_1', items,
    total_items: items.reduce((s, i) => s + i.quantity, 0),
    total_price: items.reduce((s, i) => s + i.total_price, 0),
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

describe('normalizeCart', () => {
  it('merges duplicate product lines into one and recomputes totals', () => {
    const cart = normalizeCart({ items: [
      { product_id: 'PROD_005', name: 'Fanta', price: 40, quantity: 1 },
      { product_id: 'PROD_005', name: 'Fanta', price: 40, quantity: 1 },
    ] })
    expect(cart.items).toHaveLength(1)
    expect(cart.items[0].quantity).toBe(2)
    expect(cart.total_items).toBe(2)
    expect(cart.total_price).toBe(80)
  })

  it('drops lines with zero quantity', () => {
    expect(normalizeCart({ items: [{ product_id: 'A', price: 1, quantity: 0 }] }).items).toEqual([])
  })
})

describe('cart store', () => {
  it('synchronises with a chat cart_state immediately', () => {
    const cart = useCartStore()
    cart.syncFromServer(serverCart([[FANTA, 1]]))
    expect(cart.items.map((i) => [i.name, i.quantity])).toEqual([['Fanta 750ml', 1]])
    expect(cart.itemCount).toBe(1)
    expect(cart.totalPrice).toBe(40)

    cart.syncFromServer(serverCart([[FANTA, 2]]))
    expect(cart.items).toHaveLength(1)
    expect(cart.quantityOf('PROD_005')).toBe(2)
  })

  it('increments optimistically and reconciles with the server', async () => {
    api.setCartItemQuantity.mockResolvedValue(serverCart([[FANTA, 1]]))
    const cart = useCartStore()

    const done = cart.increment(FANTA)
    expect(cart.quantityOf('PROD_005')).toBe(1) // before the server answers
    await done

    expect(api.setCartItemQuantity).toHaveBeenCalledWith('PROD_005', 1)
    expect(cart.items).toHaveLength(1)
  })

  it('sends rapid clicks sequentially with absolute quantities', async () => {
    api.setCartItemQuantity.mockImplementation(async (id, q) => serverCart([[FANTA, q]]))
    const cart = useCartStore()
    cart.increment(FANTA)
    cart.increment(FANTA)
    await cart.increment(FANTA)

    expect(api.setCartItemQuantity.mock.calls.map((call) => call[1])).toEqual([1, 2, 3])
    expect(cart.quantityOf('PROD_005')).toBe(3)
    expect(cart.items).toHaveLength(1)
  })

  it('removes an item when quantity reaches 0 and never goes negative', async () => {
    api.setCartItemQuantity.mockImplementation(async (id, q) => serverCart(q ? [[FANTA, q], [COKE, 2]] : [[COKE, 2]]))
    const cart = useCartStore()
    cart.syncFromServer(serverCart([[FANTA, 1], [COKE, 2]]))

    await cart.decrement(FANTA)
    expect(cart.quantityOf('PROD_005')).toBe(0)
    expect(cart.items.map((i) => i.product_id)).toEqual(['PROD_001'])

    await cart.decrement(FANTA)
    expect(api.setCartItemQuantity).toHaveBeenCalledTimes(1)
  })

  it('does not exceed stock', async () => {
    const cart = useCartStore()
    cart.syncFromServer(serverCart([[FANTA, 2]]))
    await cart.increment({ ...FANTA, inventory: 2 })
    expect(api.setCartItemQuantity).not.toHaveBeenCalled()
    expect(cart.quantityOf('PROD_005')).toBe(2)
  })

  it('restores the server cart and shows a message when an update is rejected', async () => {
    const error = Object.assign(new Error('400'), { userMessage: 'Only 3 of Fanta 750ml available' })
    api.setCartItemQuantity.mockRejectedValue(error)
    api.fetchCart.mockResolvedValue(serverCart([[FANTA, 3]]))
    const cart = useCartStore()
    cart.syncFromServer(serverCart([[FANTA, 3]]))

    await cart.increment(FANTA)
    expect(cart.quantityOf('PROD_005')).toBe(3)
    expect(cart.error).toBe('Only 3 of Fanta 750ml available')
  })
})
