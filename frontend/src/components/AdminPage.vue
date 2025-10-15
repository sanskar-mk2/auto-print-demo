<script setup>
import { ref, computed, onMounted } from "vue";

// Restaurant management
const restaurants = ref([]);
const newRestaurantName = ref("");
const restaurantSuccessMessage = ref("");
const restaurantErrorMessage = ref("");

// Form data
const selectedRestaurantId = ref("");
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
        return sum + qty * price;
    }, 0);
});

// Validation
const isValid = computed(() => {
    return (
        selectedRestaurantId.value &&
        items.value.every(
            (item) => item.qty > 0 && item.name.trim() !== "" && item.price >= 0
        )
    );
});

// Restaurant management functions
async function loadRestaurants() {
    try {
        const response = await fetch("/api/restaurants");
        if (response.ok) {
            restaurants.value = await response.json();
        }
    } catch (error) {
        console.error("Error loading restaurants:", error);
    }
}

async function createRestaurant() {
    if (!newRestaurantName.value.trim()) {
        restaurantErrorMessage.value = "Restaurant name is required";
        return;
    }

    try {
        const response = await fetch("/api/restaurants", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ name: newRestaurantName.value.trim() }),
        });

        if (!response.ok) {
            throw new Error("Failed to create restaurant");
        }

        const result = await response.json();
        restaurantSuccessMessage.value = `Restaurant "${result.name}" created with token: ${result.token}`;
        restaurantErrorMessage.value = "";
        newRestaurantName.value = "";

        // Reload restaurants list
        await loadRestaurants();

        // Clear success message after 5 seconds
        setTimeout(() => {
            restaurantSuccessMessage.value = "";
        }, 5000);
    } catch (error) {
        restaurantErrorMessage.value =
            "Error creating restaurant: " + error.message;
        restaurantSuccessMessage.value = "";
    }
}

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
    selectedRestaurantId.value = "";
    table.value = "";
    items.value = [{ qty: 1, name: "", price: 0 }];
    successMessage.value = "";
    errorMessage.value = "";
}

// Load restaurants on mount
onMounted(() => {
    loadRestaurants();
});

