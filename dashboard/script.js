// ==============================
// WebSocket Configuration
// ==============================

// Example:
// ws://157.173.101.159:8000/ws
const WS_URL = "ws://localhost:8000/ws";

const socket = new WebSocket(WS_URL);

const movementEl = document.getElementById("movement");
const confidenceEl = document.getElementById("confidence");
const timestampEl = document.getElementById("timestamp");
const connectionEl = document.getElementById("connectionStatus");


// ==============================
// Connection Events
// ==============================

socket.onopen = () => {
    console.log("WebSocket connected");
    connectionEl.textContent = "CONNECTED";
    connectionEl.classList.remove("disconnected");
    connectionEl.classList.add("connected");
};

socket.onclose = () => {
    console.log("WebSocket disconnected");
    connectionEl.textContent = "DISCONNECTED";
    connectionEl.classList.remove("connected");
    connectionEl.classList.add("disconnected");
};

socket.onerror = (error) => {
    console.error("WebSocket error:", error);
};


// ==============================
// Message Handler
// ==============================

socket.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);

        /*
        Expected format:
        {
            "status": "MOVE_LEFT",
            "confidence": 0.87,
            "timestamp": 1730000000
        }
        */

        const { status, confidence, timestamp } = data;

        updateMovement(status);
        confidenceEl.textContent = (confidence * 100).toFixed(2) + " %";
        timestampEl.textContent = formatTimestamp(timestamp);

    } catch (err) {
        console.error("Invalid message format", err);
    }
};


// ==============================
// UI Update Functions
// ==============================

function updateMovement(status) {
    movementEl.textContent = status;

    // Reset classes
    movementEl.className = "movement";

    switch (status) {
        case "MOVE_LEFT":
            movementEl.classList.add("move-left");
            break;

        case "MOVE_RIGHT":
            movementEl.classList.add("move-right");
            break;

        case "CENTERED":
            movementEl.classList.add("centered");
            break;

        case "NO_FACE":
            movementEl.classList.add("no-face");
            break;
    }
}

function formatTimestamp(ts) {
    const date = new Date(ts * 1000);
    return date.toLocaleString();
}