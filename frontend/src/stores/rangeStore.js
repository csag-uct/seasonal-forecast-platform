import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useRangeStore = defineStore("range", () => {
  const now = new Date();

  // State — defaults to the current year and month
  const startMonth = ref(now.getMonth() + 1); // 1–12
  const endMonth = ref(startMonth.value + 3 > 12 ? startMonth.value + 3 - 12 : startMonth.value + 3);


  // Actions
  function setStartMonth(m)  { startMonth.value  = m; }
  function setEndMonth(m) { endMonth.value = m; }
  function set(a, b)   { startMonth.value = a; endMonth.value = b; }

  return { startMonth, endMonth, setStartMonth, setEndMonth, set };
});