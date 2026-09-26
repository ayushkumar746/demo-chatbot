/**
 * Product browsing state: debounced search + pagination over GET /api/products.
 */
import { onBeforeUnmount, ref, watch } from 'vue'
import { fetchProducts } from '../services/api.js'
import { PRODUCTS_PAGE_SIZE, SEARCH_DEBOUNCE_MS } from '../config.js'

export function useProducts() {
  const query = ref('')
  const page = ref(1)
  const products = ref([])
  const total = ref(0)
  const totalPages = ref(1)
  const loading = ref(false)
  const error = ref('')
  let requestId = 0
  let debounceTimer = null

  async function load() {
    const currentRequest = ++requestId
    loading.value = true
    error.value = ''
    try {
      const data = await fetchProducts({ q: query.value, page: page.value, pageSize: PRODUCTS_PAGE_SIZE })
      if (currentRequest !== requestId) return // a newer search superseded this one
      products.value = data.items
      total.value = data.total
      totalPages.value = data.total_pages
    } catch (err) {
      if (currentRequest !== requestId) return
      console.error('[products] load failed', err)
      error.value = err.userMessage || 'Could not load products.'
      products.value = []
    } finally {
      if (currentRequest === requestId) loading.value = false
    }
  }

  watch(query, () => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      page.value = 1
      load()
    }, SEARCH_DEBOUNCE_MS)
  })

  function goToPage(target) {
    const next = Math.min(Math.max(1, target), totalPages.value)
    if (next === page.value) return
    page.value = next
    load()
  }

  onBeforeUnmount(() => clearTimeout(debounceTimer))

  return { query, page, products, total, totalPages, loading, error, load, goToPage }
}
