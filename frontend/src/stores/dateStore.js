import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useDateStore = defineStore("date", () => {
  const now = new Date();

  // State — defaults to the current year and month
  const year  = ref(now.getFullYear());
  const month = ref(now.getMonth() + 1); // 1–12

  // Convenience getters
  const monthName = computed(() => {
    return new Date(year.value, month.value - 1, 1)
      .toLocaleString("default", { month: "long" });
  });

  const label = computed(() => `${monthName.value} ${year.value}`);

  // Actions
  function setYear(y)  { year.value  = y; }
  function setMonth(m) { month.value = m; }
  function set(y, m)   { year.value = y; month.value = m; }

  function reset() {
    const n = new Date();
    year.value  = n.getFullYear();
    month.value = n.getMonth() + 1;
  }

  return { year, month, monthName, label, setYear, setMonth, set, reset };
});