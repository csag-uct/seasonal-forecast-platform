<template>
  <div class="feature-data-panel">

    <!-- No feature selected -->
    <div v-if="!featureId" class="fdp-empty">
      <p class="fdp-empty-text">Select a hexagon on the map to see results</p>
    </div>

    <template v-else>

    <p>This amount of rainfall was not met {{ result.obs_below}} times over the past {{ result.obs_below + result.obs_above }} years which is {{ result.obs_percentile }}% of the time.
    </p>

    <h3>Less than {{ result.obs_threshold }}: {{ result.obs_percentile }}% of the time</h3>

    <p>This also means that this amount of rainfall was met {{ result.obs_above}} times over the past {{ result.obs_below + result.obs_above }} years which is {{ 100.0 - result.obs_percentile }}% of the time.
    </p>

    <h3>So will {{ result.obs_threshold }} mm of rainfall be received for the coming period?</h3>

    <p>The forecast says that there is a {{ result.fcst_prob_above }}% probability of this occuring and {{ result.fcst_prob_below }}% probability of it not occuring.</p>

    <h3>Historical accuracy of the forecast</h3>
    <p>Consider that the forecast is never perfect and this is one of many forecasts.</p>
    <p>To help you interpret the numbers above and to build an appropriate level of confidence in the forecast, let us
    look at what happened in the past.</p>
    <p>Over the so {{ result.hits + result.misses }} years of historical data, the forecast (for this amount and this period) was:</p>
    <p>Correct {{ result.hits }} times.  i.e. forecast matched what actually happened</p>
    <p>Incorrect {{ result.misses }} times.  i.e. forecast was wrong (predicted one thing, observed another)</p>
    
    </template>

  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import api from "../api";
import { useMapStore } from "../stores/mapStore";
import { useDateStore } from "../stores/dateStore";
import { useRangeStore } from "../stores/rangeStore";
import { useSelectStore } from "../stores/selectStore";

const mapStore    = useMapStore();
const dateStore   = useDateStore();
const rangeStore  = useRangeStore();
const selectStore = useSelectStore();

const initYear = computed(() => dateStore.year);
const initMonth = computed(() => dateStore.month);

const startMonth = computed(() => rangeStore.startMonth);
const endMonth = computed(() => rangeStore.endMonth);

const featureId = computed(() => mapStore.featureId);
const threshold = computed(() => selectStore.thresholdValue);

const thresholdDisplay = computed(() =>
  threshold.value === null ? "—" : threshold.value
);

const loading = ref(false);
const error   = ref("");
const result  = ref(null);

async function fetchData() {
  if (!featureId.value) return;
  loading.value = true;
  error.value   = "";
  result.value  = null;
  try {
    const { data } = await api.get(`/forecast/ecmwf/${initYear.value}/${initMonth.value}/pr/${featureId.value}`, {
      params: { 
        obs_threshold: threshold.value, 
        lead: `${startMonth.value - initMonth.value},${endMonth.value - initMonth.value}`, 
      }
    });
    result.value = data;
  } catch (e) {
    // Dummy fallback so the UI is demonstrable before the endpoint exists
    if (e.response?.status === 404 || e.code === "ERR_NETWORK" || e.response?.status === 500) {
      result.value = data;
    } else {
      error.value = e.response?.data?.error ?? e.message ?? "Unknown error";
    }
  } finally {
    loading.value = false;
  }
  console.log(result.value);
}

function buildDummyResult(id, thresh) {
  const seed   = Number(String(id).replace(/\D/g, "").slice(-4)) || 1234;
  const years  = Array.from({ length: 10 }, (_, i) => 2014 + i);
  const values = years.map((y) => Math.round(((seed * (y % 13 + 1) * 7) % 800) + 100));
  const t      = thresh ?? 400;
  return {
    mean:         Math.round(values.reduce((a, b) => a + b, 0) / values.length),
    max:          Math.max(...values),
    years_above:  values.filter((v) => v >= t).length,
    years_below:  values.filter((v) => v < t).length,
    records:      years.map((year, i) => ({ year, value: values[i] })),
  };
}

// Re-fetch whenever the selected feature or threshold changes
watch(featureId, fetchData);
watch(threshold, () => { if (featureId.value) fetchData(); });
</script>

<style scoped>
.feature-data-panel {
  font-size: 0.875rem;
}

/* ── Empty state ──────────────────────────────────────────── */

.fdp-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #adb5bd;
  gap: 10px;
}

.fdp-empty-icon {
  font-size: 2rem;
}

.fdp-empty-text {
  margin: 0;
  font-style: italic;
}

/* ── Header ───────────────────────────────────────────────── */

.fdp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  gap: 8px;
  flex-wrap: wrap;
}

.fdp-title {
  font-weight: 600;
  color: #212529;
  margin-right: 10px;
}

.fdp-id {
  font-size: 0.78rem;
  background: #f1f3f5;
  padding: 1px 6px;
  border-radius: 4px;
  color: #495057;
}

.fdp-threshold-pill {
  display: inline-block;
  font-size: 0.75rem;
  color: #6c757d;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 20px;
  padding: 2px 10px;
}

.fdp-refresh-btn {
  background: none;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  width: 30px;
  height: 30px;
  cursor: pointer;
  font-size: 1rem;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.fdp-refresh-btn:hover:not(:disabled) {
  background: #f1f3f5;
}

.fdp-spin {
  display: inline-block;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Loading ──────────────────────────────────────────────── */

.fdp-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #6c757d;
  padding: 20px 0;
}

.fdp-spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid #dee2e6;
  border-top-color: #4285F4;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* ── Summary metrics ──────────────────────────────────────── */

.fdp-meta {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.fdp-meta-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.fdp-meta-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #adb5bd;
  font-weight: 600;
}

.fdp-meta-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #212529;
}

/* ── Records table ────────────────────────────────────────── */

.fdp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

.fdp-table th {
  text-align: left;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #adb5bd;
  font-weight: 600;
  padding: 4px 8px 6px;
  border-bottom: 1px solid #dee2e6;
}

.fdp-table td {
  padding: 5px 8px;
  border-bottom: 1px solid #f1f3f5;
  color: #495057;
}

.fdp-row-above td { background: rgba(66, 133, 244, 0.04); }
.fdp-row-below td { background: transparent; }

.fdp-status-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 10px;
}

.fdp-above {
  background: rgba(66, 133, 244, 0.12);
  color: #1a6bf4;
}

.fdp-below {
  background: rgba(108, 117, 125, 0.1);
  color: #6c757d;
}
</style>
