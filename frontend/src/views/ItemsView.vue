<template>
  <div>
    <h2 class="mb-4 fw-bold">Items</h2>

    <!-- Add Item Form -->
    <div class="card border-0 shadow-sm mb-4">
      <div class="card-body">
        <h5 class="card-title">Add New Item</h5>
        <div class="row g-2">
          <div class="col-md-4">
            <input
              v-model="form.name"
              type="text"
              class="form-control"
              placeholder="Name *"
            />
          </div>
          <div class="col-md-5">
            <input
              v-model="form.description"
              type="text"
              class="form-control"
              placeholder="Description"
            />
          </div>
          <div class="col-md-3">
            <button
              class="btn btn-dark w-100"
              @click="addItem"
              :disabled="saving || !form.name.trim()"
            >
              {{ saving ? "Adding…" : "Add Item" }}
            </button>
          </div>
        </div>
        <p v-if="error" class="text-danger mt-2 mb-0 small">{{ error }}</p>
      </div>
    </div>

    <!-- Items Table -->
    <div class="card border-0 shadow-sm">
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5 text-muted">Loading…</div>
        <div v-else-if="items.length === 0" class="text-center py-5 text-muted">
          No items yet. Add one above!
        </div>
        <table v-else class="table table-hover mb-0">
          <thead class="table-dark">
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Description</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td class="text-muted small align-middle">{{ item.id }}</td>
              <td class="fw-semibold align-middle">{{ item.name }}</td>
              <td class="text-muted align-middle">{{ item.description }}</td>
              <td class="text-end align-middle">
                <button
                  class="btn btn-sm btn-outline-danger"
                  @click="removeItem(item.id)"
                >
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "../api";

const items = ref([]);
const loading = ref(false);
const saving = ref(false);
const error = ref("");
const form = ref({ name: "", description: "" });

async function fetchItems() {
  loading.value = true;
  try {
    const { data } = await api.getItems();
    items.value = data.items;
  } finally {
    loading.value = false;
  }
}

async function addItem() {
  error.value = "";
  saving.value = true;
  try {
    const { data } = await api.createItem(form.value);
    items.value.push(data);
    form.value = { name: "", description: "" };
  } catch (e) {
    error.value = e.response?.data?.error || "Failed to create item.";
  } finally {
    saving.value = false;
  }
}

async function removeItem(id) {
  await api.deleteItem(id);
  items.value = items.value.filter((i) => i.id !== id);
}

onMounted(fetchItems);
</script>
