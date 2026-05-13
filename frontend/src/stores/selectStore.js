import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useSelectStore = defineStore("select", () => {
  
  const now = new Date();

  // State — defaults to the current year and month
  const initYear  = ref(now.getFullYear());
  const initMonth = ref(now.getMonth() + 1); // 1–12

  // State — defaults to the current month and current month + 3
  const startMonth = ref(now.getMonth() + 1); // 1–12
  const endMonth = ref(startMonth+3);

  // Wrap end month past 12
  if (endMonth.value > 12) { endMonth.value -= 12;}

  // Actions
  function setInitMonth(m)   {  initMonth.value = m; }
  function setInitYear(y)    {  initYear.value = y; }
  function setStartMonth(m)  { startMonth.value  = m; }
  function setEndMonth(m) { endMonth.value = m; }

  // Convenience getters
  const initMonthName = computed(() => {
    return new Date(initYear.value, initMonth.value - 1, 1)
      .toLocaleString("default", { month: "long" });
  });

  // Convenience getters
  const startMonthName = computed(() => {
    return new Date(initYear.value, startMonth.value - 1, 1)
      .toLocaleString("default", { month: "long" });
  });

  // Convenience getters
  const endMonthName = computed(() => {
    return new Date(initYear.value, endMonth.value - 1, 1)
      .toLocaleString("default", { month: "long" });
  });

  const thresholdValue = ref(null);
  function setThreshold(v) { thresholdValue.value = v; }

  function reset() {
    const now = new Date();

    initYear.value = now.getFullYear();
    initMonth.value = now.getMonth() + 1;
    startMonth.value = initMonth.value;
    endMonth.value = startMonth.value + 3;

    // Wrap end month past 12
    if (endMonth.value > 12) { endMonth.value -= 12;}
  }

  return { startMonth, endMonth, thresholdValue, setInitMonth, setInitYear, setStartMonth, setEndMonth, setThreshold, initMonthName, startMonthName, endMonthName };

});
