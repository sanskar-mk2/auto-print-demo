<script setup>
import { ref, onMounted, computed } from "vue";

// Authentication
const token = ref("");
const restaurantInfo = ref(null);
const authError = ref("");
const isAuthenticated = computed(() => !!restaurantInfo.value);

// Printer
const printerStatus = ref("⏳ Please enter your restaurant token to start");
const lastPrint = ref(null);
const logs = ref([]);
const pollMs = 5000;

let IminPrintInstance = null;

function log(msg) {
    const t = new Date().toLocaleTimeString();
    logs.value.unshift(`[${t}] ${msg}`);
    if (isAuthenticated.value) {
        printerStatus.value = msg;
    }
}

// Authentication functions
async function verifyToken(tokenValue) {
    if (!tokenValue.trim()) {
        authError.value = "";
        restaurantInfo.value = null;
        return;
    }

    try {
        const response = await fetch(
            `/api/restaurants/verify/${tokenValue.trim()}`
        );
        if (response.ok) {
            restaurantInfo.value = await response.json();
            authError.value = "";
            // Save to localStorage
            localStorage.setItem("restaurant_token", tokenValue.trim());
            log(`✅ Authenticated as: ${restaurantInfo.value.name}`);
        } else {
            restaurantInfo.value = null;
            authError.value = "Invalid token";
        }
    } catch (error) {
        restaurantInfo.value = null;
        authError.value = "Error verifying token";
    }
}

function logout() {
    token.value = "";
    restaurantInfo.value = null;
    authError.value = "";
    localStorage.removeItem("restaurant_token");
    printerStatus.value = "⏳ Please enter your restaurant token to start";
    log("Logged out");
}

function waitForBridge(timeout = 10000) {
    return new Promise((resolve, reject) => {
        const start = Date.now();
        const check = setInterval(() => {
            if (window.IminPrinter) {
                clearInterval(check);
                resolve();
            } else if (Date.now() - start > timeout) {
                clearInterval(check);
                reject(new Error("Bridge not found"));
            }
        }, 300);
    });
}

async function initPrinter() {
    try {
        await waitForBridge();
        log("Bridge detected, creating IminPrinter instance...");

        IminPrintInstance = new window.IminPrinter();
        const connected = await IminPrintInstance.connect();
        if (!connected) {
            log("❌ Failed to connect to print service");
            return;
        }

        log("✅ Connected to print service, initializing printer...");
        await IminPrintInstance.initPrinter();
        log("✅ Printer initialized successfully");

        // check printer status every few seconds
        const timer = setInterval(async () => {
            try {
                const s = await IminPrintInstance.getPrinterStatus();
                if (s.value === 0) {
                    printerStatus.value = "🟢 Ready";
                } else {
                    log("⚠️ Printer status abnormal: " + JSON.stringify(s));
                }
            } catch (err) {
                log("⚠️ Status check error: " + err.message);
            }
        }, 4000);
    } catch (e) {
        log("❌ Printer init failed: " + e.message);
    }
}

function formatReceipt(o) {
    const lines = [];
    lines.push("==============================");
    lines.push("        ORDER RECEIPT");
    lines.push("==============================");
    lines.push(`Order #${o.id}`);
    if (o.table) lines.push(`Table: ${o.table}`);
    lines.push("------------------------------");
    o.items.forEach((i) => {
        const name = (i.name || "").slice(0, 18).padEnd(18, " ");
        const qty = String(i.qty || 1).padStart(2, " ");
        const price = String(i.price || 0).padStart(5, " ");
        lines.push(`${qty}x ${name} ${price}`);
    });
    lines.push("------------------------------");
    lines.push(`TOTAL ₹${o.total}`);
    lines.push(new Date().toLocaleString());
    lines.push("==============================\n\n");
    return lines.join("\n");
}

