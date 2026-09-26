<script setup>
const model = defineModel({ type: String, default: '' })

defineProps({
  placeholder: { type: String, default: 'Search products...' },
})
</script>

<template>
  <div class="search" role="search">
    <label for="product-search" class="visually-hidden">Search products by name, brand or category</label>
    <svg class="search__icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
    </svg>
    <input
      id="product-search"
      v-model="model"
      type="search"
      :placeholder="placeholder"
      autocomplete="off"
      maxlength="100"
    />
    <button v-if="model" type="button" class="search__clear" aria-label="Clear search" @click="model = ''">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
    </button>
  </div>
</template>

<style scoped>
.search {
  position: relative;
  display: flex;
  align-items: center;
}

.search__icon {
  position: absolute;
  left: 14px;
  width: 18px;
  height: 18px;
  fill: none;
  stroke: var(--color-text-muted);
  stroke-width: 2;
  stroke-linecap: round;
  pointer-events: none;
}

input {
  width: 100%;
  height: 46px;
  padding: 0 44px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--transition), box-shadow var(--transition);
}

input::-webkit-search-cancel-button {
  display: none;
}

input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-soft);
}

.search__clear {
  position: absolute;
  right: 8px;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: none;
  border-radius: 50%;
  background: transparent;
}

.search__clear:hover {
  background: var(--color-surface-muted);
}

.search__clear svg {
  width: 16px;
  height: 16px;
  stroke: var(--color-text-muted);
  stroke-width: 2.2;
  stroke-linecap: round;
}
</style>
