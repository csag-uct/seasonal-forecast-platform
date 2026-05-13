<template>
  <div>

    <div class="row align-items-start mb-4">
      <div class="col-md-8">
        <h2 class="fw-bold mb-1">Exploring forecast data</h2>
        <p>
        This page presents allows you to explore a seasonal forecast produced in <strong>{{ dateStore.monthName}} {{ dateStore.year }}</strong>.  You will be able to select a location, a period of the year, and a minimum or maximum requirement to
produce a personalised forecast.  
        </p>
      </div>
      <div class="col-md-4 d-flex justify-content-start">
        <YearMonthPicker />
      </div>
    </div>


    <!-- Map Section -->
        <h2 class="fw-bold mb-1">Map</h2>
        <p>
        Choose the location from which you would like to get seasonal forecast information. You can zoom in either by using the
plus (+) and minus (-) signs or using the zoom function on your device.
        </p>
        <MapView
          :center="[25.0, -29.0]"
          :zoom="5"
          @select="onMapSelect"
        />

        <!-- Selected feature as Vue model -->
        <div v-if="selectedHexId !== null" class="mt-3 p-3 bg-light rounded">
          <p class="mb-1 fw-semibold">Selected Feature (Vue model)</p>
          <div class="row g-2">
            <div class="col-sm-4">
              <label class="form-label text-muted small mb-1">Hex ID</label>
              <input class="form-control font-monospace" :value="selectedHexId" readonly />
            </div>
            <div class="col-sm-4">
              <label class="form-label text-muted small mb-1">Latitude</label>
              <input class="form-control font-monospace" :value="clickedLat?.toFixed(6)" readonly />
            </div>
            <div class="col-sm-4">
              <label class="form-label text-muted small mb-1">Longitude</label>
              <input class="form-control font-monospace" :value="clickedLon?.toFixed(6)" readonly />
            </div>
          </div>
        </div>

    <h2 class="fw-bold mb-1">Average Seasons</h2>
    <p>
    This seasonal chart shows the historical average rainfall per month for your chosen location. The data runs from 1981 to 2025,
you can get the monthly totals by hovering over the bars.<br/>
Does this relate with what you know about the location?
    </p>
    <ChartView
      title="Monthly averages"
      timeAgg="seasonal"
      :showRangeSlider="false"
      :showThresholdSelector="false"
    />


    <!--Chart -->
    <h2 class="fw-bold mb-1">Seasonal History</h2>
    <p>
    This seasonal chart shows the historical rainfall per season for your chosen location.  You can select the months of your season of interest using the sliders below.
    </p>
    <ChartView
      :showRangeSlider="true"
      :showThresholdSelector="true"
    />

    <!-- Feature Data Panel -->
    <div class="card border-0 shadow-sm mb-4">
      <div class="card-body">
        <h5 class="card-title mb-3">📊 Feature Analysis</h5>
        <FeatureDataPanel />
      </div>
    </div>

    <!-- API Health Check -->
    <div class="mt-4">
      <button class="btn btn-outline-secondary" @click="checkHealth" :disabled="loading">
        {{ loading ? "Checking…" : "Check API Health" }}
      </button>
      <span v-if="healthMsg" class="ms-3 badge" :class="healthOk ? 'bg-success' : 'bg-danger'">
        {{ healthMsg }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

import api from "../api";

import { useMapStore } from "../stores/mapStore";
import { useSelectStore } from "../stores/selectStore";
import { useDateStore } from "../stores/dateStore";


import YearMonthPicker from "../components/Yearmonthpicker.vue";
import MapView from "../components/MapView.vue";
import ChartView from "../components/ChartView.vue";
import FeatureDataPanel from "../components/FeatureDataPanel.vue";

const mapStore = useMapStore();
const selectStore = useSelectStore();
const dateStore = useDateStore();

console.log(selectStore.initMonth);

// Map selection state — these are the Vue model values
const selectedHexId = ref(null);
const clickedLat    = ref(null);
const clickedLon    = ref(null);

function onMapSelect({ id, lat, lon }) {
  selectedHexId.value = id;
  clickedLat.value    = lat;
  clickedLon.value    = lon;
  console.log('selectedHexID changed');
  console.log(mapStore.featureId);
}

// Health check
const loading = ref(false);
const healthMsg = ref("");
const healthOk = ref(false);

async function checkHealth() {
  loading.value = true;
  healthMsg.value = "";
  try {
    const { data } = await api.health();
    healthMsg.value = data.message;
    healthOk.value = true;
  } catch {
    healthMsg.value = "API unreachable";
    healthOk.value = false;
  } finally {
    loading.value = false;
  }
}
</script>
