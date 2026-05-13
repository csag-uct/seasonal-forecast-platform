<template>
  <div class="month-slider">

    <!-- Labels row -->
    <div class="slider-labels" aria-hidden="true">
      <span
        v-for="(m, i) in MONTHS"
        :key="i"
        class="slider-label"
        :style="{ left: thumbLeft(i) + '%' }"
        :class="{
          'label-active': isIndexInRange(i),
          'label-start':  i === startIndex,
          'label-end':    i === endIndex,
        }"
      >{{ m.short }}</span>
    </div>

    <!-- Track -->
    <div
      ref="trackEl"
      class="slider-track"
      @mousedown="onTrackClick"
      @touchstart.passive="onTrackClick"
    >
      <!-- Filled range -->
      <div
        class="slider-fill"
        :style="{ left: fillLeft + '%', width: fillWidth + '%' }"
      ></div>

      <!-- Start handle -->
      <div
        class="slider-handle handle-start"
        :style="{ left: thumbLeft(startIndex) + '%' }"
        :class="{ 'handle-active': dragging === 'start' }"
        role="slider"
        :aria-valuenow="startMonth"
        :aria-valuemin="1"
        :aria-valuemax="12"
        :aria-label="`Start month: ${MONTHS[startIndex].long}`"
        tabindex="0"
        @mousedown.stop="startDrag('start', $event)"
        @touchstart.passive.stop="startDrag('start', $event)"
        @keydown="onKeydown('start', $event)"
      >
      <!--  REMOVING the handle label for now <span class="handle-label">{{ MONTHS[startIndex].short }}</span> -->
      </div>

      <!-- End handle -->
      <div
        class="slider-handle handle-end"
        :style="{ left: thumbLeft(endIndex) + '%' }"
        :class="{ 'handle-active': dragging === 'end' }"
        role="slider"
        :aria-valuenow="endMonth"
        :aria-valuemin="1"
        :aria-valuemax="12"
        :aria-label="`End month: ${MONTHS[endIndex].long}`"
        tabindex="0"
        @mousedown.stop="startDrag('end', $event)"
        @touchstart.passive.stop="startDrag('end', $event)"
        @keydown="onKeydown('end', $event)"
      >
      <!-- REMOVING the handle label for now   <span class="handle-label">{{ MONTHS[endIndex].short }}</span> -->
      </div>
    </div>

    <!-- Selected range summary -->
    <div class="slider-summary">
      <span class="summary-range">
        {{ MONTHS[startIndex].long }}
        <span class="summary-arrow">→</span>
        {{ MONTHS[endIndex].long }}
      </span>
      <span class="summary-count">
        {{ spanMonths }} month{{ spanMonths !== 1 ? 's' : '' }}
      </span>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from "vue";
import { useDateStore } from "../stores/dateStore";
import { useRangeStore } from "../stores/rangeStore";

const dateStore = useDateStore();
const rangeStore = useRangeStore();

// ── Month sequence: Jul → Dec → Jan → Jun (indices 0–17) ──────────────────
//   Slider position 0  = July    (calendar month 7)
//   Slider position 5  = December(calendar month 12)
//   Slider position 6  = January (calendar month 1)
//   Slider position 17 = June    (calendar month 6)

const MONTHS = [
  { short: "Jan", long: "January",   cal: 1  },
  { short: "Feb", long: "February",  cal: 2  },
  { short: "Mar", long: "March",     cal: 3  },
  { short: "Apr", long: "April",     cal: 4  },
  { short: "May", long: "May",       cal: 5  },
  { short: "Jun", long: "June",      cal: 6  },
  { short: "Jul", long: "July",      cal: 7  },
  { short: "Aug", long: "August",    cal: 8  },
  { short: "Sep", long: "September", cal: 9  },
  { short: "Oct", long: "October",   cal: 10 },
  { short: "Nov", long: "November",  cal: 11 },
  { short: "Dec", long: "December",  cal: 12 },
  { short: "Jan", long: "January",   cal: 1  },
  { short: "Feb", long: "February",  cal: 2  },
  { short: "Mar", long: "March",     cal: 3  },
  { short: "Apr", long: "April",     cal: 4  },
  { short: "May", long: "May",       cal: 5  },
  { short: "Jun", long: "June",      cal: 6  },
];

