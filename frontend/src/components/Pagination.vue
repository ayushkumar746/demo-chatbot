<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['change'])

/** Page numbers with ellipses, e.g. [1, '…', 4, 5, 6, '…', 20] */
const pages = computed(() => {
  const total = props.totalPages
  const current = props.page
  if (total <= 7) return Array.from({ length: total }, (_, index) => index + 1)

  const items = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  if (start > 2) items.push('start-gap')
  for (let number = start; number <= end; number += 1) items.push(number)
  if (end < total - 1) items.push('end-gap')
  items.push(total)
  return items
})

function go(target) {
  if (!props.disabled && target >= 1 && target <= props.totalPages && target !== props.page) emit('change', target)
}
</script>

<template>
  <nav v-if="totalPages > 1" class="pagination" aria-label="Product pages">
    <button type="button" class="pagination__nav" :disabled="disabled || page <= 1" @click="go(page - 1)">
      <span aria-hidden="true">←</span> <span class="pagination__nav-label">Previous</span>
    </button>

    <ul class="pagination__pages">
      <li v-for="item in pages" :key="item">
        <span v-if="typeof item === 'string'" class="pagination__gap" aria-hidden="true">…</span>
        <button
          v-else
          type="button"
          class="pagination__page"
          :class="{ 'pagination__page--active': item === page }"
          :aria-current="item === page ? 'page' : undefined"
          :aria-label="`Page ${item}`"
          :disabled="disabled"
          @click="go(item)"
        >
          {{ item }}
        </button>
      </li>
    </ul>

    <span class="pagination__compact" aria-live="polite">Page {{ page }} of {{ totalPages }}</span>

    <button type="button" class="pagination__nav" :disabled="disabled || page >= totalPages" @click="go(page + 1)">
      <span class="pagination__nav-label">Next</span> <span aria-hidden="true">→</span>
    </button>
  </nav>
</template>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination__pages {
  display: flex;
  gap: 4px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.pagination__nav,
.pagination__page {
  min-width: 40px;
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-weight: 600;
  transition: background var(--transition), border-color var(--transition), color var(--transition);
}

.pagination__nav:hover:not(:disabled),
.pagination__page:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.pagination__nav:disabled {
  opacity: 0.45;
}

.pagination__page--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.pagination__page--active:hover:not(:disabled) {
  color: #fff;
}

.pagination__gap {
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 40px;
  color: var(--color-text-muted);
}

.pagination__compact {
  display: none;
  font-weight: 600;
  color: var(--color-text-muted);
}

@media (max-width: 560px) {
  .pagination__pages {
    display: none;
  }

  .pagination__compact {
    display: inline;
  }

  .pagination__nav-label {
    display: none;
  }
}
</style>
