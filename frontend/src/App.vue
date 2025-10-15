<script setup>
import { ref, onMounted } from "vue";

const status = ref("Connecting to print service...");
const logs = ref([]);
const bridgeReady = ref(false);

function log(msg) {
  const t = new Date().toISOString().substr(11, 8);
  logs.value.unshift(`[${t}] ${msg}`);
  status.value = msg;
}

function detectBridge(timeout = 10000) {
  return new Promise((resolve) => {
    const start = Date.now();
    const interval = setInterval(() => {
      if (window.IminPrintInstance) {
        clearInterval(interval);
        bridgeReady.value = true;
        log("Bridge detected.");
        resolve(true);
      } else if (Date.now() - start >= timeout) {
        clearInterval(interval);
        log("Bridge detection timed out.");
        resolve(false);
      }
    }, 300);
  });
}

async function initPrinter(type = null) {
  if (!bridgeReady.value) {
    log("Bridge not ready — cannot init.");
    return;
  }
  try {
    if (type !== null) {
      await window.IminPrintInstance.initPrinter(type);
      log(`initPrinter success (type ${type})`);
    } else {
      // try multiple types
      const types = [
        window.IminPrintInstance.PrintConnectType.SPI,
        window.IminPrintInstance.PrintConnectType.USB,
        window.IminPrintInstance.PrintConnectType.Bluetooth,
      ];
      for (const t of types) {
        try {
          await window.IminPrintInstance.initPrinter(t);
          log(`initPrinter success with type ${t}`);
          return;
        } catch (e) {
          log(`initPrinter failed for type ${t}: ${e.message}`);
        }
      }
      log("All initPrinter attempts failed.");
    }
  } catch (err) {
    log("initPrinter error: " + err.message);
    console.error(err);
  }
}

async function getStatus() {
  try {
    window.IminPrintInstance.getPrinterStatus(
      window.IminPrintInstance.PrintConnectType.SPI,
      (resp) => {
        log("printer status (SPI) => " + resp.value);
      }
    );
  } catch (e) {
    log("getPrinterStatus error: " + e.message);
  }
}

async function printTest() {
  try {
    window.IminPrintInstance.setAlignment(1);
    window.IminPrintInstance.setTextSize(28);
    await window.IminPrintInstance.printText("Test print from app\n", 0);
    log("printText executed");
  } catch (e) {
    log("printText error: " + e.message);
  }
}

onMounted(async () => {
  const ok = await detectBridge(8000);
  if (!ok) {
    log("Bridge still missing after timeout; printing unavailable.");
  } else {
    // optionally auto init:
    // await initPrinter();
  }
});
</script>

<template>
  <div style="padding: 1rem; font-family: monospace;">
    <h3>Printer Demo UI</h3>
    <p>Status: <b>{{ status }}</b></p>
    <div style="margin-bottom:1rem;">
      <button @click="initPrinter()">Init Printer</button>
      <button @click="getStatus()">Get Status</button>
      <button @click="printTest()">Print Text</button>
    </div>
    <div
      style="
        background: #000;
        color: #0f0;
        padding: 0.5rem;
        border: 1px solid #444;
        height: 250px;
        overflow-y: auto;
      "
    >
      <div v-for="(l, idx) in logs.slice(0,50)" :key="idx">{{ l }}</div>
    </div>
  </div>
</template>

<style scoped>
main {
    font-family: system-ui, sans-serif;
}
</style>