// Submit order
async function submitOrder() {
    if (!isValid.value) {
        errorMessage.value = "Please fill in all item fields correctly";
        return;
    }

    try {
        const payload = {
            restaurant_id: parseInt(selectedRestaurantId.value),
            table: table.value || null,
            items: items.value.map((item) => ({
                qty: parseInt(item.qty),
                name: item.name.trim(),
                price: parseFloat(item.price),
            })),
            total: total.value,
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
        const restaurant = restaurants.value.find(
            (r) => r.id === parseInt(selectedRestaurantId.value)
        );
        createdOrders.value.unshift({
            id: result.id,
            restaurant: restaurant?.name || "Unknown",
            table: table.value || "—",
            items: payload.items,
            total: total.value,
            created_at: new Date().toLocaleString(),
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
        <h1 class="text-2xl font-semibold mb-6">
            🍽️ Admin - Restaurant Management
        </h1>

        <!-- Restaurant Management Section -->
        <div class="bg-white p-6 rounded-lg border shadow-sm mb-6">
            <h2 class="text-lg font-medium mb-4">Manage Restaurants</h2>

            <!-- Restaurant Success/Error Messages -->
            <div
                v-if="restaurantSuccessMessage"
                class="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded"
            >
                {{ restaurantSuccessMessage }}
            </div>
            <div
                v-if="restaurantErrorMessage"
                class="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded"
            >
                {{ restaurantErrorMessage }}
            </div>

            <!-- Add New Restaurant -->
            <div class="mb-4">
                <div class="flex gap-3 items-end">
                    <div class="flex-1">
                        <label
                            class="block text-sm font-medium text-gray-700 mb-2"
                        >
                            Restaurant Name
                        </label>
                        <input
                            v-model="newRestaurantName"
                            type="text"
                            placeholder="e.g., Pizza Palace, Burger King"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <button
                        @click="createRestaurant"
                        :disabled="!newRestaurantName.trim()"
                        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                        Create Restaurant
                    </button>
                </div>
            </div>

            <!-- Existing Restaurants List -->
            <div v-if="restaurants.length > 0">
                <h3 class="text-md font-medium mb-3">Existing Restaurants</h3>
                <div class="space-y-2">
                    <div
                        v-for="restaurant in restaurants"
                        :key="restaurant.id"
                        class="p-3 border border-gray-200 rounded-lg bg-gray-50"
                    >
                        <div class="flex justify-between items-center">
                            <div>
                                <span class="font-medium">{{
                                    restaurant.name
                                }}</span>
                                <span class="text-gray-500 ml-2"
                                    >(ID: {{ restaurant.id }})</span
                                >
                            </div>
                            <div class="text-right">
                                <div
                                    class="text-sm font-mono bg-white px-2 py-1 rounded border"
                                >
                                    {{ restaurant.token }}
                                </div>
                                <div class="text-xs text-gray-500 mt-1">
                                    Created:
                                    {{
                                        new Date(
                                            restaurant.created_at
                                        ).toLocaleDateString()
                                    }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Order Creation Section -->
        <div class="bg-white p-6 rounded-lg border shadow-sm mb-6">
            <h2 class="text-lg font-medium mb-4">Create Order</h2>
            <!-- Success/Error Messages -->
            <div
                v-if="successMessage"
                class="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded"
            >
                {{ successMessage }}
            </div>
            {{ successMessage }}
        </div>
        <div
            v-if="errorMessage"
            class="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded"
        >
            {{ errorMessage }}
        </div>

        <!-- Order Form -->
        <div class="bg-white p-6 rounded-lg border shadow-sm mb-6">
            <h2 class="text-lg font-medium mb-4">New Order</h2>

            <!-- Restaurant Selection -->
            <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Restaurant *
                </label>
                <select
                    v-model="selectedRestaurantId"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">Select a restaurant</option>
                    <option
                        v-for="restaurant in restaurants"
                        :key="restaurant.id"
                        :value="restaurant.id"
                    >
                        {{ restaurant.name }}
                    </option>
                </select>
            </div>

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
                    <table
                        class="w-full border-collapse border border-gray-300"
                    >
                        <thead>
                            <tr class="bg-gray-50">
                                <th
                                    class="border border-gray-300 px-3 py-2 text-left text-sm font-medium"
                                >
                                    Qty
                                </th>
                                <th
                                    class="border border-gray-300 px-3 py-2 text-left text-sm font-medium"
                                >
                                    Name
                                </th>
                                <th
                                    class="border border-gray-300 px-3 py-2 text-left text-sm font-medium"
                                >
                                    Price (₹)
                                </th>
                                <th
                                    class="border border-gray-300 px-3 py-2 text-left text-sm font-medium"
                                >
                                    Action
                                </th>
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
                                <td
                                    class="border border-gray-300 px-3 py-2 text-center"
                                >
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
                    <span class="text-xl font-bold"
                        >₹{{ total.toFixed(2) }}</span
                    >
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
        <div
            v-if="createdOrders.length > 0"
            class="bg-white p-6 rounded-lg border shadow-sm"
        >
            <h2 class="text-lg font-medium mb-4">Recent Orders</h2>
            <div class="space-y-3">
                <div
                    v-for="order in createdOrders"
                    :key="order.id"
                    class="p-4 border border-gray-200 rounded-lg"
                >
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <span class="font-medium"
                                >Order #{{ order.id }}</span
                            >
                            <span class="text-gray-600 ml-2">{{
                                order.restaurant
                            }}</span>
                            <span class="text-gray-600 ml-2"
                                >Table: {{ order.table }}</span
                            >
                        </div>
                        <div class="text-right">
                            <div class="font-bold">
                                ₹{{ order.total.toFixed(2) }}
                            </div>
                            <div class="text-sm text-gray-500">
                                {{ order.created_at }}
                            </div>
                        </div>
                    </div>
                    <div class="text-sm text-gray-600">
                        <div
                            v-for="item in order.items"
                            :key="`${item.name}-${item.qty}`"
                        >
                            {{ item.qty }}x {{ item.name }} - ₹{{
                                item.price.toFixed(2)
                            }}
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
