#!/bin/bash
# NetGuardian Quick Start Script
# Runs API backend and Streamlit SOC Dashboard concurrently.

echo "============================================================"
echo "Starting NetGuardian SOC System..."
echo "============================================================"

# Check if port 8000 is occupied
if lsof -pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "[*] API Server (Port 8000) is already running."
else
    echo "[+] Starting API Server on Port 8000 in background..."
    env NETGUARDIAN_AI_MODE=live NETGUARDIAN_AI_PROVIDER=ollama \
        NETGUARDIAN_OLLAMA_URL=http://127.0.0.1:11434 \
        NETGUARDIAN_OLLAMA_MODEL=qwen2.5:7b \
        NETGUARDIAN_OLLAMA_TIMEOUT_SECONDS=120 \
        NETGUARDIAN_DASHBOARD_AGENT_TIMEOUT_SECONDS=120 \
        .venv/bin/uvicorn netguardian.api:app --host 127.0.0.1 --port 8000 > api.log 2>&1 &
    API_PID=$!
fi

# Check if port 8501 is occupied
if lsof -pi :8501 -sTCP:LISTEN -t >/dev/null ; then
    echo "[*] SOC Dashboard (Port 8501) is already running."
else
    echo "[+] Starting SOC Dashboard on Port 8501 in background..."
    .venv/bin/streamlit run netguardian/dashboard.py --server.address 127.0.0.1 --server.port 8501 > dashboard.log 2>&1 &
    DASHBOARD_PID=$!
fi

echo ""
echo "System up!"
echo "- NetGuardian API:  http://127.0.0.1:8000"
echo "- SOC Dashboard:    http://127.0.0.1:8501"
echo ""
echo "To stop the background servers, run:"
echo "  kill \$(lsof -t -i:8000 -i:8501)"
echo "============================================================"
