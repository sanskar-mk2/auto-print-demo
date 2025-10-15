<script setup>
import { ref, onMounted } from "vue";

const logs = ref([]);
const status = ref("⏳ Connecting to print service...");
let IminPrintInstance = null;

function log(msg) {
    const t = new Date().toLocaleTimeString();
    logs.value.unshift(`[${t}] ${msg}`);
    status.value = msg;
}

async function init() {
    try {
        // wait for the SDK bridge to exist
        await waitForBridge();

        IminPrintInstance = new window.IminPrinter();
        log("Bridge found, creating IminPrinter instance...");

        const connected = await IminPrintInstance.connect();
        if (!connected) {
            log("❌ Failed to connect to print service.");
            return;
        }

        log("✅ Connected to print service, initializing printer...");
        await IminPrintInstance.initPrinter();
        log("✅ Printer initialized. Checking status...");

        const timer = setInterval(async () => {
            const statusResp = await IminPrintInstance.getPrinterStatus();
            if (statusResp.value === 0) {
                log("🟢 Printer status normal.");
                clearInterval(timer);
            } else {
                log(
                    "⚠️ Printer error or disconnected: " +
                        JSON.stringify(statusResp)
                );
                await IminPrintInstance.initPrinter();
            }
        }, 2000);
    } catch (e) {
        log("❌ Error: " + e.message);
    }
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

onMounted(() => {
    init();
});
</script>

<template>
    <div style="font-family: monospace; padding: 1rem">
        <h2>Imin Printer Debug (Vue)</h2>
        <p>
            Status: <b>{{ status }}</b>
        </p>
        <div
            style="
                border: 1px solid #444;
                background: #000;
                color: #0f0;
                border-radius: 8px;
                padding: 0.5rem;
                max-height: 300px;
                overflow-y: auto;
            "
        >
            <div v-for="(line, idx) in logs" :key="idx">{{ line }}</div>
        </div>
        <div style="margin-top: 1rem">
            <button
                @click="IminPrintInstance?.printText('Hello from Vue\n', 0)"
            >
                Print Test
            </button>
            <button @click="IminPrintInstance?.printAndLineFeed()">
                Feed Paper
            </button>
            <button @click="IminPrintInstance?.cutPaper()">Cut</button>
        </div>
    </div>
</template>
