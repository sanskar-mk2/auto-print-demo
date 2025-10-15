import { createApp } from "vue";
import "./style.css";
import App from "./App.vue";

// Check if iMin bridge is ready before loading Vue app
if (!window.__iminReady) {
    console.warn('imin bridge not detected yet; retrying...');
    window.addEventListener('load', () => console.log(window.IminPrinter));
}

// JavaScript error logging setup
const API_LOG = "/api/logs/js"; // proxied to FastAPI

function sendLog(data) {
    console.log("Sending log:", data);
    // avoid infinite loops if /api/logs fails
    try {
        navigator.sendBeacon(API_LOG, JSON.stringify(data));
    } catch {
        fetch(API_LOG, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        }).catch(() => {
            // Silent fail to avoid infinite loops
        });
    }
}

// global catch for syntax/runtime errors
window.onerror = (msg, src, line, col, err) => {
    sendLog({
        type: "error",
        message: msg?.toString(),
        source: src,
        line,
        col,
        stack: err?.stack,
        userAgent: navigator.userAgent,
        time: new Date().toISOString(),
    });
};

// catch unhandled Promise rejections
window.addEventListener("unhandledrejection", (e) => {
    console.log("Unhandled rejection caught:", e.reason);
    sendLog({
        type: "unhandledrejection",
        message: e.reason?.message || e.reason || "unknown",
        reason: e.reason?.message || e.reason || "unknown",
        stack: e.reason?.stack,
        time: new Date().toISOString(),
    });
});

createApp(App).mount("#app");