const TOTAL = MONTHS.length; // 12 positions, 11 gaps

// ── Props & emits ──────────────────────────────────────────────────────────

const props = defineProps({
  /** Initial start month (1–12, calendar). Defaults to July = 7 */
  modelStartMonth: { type: Number, default: 1 },
  /** Initial end month (1–12, calendar). Defaults to June = 6 */
  modelEndMonth:   { type: Number, default: 12 },
});

const emit = defineEmits([
  "update:startMonth",
  "update:endMonth",
  "change",           // fires { startMonth, endMonth } on every change
]);

// ── Internal state: slider indices (0–TOTAL-1) ────────────────────────────

function calToIndex(cal) {
  const i = MONTHS.findIndex((m) => m.cal === cal);
  return i === -1 ? 0 : i;
}

// Minimum start index driven by Yearmonthpicker's selected month
const minStartIndex = computed(() => calToIndex(dateStore.month));

const initStart = Math.max(calToIndex(props.modelStartMonth), calToIndex(dateStore.month));
const initEnd   = Math.min(Math.max(calToIndex(props.modelEndMonth), initStart), initStart + 5, TOTAL - 1);

const startIndex = ref(initStart);
const endIndex   = ref(initEnd);

// ── Public month values (1–12) ─────────────────────────────────────────────

const startMonth = computed(() => MONTHS[startIndex.value].cal);
const endMonth   = computed(() => MONTHS[endIndex.value].cal);

// ── Derived geometry ───────────────────────────────────────────────────────

/** Percent offset for a handle at slider index i */
function thumbLeft(i) {
  return (i / (TOTAL - 1)) * 100;
}

const fillLeft  = computed(() => thumbLeft(startIndex.value));
const fillWidth = computed(() => thumbLeft(endIndex.value) - thumbLeft(startIndex.value));

/** How many months are in the selected span */
const spanMonths = computed(() => endIndex.value - startIndex.value + 1);

function isIndexInRange(i) {
  return i >= startIndex.value && i <= endIndex.value;
}

// ── Drag handling ──────────────────────────────────────────────────────────

const trackEl = ref(null);
const dragging = ref(null); // 'start' | 'end' | null

function indexFromClientX(clientX) {
  const rect = trackEl.value.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
  return Math.round(ratio * (TOTAL - 1));
}

function clampedIndex(idx, handle) {
  if (handle === "start") return Math.max(minStartIndex.value, Math.min(endIndex.value, idx));
  return Math.max(startIndex.value, Math.min(startIndex.value + 5, TOTAL - 1, idx));
}

function applyIndex(handle, idx) {
  const clamped = clampedIndex(idx, handle);
  if (handle === "start") {
    startIndex.value = clamped;
    // Enforce 6-month cap: pull end back if start moved forward
    if (endIndex.value > startIndex.value + 5) {
      endIndex.value = startIndex.value + 5;
    }
  } else {
    endIndex.value = clamped;
  }
  emitValues();
}

function emitValues() {
  emit("update:startMonth", startMonth.value);
  emit("update:endMonth",   endMonth.value);
  emit("change", { startMonth: startMonth.value, endMonth: endMonth.value });
}

function startDrag(handle, evt) {
  dragging.value = handle;
  const moveEvt  = evt.type === "touchstart" ? "touchmove"  : "mousemove";
  const upEvt    = evt.type === "touchstart" ? "touchend"   : "mouseup";

  function onMove(e) {
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    applyIndex(handle, indexFromClientX(clientX));
  }

  function onUp() {
    dragging.value = null;
    window.removeEventListener(moveEvt, onMove);
    window.removeEventListener(upEvt,   onUp);
  }

  window.addEventListener(moveEvt, onMove);
  window.addEventListener(upEvt,   onUp);
}

