<script setup>
import { ref, onMounted } from "vue";

const printerStatus = ref("initializing...");
const debugLogs = ref([]);
const lastPrint = ref(null);
const pollMs = 3000;

function log(msg) {
  const time = new Date().toLocaleTimeString();
  debugLogs.value.unshift(`[${time}] ${msg}`);
  printerStatus.value = msg;
}

function iminReady() {
  return typeof window.IminPrintInstance !== "undefined";
}

async function waitForIminBridge(timeout = 10000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    if (iminReady()) return true;
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

async function initPrinter() {
  log("Checking for Imin bridge...");
  const ready = await waitForIminBridge();

  if (!ready) {
    log("❌ Bridge not found — are you on an Imin POS?");
    return;
  }

  log("✅ Bridge detected, initializing printer...");

  try {
    const connType = window.IminPrintInstance.PrintConnectType.SPI;
    await window.IminPrintInstance.initPrinter(connType);
    log("✅ Printer initialized successfully");

    window.IminPrintInstance.setAlignment(1);
    window.IminPrintInstance.setTextSize(28);
    window.IminPrintInstance.printText("Printer Ready\n\n", 0);
  } catch (e) {
    log("⚠️ initPrinter() error: " + e.message);
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
  <div style="font-family: monospace; padding: 1rem;">
    <h2>Imin Printer Debug</h2>
    <p>Status: <b>{{ printerStatus }}</b></p>
    <p v-if="lastPrint">Last print: {{ lastPrint }}</p>
    <div
      style="
        margin-top: 1rem;
        border: 1px solid #ccc;
        border-radius: 8px;
        max-height: 300px;
        overflow-y: auto;
        background: #111;
        color: #0f0;
        padding: 0.5rem;
      "
    >
      <div v-for="(msg, i) in debugLogs" :key="i">{{ msg }}</div>
    </div>
  </div>
</template>

<style scoped>
main {
    font-family: system-ui, sans-serif;
}
</style>
