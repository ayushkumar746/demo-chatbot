<script setup>
const props = defineProps({
  quantity: { type: Number, required: true },
  max: { type: Number, default: Infinity },
  label: { type: String, required: true }, // product name, for accessible labels
  disabled: { type: Boolean, default: false },
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['increment', 'decrement'])
</script>

<template>
  <div class="quantity" :class="{ 'quantity--compact': compact }" role="group" :aria-label="`Quantity of ${label}`">
    <button
      type="button"
      class="quantity__btn"
      :aria-label="quantity === 1 ? `Remove ${label} from cart` : `Decrease quantity of ${label}`"
      :disabled="disabled || props.quantity <= 0"
      @click="emit('decrement')"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 12h12" /></svg>
    </button>
    <output class="quantity__value" aria-live="polite">{{ quantity }}</output>
    <button
      type="button"
      class="quantity__btn"
      :aria-label="`Increase quantity of ${label}`"
      :disabled="disabled || props.quantity >= max"
      @click="emit('increment')"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 12h12M12 6v12" /></svg>
    </button>
  </div>
</template>

<style scoped>
.quantity {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  overflow: hidden;
}

.quantity__btn {
  width: 40px;
  height: 38px;
  display: grid;
  place-items: center;
  border: none;
  background: transparent;
  color: var(--color-primary);
  transition: background var(--transition);
  touch-action: manipulation;
}

.quantity__btn svg {
  width: 18px;
  height: 18px;
  stroke: currentColor;
  stroke-width: 2.4;
  stroke-linecap: round;
}

.quantity__btn:hover:not(:disabled) {
  background: var(--color-primary-soft);
}

.quantity__btn:disabled {
  color: #b6bccb;
}

.quantity__value {
  min-width: 28px;
  text-align: center;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.quantity--compact .quantity__btn {
  width: 32px;
  height: 30px;
}
</style>
