#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WIN_ROOT='C:\Trading\System-Tools'
WIN_BRIDGE_DIR='C:\Trading\System-Tools\mt5-connection-bridge'
WIN_BRIDGE_MNT='/mnt/c/Trading/System-Tools/mt5-connection-bridge'
REMOTE_URL='https://github.com/LeonAI-DO-YLCS/mt5-connection-bridge.git'
BRIDGE_PORT='8001'
START_BRIDGE='true'
INSTALL_DEPS='true'

usage() {
  cat <<'EOF'
Usage: scripts/refresh_windows_mt5_bridge.sh [options]

Refreshes the Windows MT5 bridge runtime clone from GitHub, restores local
runtime files, optionally reinstalls Python dependencies, and optionally
restarts the Windows-native bridge.

Options:
  --no-start         Refresh the Windows clone but do not restart the bridge
  --skip-install     Do not run pip install in the Windows clone
  --help             Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-start)
      START_BRIDGE='false'
      ;;
    --skip-install)
      INSTALL_DEPS='false'
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need_cmd powershell.exe
need_cmd cmd.exe
need_cmd curl
need_cmd awk
need_cmd mktemp

BACKUP_DIR="$(mktemp -d)"
PS_START_SCRIPT=''
trap 'rm -rf "$BACKUP_DIR"' EXIT

echo "[1/6] Backing up Windows runtime files"
if [[ -f "$WIN_BRIDGE_MNT/.env" ]]; then
  cp "$WIN_BRIDGE_MNT/.env" "$BACKUP_DIR/.env"
fi
if [[ -f "$WIN_BRIDGE_MNT/logs/runtime_state.json" ]]; then
  mkdir -p "$BACKUP_DIR/logs"
  cp "$WIN_BRIDGE_MNT/logs/runtime_state.json" "$BACKUP_DIR/logs/runtime_state.json"
fi

echo "[2/6] Stopping bridge listener on port ${BRIDGE_PORT}"
powershell.exe -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort ${BRIDGE_PORT} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id \$_ -Force -ErrorAction SilentlyContinue }" >/dev/null 2>&1 || true

PS_REFRESH_SCRIPT="$(mktemp --suffix=.ps1)"
trap 'rm -rf "$BACKUP_DIR" "$PS_REFRESH_SCRIPT" "$PS_START_SCRIPT"' EXIT
cat >"$PS_REFRESH_SCRIPT" <<EOF
$dst = '${WIN_BRIDGE_DIR}'
$root = '${WIN_ROOT}'
if (-not (Test-Path $root)) {
  New-Item -ItemType Directory -Force -Path $root | Out-Null
}
if (Test-Path $dst) {
  Remove-Item -Recurse -Force $dst
}
git clone '${REMOTE_URL}' $dst
EOF

echo "[3/6] Re-cloning Windows runtime from GitHub"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(wslpath -w "$PS_REFRESH_SCRIPT")"

echo "[4/6] Restoring runtime-local files"
if [[ -f "$BACKUP_DIR/.env" ]]; then
  cp "$BACKUP_DIR/.env" "$WIN_BRIDGE_MNT/.env"
fi
if [[ -f "$BACKUP_DIR/logs/runtime_state.json" ]]; then
  mkdir -p "$WIN_BRIDGE_MNT/logs"
  cp "$BACKUP_DIR/logs/runtime_state.json" "$WIN_BRIDGE_MNT/logs/runtime_state.json"
fi

if [[ "$INSTALL_DEPS" == 'true' ]]; then
  echo "[5/6] Installing Windows Python dependencies"
  cmd.exe /c "cd /d C:\Trading\System-Tools\mt5-connection-bridge && py -3.12 -m pip install -r requirements.txt && py -3.12 -m pip install requests"
else
  echo "[5/6] Skipping dependency installation"
fi

if [[ "$START_BRIDGE" == 'true' ]]; then
  PS_START_SCRIPT="$(mktemp --suffix=.ps1)"
  cat >"$PS_START_SCRIPT" <<EOF
$repo = '${WIN_BRIDGE_DIR}'
Set-Location $repo
$stdoutLog = Join-Path $repo 'logs\\bridge-refresh.stdout.log'
$stderrLog = Join-Path $repo 'logs\\bridge-refresh.stderr.log'
New-Item -ItemType Directory -Force -Path (Join-Path $repo 'logs') | Out-Null
Start-Process -FilePath 'C:\Users\LeonAI-DO\AppData\Local\Programs\Python\Python312\python.exe' -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','${BRIDGE_PORT}' -WorkingDirectory $repo -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -WindowStyle Hidden
EOF
  echo "[6/6] Starting Windows bridge"
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(wslpath -w "$PS_START_SCRIPT")"

  if [[ -f "$WIN_BRIDGE_MNT/.env" ]]; then
    API_KEY="$(awk -F= '$1=="MT5_BRIDGE_API_KEY" {print substr($0, index($0, "=")+1); exit}' "$WIN_BRIDGE_MNT/.env")"
  else
    API_KEY=''
  fi

  if [[ -n "$API_KEY" ]]; then
    echo "Waiting for bridge health on localhost:${BRIDGE_PORT}"
    for _ in $(seq 1 20); do
      if curl -fsS -H "X-API-KEY: ${API_KEY}" "http://localhost:${BRIDGE_PORT}/health" >/dev/null 2>&1; then
        echo "Bridge is healthy"
        curl -sS -H "X-API-KEY: ${API_KEY}" "http://localhost:${BRIDGE_PORT}/health"
        exit 0
      fi
      sleep 2
    done
    echo "Bridge did not become healthy within the expected time window" >&2
    exit 1
  fi

  echo "Bridge started, but no API key was restored so health was not checked"
else
  echo "[6/6] Skipping bridge restart"
fi
