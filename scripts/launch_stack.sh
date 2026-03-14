#!/usr/bin/env bash

# Unified Stack Launcher
# Launches MT5 Bridge (Windows via WSL), Backend (WSL), and Frontend (WSL)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs/stack"
mkdir -p "$LOG_DIR"

# Ports
BACKEND_PORT=8000
BRIDGE_PORT=8001
FRONTEND_PORT=5173

# Colors
C_RESET=$'\033[0m'
C_HEADER=$'\033[1;36m'
C_OK=$'\033[1;32m'
C_WARN=$'\033[1;33m'
C_ERR=$'\033[1;31m'

echo "${C_HEADER}====================================================${C_RESET}"
echo "${C_HEADER} AI Hedge Fund Stack Launcher                       ${C_RESET}"
echo "${C_HEADER}====================================================${C_RESET}"

# 1. Environment Checks
echo "Checking environment..."

if ! command -v powershell.exe >/dev/null 2>&1; then
    echo "${C_ERR}Error: powershell.exe not found. This script must be run from WSL2.${C_RESET}"
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "${C_ERR}Error: uv not found. Please install uv in WSL.${C_RESET}"
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "${C_ERR}Error: npm not found. Please install Node.js/npm in WSL.${C_RESET}"
    exit 1
fi

if [[ ! -f "$ROOT_DIR/.env" ]]; then
    echo "${C_WARN}Warning: .env file not found in root. Creating from .env.example...${C_RESET}"
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

# 2. Port Cleanup
echo "Cleaning up existing processes..."

cleanup_port() {
    local port=$1
    local pids
    pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        echo "Killing processes on port $port: $pids"
        kill -9 $pids 2>/dev/null || true
    fi
}

cleanup_port "$BACKEND_PORT"
cleanup_port "$FRONTEND_PORT"
# Bridge might be running on Windows, launch_bridge_dashboard.sh handles its own cleanup,
# but we can try to kill any local listeners if they exist.
cleanup_port "$BRIDGE_PORT"

# 3. Launch Backend
echo "Starting Backend on port $BACKEND_PORT..."
cd "$ROOT_DIR"
uv run uvicorn app.backend.main:app --host 127.0.0.1 --port "$BACKEND_PORT" > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

# 4. Launch Frontend
echo "Starting Frontend on port $FRONTEND_PORT..."
cd "$ROOT_DIR/app/frontend"
# Check if node_modules exists
if [[ ! -d "node_modules" ]]; then
    echo "Installing frontend dependencies..."
    npm install > "$LOG_DIR/frontend_install.log" 2>&1
fi
npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Cleanup trap
cleanup() {
    echo ""
    echo "${C_WARN}Shutting down stack...${C_RESET}"
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    echo "Background processes stopped."
}

trap cleanup EXIT

# 5. Launch MT5 Bridge (Foreground)
echo "${C_OK}Launching MT5 Bridge TUI...${C_RESET}"
echo "Check logs/stack/ for backend/frontend output if they fail to start."
cd "$ROOT_DIR/mt5-connection-bridge"
LAUNCHER_SKIP_PREFLIGHT=true ./scripts/launch_bridge_windows.sh
