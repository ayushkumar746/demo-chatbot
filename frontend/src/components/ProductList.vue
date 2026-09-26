<script setup>
import { onMounted, ref } from 'vue'
import ProductCard from './ProductCard.vue'
import SearchBar from './SearchBar.vue'
import Pagination from './Pagination.vue'
import { useProducts } from '../composables/useProducts.js'

const { query, page, products, total, totalPages, loading, error, load, goToPage } = useProducts()
const sectionRef = ref(null)

function changePage(target) {
  goToPage(target)
  sectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(load)
</script>

<template>
  <section ref="sectionRef" class="products" aria-labelledby="products-heading">
    <div class="products__header">
      <div>
        <h2 id="products-heading">Products</h2>
        <p class="products__count" aria-live="polite">
          <template v-if="!loading || products.length">{{ total }} {{ total === 1 ? 'product' : 'products' }}</template>
        </p>
      </div>
      <SearchBar v-model="query" placeholder="Search by name, brand or category…" class="products__search" />
    </div>

    <div v-if="error" class="products__state products__state--error" role="alert">
      <p>{{ error }}</p>
      <button type="button" class="btn-primary" @click="load">Try again</button>
    </div>

    <div v-else-if="loading && !products.length" class="products__grid" aria-busy="true" aria-label="Loading products">
      <div v-for="index in 8" :key="index" class="products__skeleton card" />
    </div>

    <div v-else-if="!products.length" class="products__state">
      <p>No products match “{{ query }}”.</p>
      <button type="button" class="btn-primary" @click="query = ''">Clear search</button>
    </div>

    <div v-else class="products__grid" :class="{ 'products__grid--loading': loading }" :aria-busy="loading">
      <ProductCard v-for="product in products" :key="product.id" :product="product" />
    </div>

    <Pagination :page="page" :total-pages="totalPages" :disabled="loading" @change="changePage" />
  </section>
</template>

<style scoped>
.products {
  display: flex;
  flex-direction: column;
  gap: 18px;
  scroll-margin-top: calc(var(--header-height) + 12px);
}

.products__header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

h2 {
  margin: 0;
  font-size: 22px;
}

.products__count {
  margin: 2px 0 0;
  min-height: 1.4em;
  color: var(--color-text-muted);
  font-size: 14px;
}

.products__search {
  flex: 1 1 280px;
  max-width: 420px;
}

.products__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 16px;
  transition: opacity var(--transition);
}

.products__grid--loading {
  opacity: 0.55;
  pointer-events: none;
}

.products__skeleton {
  height: 320px;
  background: linear-gradient(100deg, #eef0f5 30%, #f7f8fb 50%, #eef0f5 70%);
  background-size: 300% 100%;
  animation: shimmer 1.3s linear infinite;
}

@keyframes shimmer {
  to {
    background-position: -150% 0;
  }
}

.products__state {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 40px 16px;
  text-align: center;
  color: var(--color-text-muted);
}

.products__state p {
  margin: 0;
}

.products__state--error {
  color: var(--color-danger);
}

@media (max-width: 640px) {
  .products__search {
    max-width: none;
  }
}

@media (max-width: 380px) {
  .products__grid {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
}
</style>
