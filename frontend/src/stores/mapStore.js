import { defineStore } from "pinia";
import { ref } from "vue";

export const useMapStore = defineStore("map", () => {
  const featureId = ref(null);
  const lat = ref(null);
  const lon = ref(null);

  function setSelection({ id, lat: newLat, lon: newLon }) {
    featureId.value = id;
    lat.value = newLat;
    lon.value = newLon;
  }

  function clearSelection() {
    featureId.value = null;
    lat.value = null;
    lon.value = null;
  }

  return { featureId, lat, lon, setSelection, clearSelection };
});