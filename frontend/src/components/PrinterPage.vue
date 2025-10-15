<script setup>
import { ref, onMounted } from "vue";

const printerStatus = ref("⏳ Connecting to print service...");
const lastPrint = ref(null);
const logs = ref([]);
const pollMs = 5000;

let IminPrintInstance = null;

function log(msg) {
    const t = new Date().toLocaleTimeString();
    logs.value.unshift(`[${t}] ${msg}`);
    printerStatus.value = msg;
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
    try {
        const res = await fetch("/api/orders/poll");
        if (!res.ok) return;
        const orders = await res.json();
        for (const o of orders) await printOrder(o);
    } catch (err) {
        log("pollOnce error: " + err.message);
    }
}

onMounted(() => {
    initPrinter();
    setInterval(pollOnce, pollMs);
});
</script>

<template>
    <main class="p-4 max-w-md mx-auto">
        <h1 class="text-xl font-semibold mb-4">🍽️ Auto Print MVP</h1>

        <div class="space-y-2 text-sm">
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
                keep this page open in the iMin WebPrint browser. new orders
                auto-print.
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
    </main>
</template>

<style scoped>
main {
    font-family: system-ui, sans-serif;
}
</style>