/** Clicking the track jumps the nearest handle */
function onTrackClick(evt) {
  const clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
  const idx = indexFromClientX(clientX);
  const distStart = Math.abs(idx - startIndex.value);
  const distEnd   = Math.abs(idx - endIndex.value);
  const handle = distStart <= distEnd ? "start" : "end";
  applyIndex(handle, idx);
}

/** Keyboard navigation for accessibility */
function onKeydown(handle, evt) {
  const delta = { ArrowLeft: -1, ArrowRight: 1, ArrowDown: -1, ArrowUp: 1 }[evt.key];
  if (delta === undefined) return;
  evt.preventDefault();
  const current = handle === "start" ? startIndex.value : endIndex.value;
  applyIndex(handle, current + delta);
}

// Re-clamp when Yearmonthpicker changes its selected month
watch(minStartIndex, (minIdx) => {
  if (startIndex.value < minIdx) startIndex.value = minIdx;
  if (endIndex.value > startIndex.value + 5) endIndex.value = startIndex.value + 5;
  if (endIndex.value < startIndex.value) endIndex.value = startIndex.value;
  emitValues();
});

onBeforeUnmount(() => {
  // Safety: remove any lingering listeners
  window.removeEventListener("mousemove", () => {});
  window.removeEventListener("mouseup",   () => {});
});
</script>

<style scoped>
.month-slider {
  user-select: none;
  padding: 0 8px;
}

/* ── Label row ─────────────────────────────────────────────── */

.slider-labels {
  position: relative;
  height: 1.1rem;
  margin-bottom: 6px;
}

.slider-label {
  position: absolute;
  transform: translateX(-50%);
  font-size: 0.7rem;
  font-weight: 500;
  color: #adb5bd;
  letter-spacing: 0.03em;
  white-space: nowrap;
  transition: color 0.15s, font-weight 0.15s;
}

.slider-label.label-active {
  color: #495057;
}

.slider-label.label-start,
.slider-label.label-end {
  color: #4285F4;
  font-weight: 700;
}

/* ── Track ─────────────────────────────────────────────────── */

.slider-track {
  position: relative;
  height: 6px;
  background: #dee2e6;
  border-radius: 3px;
  cursor: pointer;
  margin: 18px 0 24px;
}

.slider-fill {
  position: absolute;
  top: 0;
  height: 100%;
  background: #4285F4;
  border-radius: 3px;
  pointer-events: none;
  transition: left 0.05s, width 0.05s;
}

/* ── Handles ───────────────────────────────────────────────── */

.slider-handle {
  position: absolute;
  top: 50%;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  border: 2.5px solid #4285F4;
  transform: translate(-50%, -50%);
  cursor: grab;
  transition: box-shadow 0.15s, border-color 0.15s, transform 0.1s;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.slider-handle:hover,
.slider-handle.handle-active {
  box-shadow: 0 0 0 5px rgba(66, 133, 244, 0.18);
  border-color: #1a6bf4;
  cursor: grabbing;
  transform: translate(-50%, -50%) scale(1.15);
}

.slider-handle:focus-visible {
  outline: none;
  box-shadow: 0 0 0 4px rgba(66, 133, 244, 0.35);
}

.handle-label {
  position: absolute;
  top: -22px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.65rem;
  font-weight: 700;
  color: #4285F4;
  white-space: nowrap;
  pointer-events: none;
  letter-spacing: 0.04em;
}

/* ── Summary ───────────────────────────────────────────────── */

.slider-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 2px;
}

.summary-range {
  font-size: 0.85rem;
  font-weight: 600;
  color: #212529;
}

.summary-arrow {
  margin: 0 6px;
  color: #4285F4;
}

.summary-count {
  font-size: 0.78rem;
  color: #6c757d;
  background: #f1f3f5;
  padding: 2px 8px;
  border-radius: 20px;
  font-weight: 500;
}
</style>