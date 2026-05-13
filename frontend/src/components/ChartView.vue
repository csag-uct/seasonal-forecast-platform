<template>
  <div>
    <!--<p class="text-muted mb-4">Plotly bar charts fed from Flask API endpoints.</p>-->

    <!-- Category filter — passed as a param to the component -->
    <!--
    <div class="mb-4 d-flex align-items-center gap-2">
      <label class="form-label mb-0 text-muted small fw-semibold">Category</label>
      <select v-model="variable" class="form-select form-select-sm w-auto">
        <option value="PRCPTOT">Rainfall</option>
        <option value="TG">Temperature</option>
      </select>
    </div>
    -->

    <div class="row g-4">

      <template v-if="showRangeSlider">
        <div class="col-12">
          <MonthRangeSlider
            v-model:startMonth="startMonth"
            v-model:endMonth="endMonth"
          />
        </div>
      </template>

      <!-- Main chart — reacts to the category dropdown -->
      <div class="col-12">
            <BarChart
              :title="props.title"
              subtitle="Fetched live from /api/chart-data"
              :endpoint="endpoint"
              :id="mapStore.featureId"
              :params="params"
              color="#4285F4"
              x-label="Year"
              :y-label="selectedCategory"
              @range="onChartRange"
            />
      </div>



      <template v-if="showThresholdSelector">
        <div class="col-12">
          <div class="mt-4 px-1">
              <ThresholdSlider
                v-model="thresholdValue"
                :min="chartMin"
                :max="chartMax"
                label="Threshold"
                :unit="selectedCategory"
              />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import BarChart from "../components/BarChart.vue";
import MonthRangeSlider  from "../components/MonthRangeSlider.vue";
import ThresholdSlider from "../components/ThresholdSlider.vue";

import { useMapStore } from "../stores/mapStore";
import { useRangeStore } from "../stores/rangeStore";
import { useDateStore } from "../stores/dateStore";
import { useSelectStore } from "../stores/selectStore";

import { watch } from "vue";

// Props
const props = defineProps({
  title: { type: String, default: "" },
  timeAgg: { type: String, default: "annual"},
  showRangeSlider: { type: Boolean, default: false },
  showThresholdSelector: { type: Boolean, default: false },
});


const mapStore = useMapStore();
const dateStore = useDateStore();
const rangeStore = useRangeStore();
const selectStore = useSelectStore();

const collection = "observed";
const dataset = "PRCPTOT_mon_CHC_CHIRPS-2.0-0p25_198101-202312_epsg102113";
const variable = ref("PRCPTOT");
const id = ref(mapStore.featureId);

const agg = ref("sum");

console.log('chartview');
console.log(dateStore.month);
console.log(variable.value);
console.log(mapStore.featureId);

// Season filter state — calendar months 1–12
const startMonth = ref(dateStore.month); // July
const endMonth   = ref(dateStore.month+3); // June (full year default)
 
const MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November", "December"];
const monthName = (m) => MONTH_NAMES[m] ?? "";

const CATEGORY_LABELS = { PRCPTOT: "Rainfall (mm)", TG: "Temperature (°C)" };
const selectedCategory = computed(() => CATEGORY_LABELS[variable.value] ?? variable.value);

const endpoint = ref("data/" + collection + "/" + dataset + "/" + variable.value + "/");

// Stable object reference: only changes when actual param values change,
// not on every ChartView re-render (which would spuriously re-trigger BarChart's watch).
const params = computed(() => ({
  agg: agg.value,
  timeagg: props.timeAgg,
  startmonth: startMonth.value,
  endmonth: endMonth.value,
}));

// ThresholdSlider state — populated when BarChart emits its data range
const chartMin       = ref(0);
const chartMax       = ref(0);
const thresholdValue = ref(null);

function onChartRange({ min, max }) {
  chartMin.value = min;
  chartMax.value = max;
  thresholdValue.value = Math.round((min + max) / 2);
  selectStore.setThreshold(thresholdValue.value);
}

watch(thresholdValue, (v) => selectStore.setThreshold(v));

watch(startMonth, (v) => rangeStore.setStartMonth(v));
watch(endMonth,   (v) => rangeStore.setEndMonth(v));
</script>