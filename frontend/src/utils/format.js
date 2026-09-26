const rupees = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 })

/** Format an amount in rupees, e.g. 40 -> "₹40". */
export function formatPrice(amount) {
  return rupees.format(Number(amount) || 0).replace(/\.00$/, '')
}

/** "cold_drink" -> "Cold drink" */
export function formatCategory(category) {
  const text = (category || '').replace(/_/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/** Adapt an API product to the shape the cart store uses. */
export function toCartProduct(product) {
  return {
    product_id: product.id,
    name: product.name,
    price: product.price,
    image_url: product.image_url,
    inventory: product.available ? product.inventory : 0,
  }
}
