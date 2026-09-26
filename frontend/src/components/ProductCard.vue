<script setup>
import { computed } from 'vue'
import ProductImage from './ProductImage.vue'
import QuantityControl from './QuantityControl.vue'
import { useCartStore } from '../stores/cart.js'
import { MAX_QUANTITY_PER_ITEM } from '../config.js'
import { formatCategory, formatPrice, toCartProduct } from '../utils/format.js'

const props = defineProps({
  product: { type: Object, required: true },
})

const cart = useCartStore()
const cartProduct = computed(() => toCartProduct(props.product))
const quantity = computed(() => cart.quantityOf(props.product.id))
const inStock = computed(() => props.product.available && props.product.inventory > 0)
const maxQuantity = computed(() => Math.min(MAX_QUANTITY_PER_ITEM, props.product.inventory))
</script>

<template>
  <article class="product-card card" :class="{ 'product-card--in-cart': quantity > 0 }">
    <div class="product-card__media">
      <ProductImage :src="product.image_url" :name="product.name" :category="product.category" />
      <span v-if="!inStock" class="product-card__badge product-card__badge--muted">Out of stock</span>
      <span v-else-if="quantity > 0" class="product-card__badge">In cart</span>
    </div>

    <div class="product-card__body">
      <p class="product-card__meta">
        <span v-if="product.brand">{{ product.brand }}</span>
        <span aria-hidden="true" v-if="product.brand">·</span>
        <span>{{ formatCategory(product.category) }}</span>
      </p>
      <h3 class="product-card__name" :title="product.name">{{ product.name }}</h3>
      <p class="product-card__price">{{ formatPrice(product.price) }}</p>
    </div>

    <div class="product-card__actions">
      <QuantityControl
        v-if="quantity > 0"
        :quantity="quantity"
        :max="maxQuantity"
        :label="product.name"
        @increment="cart.increment(cartProduct)"
        @decrement="cart.decrement(cartProduct)"
      />
      <button
        v-else
        type="button"
        class="btn-primary product-card__add"
        :disabled="!inStock"
        :aria-label="`Add ${product.name} to cart`"
        @click="cart.increment(cartProduct)"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 12h12M12 6v12" /></svg>
        {{ inStock ? 'Add' : 'Unavailable' }}
      </button>
    </div>
  </article>
</template>

<style scoped>
.product-card {
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 10px;
  transition: transform var(--transition), box-shadow var(--transition), border-color var(--transition);
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.product-card--in-cart {
  border-color: #c7c3ff;
}

.product-card__media {
  position: relative;
}

.product-card__badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: var(--color-primary);
  color: #fff;
}

.product-card__badge--muted {
  background: #5b6477;
}

.product-card__body {
  flex: 1;
  min-width: 0;
}

.product-card__meta {
  margin: 0;
  display: flex;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-card__name {
  margin: 2px 0 4px;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 2.6em;
}

.product-card__price {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.product-card__actions {
  display: flex;
  justify-content: center;
}

.product-card__add {
  width: 100%;
  border-radius: 999px;
  min-height: 40px;
}

.product-card__add svg {
  width: 16px;
  height: 16px;
  stroke: currentColor;
  stroke-width: 2.6;
  stroke-linecap: round;
}
</style>
