<script setup>
import { ref, onMounted } from "vue";

const printerStatus = ref("not initialized");
const lastPrint = ref(null);
const pollMs = 5000;

function iminReady() {
    return typeof window.IminPrintInstance !== "undefined";
}

async function initPrinter() {
    if (!iminReady()) {
        printerStatus.value = "bridge missing";
        return;
    }
    try {
        await IminPrintInstance.initPrinter(
            IminPrintInstance.PrintConnectType.SPI
        );
        printerStatus.value = "ready";
        IminPrintInstance.setAlignment(1);
        IminPrintInstance.setTextSize(28);
        IminPrintInstance.printText("printer ready\n\n", 0);
    } catch (e) {
        printerStatus.value = "init error";
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
    if (!iminReady()) return;
    IminPrintInstance.setAlignment(0);
    IminPrintInstance.setTextSize(26);
    IminPrintInstance.printText(formatReceipt(o), 0);
    IminPrintInstance.printAndFeedPaper(60);
    try {
        IminPrintInstance.partialCut();
    } catch (e) {}
    lastPrint.value = `#${o.id} at ${new Date().toLocaleTimeString()}`;
}

async function pollOnce() {
    try {
        const res = await fetch("/api/orders/poll");
        if (!res.ok) return;
        const orders = await res.json();
        for (const o of orders) await printOrder(o);
    } catch {}
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
                keep this page open in the imin webprint browser. new orders
                auto-print.
            </p>
        </div>
    </main>
</template>

<style scoped>
main {
    font-family: system-ui, sans-serif;
}
</style>
