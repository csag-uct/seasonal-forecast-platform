<template>
  <div class="ym-picker">

    <!-- Year row -->
    <div class="ym-row">
      <button
        class="ym-step-btn"
        @click="stepYear(-1)"
        :disabled="year <= minYear"
        aria-label="Previous year"
      >‹</button>

      <div class="ym-year-display">
        <span class="ym-year-value">{{ year }}</span>
        <span class="ym-year-label">year</span>
      </div>

      <button
        class="ym-step-btn"
        @click="stepYear(1)"
        :disabled="year >= maxYear"
        aria-label="Next year"
      >›</button>
    </div>

    <!-- Month grid -->
    <div class="ym-month-grid">
      <button
        v-for="m in MONTHS"
        :key="m.num"
        class="ym-month-btn"
        :class="{
          'is-selected': m.num === month,
          'is-current':  m.num === currentMonth && year === currentYear,
          'is-future':   isFuture(m.num),
        }"
        :disabled="isFuture(m.num)"
        @click="selectMonth(m.num)"
        :aria-label="m.long"
        :aria-pressed="m.num === month"
      >
        {{ m.short }}
      </button>
    </div>

    <!-- Footer: selected label + reset -->
    <div class="ym-footer">
      <span class="ym-label">{{ dateStore.label }}</span>
      <button
        v-if="!isCurrentMonthYear"
        class="ym-reset-btn"
        @click="reset"
        title="Reset to today"
      >
        ↺ Today
      </button>
    </div>

  </div>
</template>

<script setup>
import { computed } from "vue";
import { useDateStore } from "../stores/dateStore";

const dateStore = useDateStore();

// ── Config ────────────────────────────────────────────────────────────────────

const now          = new Date();
const currentYear  = now.getFullYear();
const currentMonth = now.getMonth() + 1;
const minYear      = currentYear - 10;
const maxYear      = currentYear;     // no future years

const MONTHS = [
  { num: 1,  short: "Jan", long: "January"   },
  { num: 2,  short: "Feb", long: "February"  },
  { num: 3,  short: "Mar", long: "March"     },
  { num: 4,  short: "Apr", long: "April"     },
  { num: 5,  short: "May", long: "May"       },
  { num: 6,  short: "Jun", long: "June"      },
  { num: 7,  short: "Jul", long: "July"      },
  { num: 8,  short: "Aug", long: "August"    },
  { num: 9,  short: "Sep", long: "September" },
  { num: 10, short: "Oct", long: "October"   },
  { num: 11, short: "Nov", long: "November"  },
  { num: 12, short: "Dec", long: "December"  },
];

// ── Store accessors ───────────────────────────────────────────────────────────

const year  = computed(() => dateStore.year);
const month = computed(() => dateStore.month);

const isCurrentMonthYear = computed(
  () => year.value === currentYear && month.value === currentMonth
);

/** Returns true if the given calendar month is in the future relative to today */
function isFuture(m) {
  return year.value === currentYear && m > currentMonth;
}

// ── Actions ───────────────────────────────────────────────────────────────────

function stepYear(delta) {
  const next = year.value + delta;
  if (next >= minYear && next <= maxYear) {
    dateStore.setYear(next);
    // If the newly selected year is the current year and the stored month is
    // now in the future, clamp it back to the current month.
    if (next === currentYear && dateStore.month > currentMonth) {
      dateStore.setMonth(currentMonth);
    }
  }
}

function selectMonth(m) {
  if (!isFuture(m)) dateStore.setMonth(m);
}

function reset() {
  dateStore.reset();
}
</script>

<style scoped>
.ym-picker {
  display: inline-flex;
  flex-direction: column;
  gap: 12px;
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 10px;
  padding: 16px;
  min-width: 240px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* ── Year row ──────────────────────────────────────────────── */

.ym-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ym-step-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #dee2e6;
  background: #f8f9fa;
  color: #495057;
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.ym-step-btn:hover:not(:disabled) {
  background: #e9ecef;
  border-color: #adb5bd;
}

.ym-step-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.ym-year-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1;
}

.ym-year-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: #212529;
  letter-spacing: -0.5px;
}

.ym-year-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #adb5bd;
  margin-top: 1px;
}

/* ── Month grid ────────────────────────────────────────────── */

.ym-month-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 5px;
}

.ym-month-btn {
  padding: 6px 0;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 0.78rem;
  font-weight: 500;
  color: #495057;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
  text-align: center;
}

.ym-month-btn:hover:not(.is-selected) {
  background: #f1f3f5;
  border-color: #dee2e6;
}

/* Current month (today's month in today's year) — subtle ring */
.ym-month-btn.is-current:not(.is-selected) {
  border-color: #4285F4;
  color: #4285F4;
  font-weight: 600;
}

/* Future months — disabled, visually dimmed */
.ym-month-btn.is-future {
  color: #ced4da;
  cursor: not-allowed;
  background: transparent;
}

.ym-month-btn.is-future:hover {
  background: transparent;
  border-color: transparent;
}

/* Selected month */
.ym-month-btn.is-selected {
  background: #4285F4;
  color: #fff;
  border-color: #4285F4;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(66,133,244,0.3);
}

/* ── Footer ────────────────────────────────────────────────── */

.ym-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 4px;
  border-top: 1px solid #f1f3f5;
}

.ym-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: #212529;
}

.ym-reset-btn {
  font-size: 0.75rem;
  color: #6c757d;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background 0.12s, color 0.12s;
}

.ym-reset-btn:hover {
  background: #f1f3f5;
  color: #495057;
}
</style>