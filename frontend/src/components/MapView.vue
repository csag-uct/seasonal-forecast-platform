<template>
  <div class="map-wrapper">
    <div ref="mapEl" class="map-container"></div>

    <!-- Coordinate / feature display overlay -->
    <div class="map-overlay card border-0 shadow-sm">
      <div class="card-body py-2 px-3">
        <div class="d-flex align-items-center gap-3 flex-wrap">
          <template v-if="featureId !== null">
            <span class="badge bg-secondary font-monospace">
              {{ lat.toFixed(5) }}, {{ lon.toFixed(5) }}
            </span>
            <button class="btn btn-sm btn-outline-secondary py-0" @click="clearSelection">
              Clear
            </button>
          </template>
          <span v-else class="text-muted small fst-italic">
            Click a hexagon to select location
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import OSM from "ol/source/OSM";
import { Vector as VectorLayer } from "ol/layer";
import { Vector as VectorSource } from "ol/source";
import GeoJSON from "ol/format/GeoJSON";
import { Style, Fill, Stroke } from "ol/style";
import { fromLonLat, toLonLat } from "ol/proj";
import "ol/ol.css";

import { useMapStore } from "../stores/mapStore";

const mapStore = useMapStore();

// Props
const props = defineProps({
  // Map center in [lon, lat] WGS84 — defaults to South Africa
  center: { type: Array, default: () => [25.0, -29.0] },
  zoom:   { type: Number, default: 5 },
});

// Emits
const emit = defineEmits(["update:featureId", "update:lat", "update:lon", "select"]);

// Reactive state exposed to parent
const featureId = ref(null);
const lat        = ref(0);
const lon        = ref(0);

const mapEl = ref(null);
let map             = null;
let selectedFeature = null;

// ── Styles ──────────────────────────────────────────────────────────────────

const defaultStyle = new Style({
  fill:   new Fill({ color: "rgba(66, 133, 244, 0.15)" }),
  stroke: new Stroke({ color: "rgba(66, 133, 244, 0.7)", width: 1 }),
});

const hoverStyle = new Style({
  fill:   new Fill({ color: "rgba(66, 133, 244, 0.30)" }),
  stroke: new Stroke({ color: "rgba(66, 133, 244, 1)", width: 1.5 }),
});

const selectedStyle = new Style({
  fill:   new Fill({ color: "rgba(234, 67, 53, 0.35)" }),
  stroke: new Stroke({ color: "rgba(234, 67, 53, 1)", width: 2.5 }),
});

// ── Vector layer ─────────────────────────────────────────────────────────────
// The GeoJSON is in EPSG:102113 (== EPSG:3857 Web Mercator).
// Tell OpenLayers to read and display it in 3857 — no reprojection needed.
const vectorSource = new VectorSource({
  url:    "hexgrid.geojson",
  format: new GeoJSON({
    dataProjection:    "EPSG:3857",
    featureProjection: "EPSG:3857",
  }),
});

const vectorLayer = new VectorLayer({
  source: vectorSource,
  style:  defaultStyle,
});

// ── Mount ─────────────────────────────────────────────────────────────────────

onMounted(() => {
  map = new Map({
    target: mapEl.value,
    layers: [
      new TileLayer({ source: new OSM() }),
      vectorLayer,
    ],
    view: new View({
      center: fromLonLat(props.center),
      zoom:   props.zoom,
    }),
  });

  // ── Hover cursor + highlight ────────────────────────────────────────────
  let hoveredFeature = null;

  map.on("pointermove", (evt) => {
    if (evt.dragging) return;

    const hit = map.hasFeatureAtPixel(evt.pixel, {
      layerFilter: (l) => l === vectorLayer,
    });
    map.getTargetElement().style.cursor = hit ? "pointer" : "";

    // Reset previously hovered feature (unless it's the selected one)
    if (hoveredFeature && hoveredFeature !== selectedFeature) {
      hoveredFeature.setStyle(undefined);
      hoveredFeature = null;
    }

    if (hit) {
      map.forEachFeatureAtPixel(
        evt.pixel,
        (feature) => {
          if (feature !== selectedFeature) {
            feature.setStyle(hoverStyle);
            hoveredFeature = feature;
          }
          return true; // stop after first hit
        },
        { layerFilter: (l) => l === vectorLayer }
      );
    }
  });

  // ── Click — select feature ───────────────────────────────────────────────
  map.on("click", (evt) => {
    // Deselect previous
    if (selectedFeature) {
      selectedFeature.setStyle(undefined);
      selectedFeature = null;
    }

    let hit = false;

    map.forEachFeatureAtPixel(
      evt.pixel,
      (feature) => {
        hit = true;
        selectedFeature = feature;
        feature.setStyle(selectedStyle);

        const id     = String(feature.get("id"));
        const coords = toLonLat(evt.coordinate);

        featureId.value = id;
        lon.value        = coords[0];
        lat.value        = coords[1];

        mapStore.setSelection({ id: featureId.value, lat: lat.value, lon: lon.value });
        console.log('MapView');
        console.log(mapStore.featureId);

        emit("update:featureId", id);
        emit("update:lat",        coords[1]);
        emit("update:lon",        coords[0]);
        emit("select", { id, lat: coords[1], lon: coords[0] });

        return true; // stop after first hit
      },
      { layerFilter: (l) => l === vectorLayer }
    );

    // Clicked empty map area — clear selection
    if (!hit) clearSelection();
  });
});

onBeforeUnmount(() => {
  map?.setTarget(null);
});

// ── Helpers ───────────────────────────────────────────────────────────────────

function clearSelection() {
  if (selectedFeature) {
    selectedFeature.setStyle(undefined);
    selectedFeature = null;
  }
  featureId.value = null;
  lat.value        = 0;
  lon.value        = 0;
  emit("update:featureId", null);
  emit("update:lat",        null);
  emit("update:lon",        null);
}

defineExpose({ featureId, lat, lon });
</script>

<style scoped>
.map-wrapper {
  position: relative;
}

.map-container {
  width: 100%;
  height: 500px;
  border-radius: 0.5rem;
  overflow: hidden;
}

.map-overlay {
  position: absolute;
  bottom: 12px;
  left: 12px;
  right: 12px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
}
</style>
