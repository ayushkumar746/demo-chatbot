<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, default: '' },
  name: { type: String, required: true },
  category: { type: String, default: '' },
  size: { type: String, default: 'md' }, // md | sm
})

const failed = ref(false)
watch(() => props.src, () => { failed.value = false })

const initials = computed(() =>
  props.name.split(/\s+/).filter(Boolean).slice(0, 2).map((word) => word[0]).join('').toUpperCase(),
)

const FALLBACK_TINTS = {
  cold_drink: '#fdecec', energy_drink: '#e8f0fe', fruit_drink: '#fff3e0',
  water: '#e1f5fe', beer: '#fff8e1', wine: '#f3e5f5', snacks: '#fffde7',
}
const tint = computed(() => FALLBACK_TINTS[props.category] || '#eef0ff')
</script>

<template>
  <div class="product-image" :class="`product-image--${size}`">
    <img v-if="src && !failed" :src="src" :alt="name" loading="lazy" @error="failed = true" />
    <div v-else class="product-image__fallback" :style="{ background: tint }" role="img" :aria-label="name">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 7h12l-1.2 12.2a2 2 0 0 1-2 1.8H9.2a2 2 0 0 1-2-1.8L6 7Zm3 0V5a3 3 0 0 1 6 0v2" fill="none"
          stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <span>{{ initials }}</span>
    </div>
  </div>
</template>

<style scoped>
.product-image {
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-surface-muted);
}

.product-image--sm {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-image__fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 4px;
  color: var(--color-text-muted);
  font-weight: 700;
}

.product-image__fallback svg {
  width: 40%;
  max-width: 56px;
}

.product-image--sm .product-image__fallback span {
  display: none;
}
</style>
