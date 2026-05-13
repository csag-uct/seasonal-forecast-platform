<template>
  <div class="barchart-wrapper">

    <!-- Header row: title + refresh button -->
    <div class="d-flex align-items-center justify-content-between mb-3">
      <div>
        <h5 class="mb-0">{{ title }}</h5>
        <p v-if="subtitle" class="text-muted small mb-0">{{ subtitle }}</p>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="error" class="alert alert-danger py-2 small">
      {{ error }}
    </div>

    <!-- Chart container — Plotly renders into this div -->
    <div ref="chartEl" class="chart-container"></div>

    <!-- Empty state (after load, no data) -->
    <div
      v-if="!loading && !error && isEmpty"
      class="text-center text-muted py-5"
    >
      No data returned from the API.
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
import Plotly from "plotly.js-dist-min";
import api from "../api";

// ── Props ─────────────────────────────────────────────────────────────────────

const props = defineProps({
  /** Title shown above the chart */
  title: { type: String, default: "Bar Chart" },

  /** Optional subtitle / description */
  subtitle: { type: String, default: "" },

  /**
   * API endpoint path relative to the base URL.
   * e.g. "/chart-data" → calls GET http://localhost:5000/api/chart-data
   */
  endpoint: { type: String, required: true },

  id: { type: String, required: true, default: "710" },

  /**
   * Optional static params appended as query string.
   * e.g. { category: "sales", year: 2024 }
   */
  params: { type: Object, default: () => ({}) },

  /** Plotly bar colour (CSS colour string) */
  color: { type: String, default: "#4285F4" },

  /** X-axis label */
  xLabel: { type: String, default: "" },

  /** Y-axis label */
  yLabel: { type: String, default: "" },
});

const emit = defineEmits(["range"]);

// ── State ─────────────────────────────────────────────────────────────────────

const chartEl = ref(null);   // template ref → Plotly mount point
const loading  = ref(false);
const error    = ref("");
const chartData = ref({ labels: [], values: [] });

const isEmpty = computed(
  () => !chartData.value.labels || chartData.value.labels.length === 0
);

// ── Plotly helpers ────────────────────────────────────────────────────────────

function buildTrace() {
  return {
    type: "bar",
    x: chartData.value.labels,
    y: chartData.value.values,
    marker: {
      color: props.color,
      opacity: 0.85,
      line: { color: props.color, width: 1 },
    },
    hovertemplate: "<b>%{x}</b><br>%{y}<extra></extra>",
  };
}

const layout = {
  margin: { t: 10, r: 20, b: 60, l: 60 },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor:  "rgba(0,0,0,0)",
  font: { family: "inherit", size: 13 },
  xaxis: {
    title: { text: props.xLabel, standoff: 12 },
    tickangle: -35,
    automargin: true,
    gridcolor: "#e9ecef",
  },
  yaxis: {
    title: { text: props.yLabel, standoff: 12 },
    gridcolor: "#e9ecef",
    zeroline: true,
    zerolinecolor: "#dee2e6",
  },
  bargap: 0.25,
};

const plotConfig = {
  responsive: true,
  displaylogo: false,
  modeBarButtonsToRemove: ["lasso2d", "select2d", "toImage"],
};

function renderChart() {
  if (!chartEl.value || isEmpty.value) return;
  Plotly.react(chartEl.value, [buildTrace()], layout, plotConfig);
}

// ── Data fetching ─────────────────────────────────────────────────────────────

async function fetchData() {
  console.log('fetchData');
  console.log(props.endpoint);
  loading.value = true;
  error.value   = "";
  try {
    const { data } = await api.get(props.endpoint + props.id, { params: props.params });

    // Expected API shape: { labels: [...], values: [...] }
    // Adapt here if your API returns a different shape.
    if (!data.labels || !data.values) {
      throw new Error('API response must include "labels" and "values" arrays.');
    }
    chartData.value = data;
    renderChart();
    if (data.values.length) {
      emit("range", { min: Math.min(...data.values), max: Math.max(...data.values) });
    }
  } catch (e) {
    error.value = e.response?.data?.error ?? e.message ?? "Unknown error";
  } finally {
    loading.value = false;
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(fetchData);

// Re-fetch if the endpoint or params prop changes at runtime
watch(() => [props.endpoint, props.id, props.params], fetchData, { deep: true });

// Clean up Plotly instance on unmount
onBeforeUnmount(() => {
  if (chartEl.value) Plotly.purge(chartEl.value);
});
</script>

<style scoped>
.chart-container {
  width: 100%;
  min-height: 320px;
}
</style>