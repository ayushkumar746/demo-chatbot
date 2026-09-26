<script setup>
import { storeToRefs } from 'pinia'
import ProductImage from './ProductImage.vue'
import QuantityControl from './QuantityControl.vue'
import { useCartStore } from '../stores/cart.js'
import { MAX_QUANTITY_PER_ITEM } from '../config.js'
import { formatPrice } from '../utils/format.js'

const cart = useCartStore()
const { items, itemCount, totalPrice, error, isSyncing, loading } = storeToRefs(cart)
</script>

<template>
  <section id="cart" class="cart card" aria-labelledby="cart-heading">
    <header class="cart__header">
      <h2 id="cart-heading">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 2-1.5L21 8H6" />
          <circle cx="10" cy="20" r="1.4" /><circle cx="17" cy="20" r="1.4" />
        </svg>
        Cart
      </h2>
      <span class="cart__count" aria-live="polite">
        {{ itemCount }} {{ itemCount === 1 ? 'item' : 'items' }}
        <span v-if="isSyncing" class="cart__syncing">· saving…</span>
      </span>
    </header>

    <p v-if="error" class="cart__error" role="alert">
      {{ error }}
      <button type="button" aria-label="Dismiss" @click="cart.clearError()">×</button>
    </p>

    <p v-if="loading && !items.length" class="cart__empty">Loading your cart…</p>
    <p v-else-if="!items.length" class="cart__empty">
      Your cart is empty. Add products from the list or ask the assistant.
    </p>

    <TransitionGroup v-else tag="ul" name="cart-line" class="cart__items">
      <li v-for="item in items" :key="item.product_id" class="cart__item">
        <ProductImage :src="item.image_url" :name="item.name" size="sm" />
        <div class="cart__item-info">
          <p class="cart__item-name" :title="item.name">{{ item.name }}</p>
          <p class="cart__item-price">{{ formatPrice(item.price) }} × {{ item.quantity }}</p>
        </div>
        <div class="cart__item-actions">
          <strong>{{ formatPrice(item.total_price) }}</strong>
          <QuantityControl
            compact
            :quantity="item.quantity"
            :max="MAX_QUANTITY_PER_ITEM"
            :label="item.name"
            @increment="cart.increment(item)"
            @decrement="cart.decrement(item)"
          />
        </div>
      </li>
    </TransitionGroup>

    <footer v-if="items.length" class="cart__footer">
      <span>Total</span>
      <strong class="cart__total">{{ formatPrice(totalPrice) }}</strong>
    </footer>
  </section>
</template>

<style scoped>
.cart {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 14px 16px;
  scroll-margin-top: calc(var(--header-height) + 12px);
}

.cart__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

h2 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
}

h2 svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.cart__count {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.cart__syncing {
  color: var(--color-primary);
}

.cart__error {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin: 10px 0 0;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: 13px;
}

.cart__error button {
  border: none;
  background: none;
  color: inherit;
  font-size: 16px;
  line-height: 1;
}

.cart__empty {
  margin: 12px 0 4px;
  color: var(--color-text-muted);
  font-size: 14px;
}

.cart__items {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
  overflow-y: auto;
  min-height: 0;
}

.cart__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-top: 1px solid var(--color-border);
}

.cart__item:first-child {
  border-top: none;
}

.cart__item-info {
  flex: 1;
  min-width: 0;
}

.cart__item-info p {
  margin: 0;
}

.cart__item-name {
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cart__item-price {
  font-size: 13px;
  color: var(--color-text-muted);
}

.cart__item-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  font-size: 14px;
}

.cart__footer {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-top: 8px;
  padding-top: 10px;
  border-top: 2px dashed var(--color-border);
  font-weight: 600;
}

.cart__total {
  font-size: 20px;
}

.cart-line-enter-active,
.cart-line-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}

.cart-line-enter-from,
.cart-line-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>
