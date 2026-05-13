import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:5000/api",
  headers: { "Content-Type": "application/json" },
});

export default {
  // Generic passthrough — used by reusable components like BarChart
  get: (endpoint, config) => api.get(endpoint, config),

  // Health
  health: () => api.get("/health"),

  // Items
  getItems: () => api.get("/items"),
  getItem: (id) => api.get(`/items/${id}`),
  createItem: (data) => api.post("/items", data),
  deleteItem: (id) => api.delete(`/items/${id}`),

  // Charts
  getData:   (params) => api.get("/chart-data",         { params }),
  getRegionData:  ()       => api.get("/chart-data/regions"),
  getProductData: ()       => api.get("/chart-data/products"),
};