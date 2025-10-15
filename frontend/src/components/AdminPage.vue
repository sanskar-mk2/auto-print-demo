<script setup>
import { ref, computed } from "vue";

// Form data
const table = ref("");
const items = ref([{ qty: 1, name: "", price: 0 }]);
const createdOrders = ref([]);
const successMessage = ref("");
const errorMessage = ref("");

// Computed total
const total = computed(() => {
  return items.value.reduce((sum, item) => {
    const qty = parseFloat(item.qty) || 0;
    const price = parseFloat(item.price) || 0;
    return sum + (qty * price);
  }, 0);
});

// Validation
const isValid = computed(() => {
  return items.value.every(item => 
    item.qty > 0 && 
    item.name.trim() !== "" && 
    item.price >= 0
  );
});

// Add new item row
function addItem() {
  items.value.push({ qty: 1, name: "", price: 0 });
}

// Remove item row
function removeItem(index) {
  if (items.value.length > 1) {
    items.value.splice(index, 1);
  }
}

// Clear form
function clearForm() {
  table.value = "";
  items.value = [{ qty: 1, name: "", price: 0 }];
  successMessage.value = "";
  errorMessage.value = "";
}

// Submit order
async function submitOrder() {
  if (!isValid.value) {
    errorMessage.value = "Please fill in all item fields correctly";
    return;
  }

  try {
    const payload = {
      table: table.value || null,
      items: items.value.map(item => ({
        qty: parseInt(item.qty),
        name: item.name.trim(),
        price: parseFloat(item.price)
      })),
      total: total.value
    };

    const response = await fetch("/api/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Failed to create order");
    }

    const result = await response.json();
    
    // Add to created orders list
    createdOrders.value.unshift({
      id: result.id,
      table: table.value || "—",
      items: payload.items,
      total: total.value,
      created_at: new Date().toLocaleString()
    });

    successMessage.value = `Order #${result.id} created successfully!`;
    errorMessage.value = "";
    
    // Clear form after success
    setTimeout(() => {
      clearForm();
    }, 2000);

  } catch (error) {
    errorMessage.value = "Error creating order: " + error.message;
    successMessage.value = "";
  }
}
</script>

<template>
  <main class="p-4 max-w-4xl mx-auto">
    <h1 class="text-2xl font-semibold mb-6">🍽️ Admin - Create Order</h1>

    <!-- Success/Error Messages -->
    <div v-if="successMessage" class="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
      {{ successMessage }}
    </div>
    <div v-if="errorMessage" class="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
      {{ errorMessage }}
    </div>

    <!-- Order Form -->
    <div class="bg-white p-6 rounded-lg border shadow-sm mb-6">
      <h2 class="text-lg font-medium mb-4">New Order</h2>
      
      <!-- Table Number -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Table Number (Optional)
        </label>
        <input
          v-model="table"
          type="text"
          placeholder="e.g., 5, A1, Counter"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- Items Table -->
      <div class="mb-4">
        <div class="flex justify-between items-center mb-3">
          <label class="block text-sm font-medium text-gray-700">
            Order Items
          </label>
          <button
            @click="addItem"
            class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          >
            + Add Item
          </button>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full border-collapse border border-gray-300">
            <thead>
              <tr class="bg-gray-50">
                <th class="border border-gray-300 px-3 py-2 text-left text-sm font-medium">Qty</th>
                <th class="border border-gray-300 px-3 py-2 text-left text-sm font-medium">Name</th>
                <th class="border border-gray-300 px-3 py-2 text-left text-sm font-medium">Price (₹)</th>
                <th class="border border-gray-300 px-3 py-2 text-left text-sm font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in items" :key="index">
                <td class="border border-gray-300 px-3 py-2">
                  <input
                    v-model.number="item.qty"
                    type="number"
                    min="1"
                    class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </td>
                <td class="border border-gray-300 px-3 py-2">
                  <input
                    v-model="item.name"
                    type="text"
                    placeholder="Item name"
                    class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </td>
                <td class="border border-gray-300 px-3 py-2">
                  <input
                    v-model.number="item.price"
                    type="number"
                    min="0"
                    step="0.01"
                    class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </td>
                <td class="border border-gray-300 px-3 py-2 text-center">
                  <button
                    v-if="items.length > 1"
                    @click="removeItem(index)"
                    class="px-2 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Total -->
      <div class="mb-6 p-3 bg-gray-50 rounded">
        <div class="flex justify-between items-center">
          <span class="text-lg font-medium">Total:</span>
          <span class="text-xl font-bold">₹{{ total.toFixed(2) }}</span>
        </div>
      </div>

      <!-- Submit Button -->
      <div class="flex gap-3">
        <button
          @click="submitOrder"
          :disabled="!isValid"
          class="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          Create Order
        </button>
        <button
          @click="clearForm"
          class="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          Clear Form
        </button>
      </div>
    </div>

    <!-- Created Orders List -->
    <div v-if="createdOrders.length > 0" class="bg-white p-6 rounded-lg border shadow-sm">
      <h2 class="text-lg font-medium mb-4">Recent Orders</h2>
      <div class="space-y-3">
        <div
          v-for="order in createdOrders"
          :key="order.id"
          class="p-4 border border-gray-200 rounded-lg"
        >
          <div class="flex justify-between items-start mb-2">
            <div>
              <span class="font-medium">Order #{{ order.id }}</span>
              <span class="text-gray-600 ml-2">Table: {{ order.table }}</span>
            </div>
            <div class="text-right">
              <div class="font-bold">₹{{ order.total.toFixed(2) }}</div>
              <div class="text-sm text-gray-500">{{ order.created_at }}</div>
            </div>
          </div>
          <div class="text-sm text-gray-600">
            <div v-for="item in order.items" :key="`${item.name}-${item.qty}`">
              {{ item.qty }}x {{ item.name }} - ₹{{ item.price.toFixed(2) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
main {
  font-family: system-ui, sans-serif;
}
</style>