async function printOrder(o) {
    try {
        if (!IminPrintInstance) return log("⚠️ Printer not ready");
        IminPrintInstance.setAlignment(0);
        IminPrintInstance.setTextSize(26);
        await IminPrintInstance.printText(formatReceipt(o), 0);
        IminPrintInstance.printAndFeedPaper(60);
        try {
            IminPrintInstance.partialCut();
        } catch (_) {}
        lastPrint.value = `#${o.id} at ${new Date().toLocaleTimeString()}`;
        log(`🖨️ Printed order #${o.id}`);
    } catch (e) {
        log("❌ Print failed: " + e.message);
    }
}

async function pollOnce() {
    if (!isAuthenticated.value) return;

    try {
        const res = await fetch(`/api/orders/poll?token=${token.value}`);
        if (!res.ok) {
            if (res.status === 404) {
                log("❌ Token expired or invalid");
                logout();
            }
            return;
        }
        const orders = await res.json();
        for (const o of orders) await printOrder(o);
    } catch (err) {
        log("pollOnce error: " + err.message);
    }
}

onMounted(() => {
    // Load token from localStorage
    const savedToken = localStorage.getItem("restaurant_token");
    if (savedToken) {
        token.value = savedToken;
        verifyToken(savedToken);
    }

    // Only initialize printer if authenticated
    if (isAuthenticated.value) {
        initPrinter();
    }

    // Start polling
    setInterval(pollOnce, pollMs);
});
</script>

<template>
    <main class="p-4 max-w-md mx-auto">
        <h1 class="text-xl font-semibold mb-4">🍽️ Auto Print MVP</h1>

        <!-- Authentication Section -->
        <div class="mb-4 p-3 rounded border bg-white">
            <div v-if="!isAuthenticated" class="space-y-3">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Restaurant Token
                    </label>
                    <div class="flex gap-2">
                        <input
                            v-model="token"
                            @input="verifyToken(token)"
                            type="text"
                            placeholder="Enter your restaurant token"
                            class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <div v-if="authError" class="text-red-600 text-sm mt-1">
                        {{ authError }}
                    </div>
                </div>
            </div>

            <div v-else class="flex justify-between items-center">
                <div>
                    <div class="text-green-600 font-medium">
                        ✅ Signed in as: {{ restaurantInfo.name }}
                    </div>
                    <div class="text-xs text-gray-500">
                        Token: {{ token.substring(0, 8) }}...
                    </div>
                </div>
                <button
                    @click="logout"
                    class="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                >
                    Logout
                </button>
            </div>
        </div>

        <div v-if="isAuthenticated" class="space-y-2 text-sm">
            <div class="p-3 rounded border bg-white">
                <div>
                    <span class="font-medium">Printer:</span>
                    {{ printerStatus }}
                </div>
                <div>
                    <span class="font-medium">Last print:</span>
                    {{ lastPrint || "—" }}
                </div>
            </div>

            <div class="flex gap-2">
                <button
                    @click="initPrinter"
                    class="px-3 py-2 rounded bg-blue-600 text-white"
                >
                    Init Printer
                </button>
                <button
                    @click="pollOnce"
                    class="px-3 py-2 rounded bg-emerald-600 text-white"
                >
                    Force Poll
                </button>
            </div>

            <p class="text-xs text-gray-500 mt-2">
                Keep this page open in the iMin WebPrint browser. New orders for
                {{ restaurantInfo.name }} will auto-print.
            </p>

            <div
                style="
                    margin-top: 1rem;
                    border: 1px solid #444;
                    background: #000;
                    color: #0f0;
                    border-radius: 8px;
                    padding: 0.5rem;
                    max-height: 250px;
                    overflow-y: auto;
                "
            >
                <div v-for="(l, i) in logs" :key="i">{{ l }}</div>
            </div>
        </div>

        <div v-else class="text-center text-gray-500 py-8">
            <p>
                Please enter your restaurant token above to start printing
                orders.
            </p>
        </div>
    </main>
</template>

<style scoped>
main {
    font-family: system-ui, sans-serif;
}
</style>
