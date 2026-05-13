<template>
  <div class="threshold-slider" :class="{ 'ts-disabled': isDisabled }">

    <!-- Header: label + live value badge -->
    <div class="ts-header">
      <span class="ts-label">{{ label }}</span>
      <span class="ts-badge">
        <span class="ts-value">{{ formattedValue }}</span>
        <span v-if="unit" class="ts-unit">&nbsp;{{ unit }}</span>
      </span>
    </div>

    <!-- Slider -->
    <div class="ts-track-wrapper">
      <input
        type="range"
        class="ts-range"
        :min="min"
        :max="max"
        :step="step"
        :value="internal"
        :disabled="isDisabled"
        @input="internal = Number($event.target.value)"
        @change="emit('update:modelValue', internal)"
      />
      <!-- Filled portion behind the thumb -->
      <div class="ts-fill" :style="{ width: fillPct + '%' }"></div>
    </div>

    <!-- Min / max labels -->
    <div class="ts-bounds">
      <span class="ts-bound-label">{{ formatNum(min) }}<span v-if="unit" class="ts-unit-sm">&thinsp;{{ unit }}</span></span>
      <span class="ts-bound-label">{{ formatNum(max) }}<span v-if="unit" class="ts-unit-sm">&thinsp;{{ unit }}</span></span>
    </div>

    <p v-if="isDisabled" class="ts-empty">No chart data loaded yet</p>

  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";

const props = defineProps({
  /** Lower bound — derived from chart data min */
  min:        { type: Number, default: 0 },
  /** Upper bound — derived from chart data max */
  max:        { type: Number, default: 100 },
  /** Slider step size */
  step:       { type: Number, default: 1 },
  /** v-model value */
  modelValue: { type: Number, default: null },
  /** Descriptive label shown above the slider */
  label:      { type: String, default: "Threshold" },
  /** Optional unit string appended to the value */
  unit:       { type: String, default: "" },
  /** Decimal places for value display (auto-derived from step if omitted) */
  decimals:   { type: Number, default: null },
});

const emit = defineEmits(["update:modelValue"]);

// Internal ref owns the drag state — avoids Vue resetting the DOM value mid-drag
const internal = ref(props.modelValue ?? props.min);

// Parent resets the value (e.g. new chart data loaded) → sync inward
watch(() => props.modelValue, (v) => { if (v !== null) internal.value = v; });

const isDisabled = computed(() => props.min >= props.max);

const effectiveDecimals = computed(() => {
  if (props.decimals !== null) return props.decimals;
  // Infer from step: step=0.1 → 1 decimal, step=0.01 → 2, step=1 → 0
  const s = String(props.step);
  const dot = s.indexOf(".");
  return dot === -1 ? 0 : s.length - dot - 1;
});

function formatNum(n) {
  return Number(n).toLocaleString(undefined, {
    minimumFractionDigits: effectiveDecimals.value,
    maximumFractionDigits: effectiveDecimals.value,
  });
}

const formattedValue = computed(() =>
  props.modelValue === null ? "—" : formatNum(internal.value)
);

const fillPct = computed(() => {
  if (isDisabled.value || props.modelValue === null) return 0;
  return ((internal.value - props.min) / (props.max - props.min)) * 100;
});
</script>

<style scoped>
.threshold-slider {
  padding: 4px 2px;
}

/* ── Header ──────────────────────────────────────────────── */

.ts-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.ts-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #495057;
}

.ts-badge {
  display: inline-flex;
  align-items: baseline;
  background: #4285F4;
  color: #fff;
  border-radius: 20px;
  padding: 3px 12px;
  font-weight: 700;
  font-size: 0.95rem;
  min-width: 80px;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(66, 133, 244, 0.3);
}

.ts-unit {
  font-size: 0.72rem;
  font-weight: 500;
  opacity: 0.85;
}

/* ── Track ───────────────────────────────────────────────── */

.ts-track-wrapper {
  position: relative;
  height: 6px;
  margin: 14px 0 8px;
}

/* Background track — sits behind the fill and thumb */
.ts-track-wrapper::before {
  content: "";
  position: absolute;
  inset: 0;
  background: #dee2e6;
  border-radius: 3px;
}

/* Blue filled portion (left of thumb) */
.ts-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #4285F4;
  border-radius: 3px;
  pointer-events: none;
  transition: width 0.05s;
}

/* Native range input — transparent track, styled thumb */
.ts-range {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  opacity: 1;
  background: transparent;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
  z-index: 1;
}

.ts-range:focus {
  outline: none;
}

/* Thumb — Webkit */
.ts-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  border: 2.5px solid #4285F4;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  cursor: grab;
  margin-top: -7px;
  transition: box-shadow 0.15s, transform 0.1s;
}

.ts-range::-webkit-slider-thumb:hover,
.ts-range:active::-webkit-slider-thumb {
  box-shadow: 0 0 0 5px rgba(66, 133, 244, 0.18);
  transform: scale(1.12);
  cursor: grabbing;
}

/* Thumb — Firefox */
.ts-range::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  border: 2.5px solid #4285F4;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  cursor: grab;
  transition: box-shadow 0.15s, transform 0.1s;
}

.ts-range::-moz-range-thumb:hover {
  box-shadow: 0 0 0 5px rgba(66, 133, 244, 0.18);
}

/* Webkit track (must be transparent — our custom divs provide the visuals) */
.ts-range::-webkit-slider-runnable-track {
  background: transparent;
  height: 6px;
}

.ts-range::-moz-range-track {
  background: transparent;
  height: 6px;
}

/* ── Bounds ──────────────────────────────────────────────── */

.ts-bounds {
  display: flex;
  justify-content: space-between;
}

.ts-bound-label {
  font-size: 0.72rem;
  color: #868e96;
  font-weight: 500;
}

.ts-unit-sm {
  font-size: 0.68rem;
  color: #adb5bd;
}

/* ── Disabled state ──────────────────────────────────────── */

.ts-disabled .ts-range {
  cursor: not-allowed;
  opacity: 0.45;
}

.ts-disabled .ts-badge {
  background: #adb5bd;
  box-shadow: none;
}

.ts-empty {
  font-size: 0.78rem;
  color: #adb5bd;
  font-style: italic;
  margin: 6px 0 0;
  text-align: center;
}
</style>
