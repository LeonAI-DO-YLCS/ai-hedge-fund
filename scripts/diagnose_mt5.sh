#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  echo "FAIL: .env not found in project root"
  exit 1
fi

set -a
source .env
set +a

MT5_BRIDGE_URL="${MT5_BRIDGE_URL:-}"
MT5_BRIDGE_API_KEY="${MT5_BRIDGE_API_KEY:-}"
SYMBOL="${1:-V75}"
START_DATE="${2:-2026-02-01}"
END_DATE="${3:-2026-02-03}"

if [[ -z "$MT5_BRIDGE_URL" ]]; then
  echo "FAIL: MT5_BRIDGE_URL is empty"
  exit 1
fi

HOST="$(echo "$MT5_BRIDGE_URL" | sed -E 's#https?://([^:/]+).*#\1#')"
PORT="$(echo "$MT5_BRIDGE_URL" | sed -E 's#.*:([0-9]+).*#\1#')"

echo "=== MT5 Bridge Diagnostics ==="
echo "Bridge URL: $MT5_BRIDGE_URL"
echo "Ticker: $SYMBOL | Start: $START_DATE | End: $END_DATE"
echo

echo "[1/5] Python runtime check"
uv run python -V

echo "[2/5] CLI startup check"
uv run python -m src.main --help >/dev/null
echo "PASS: src.main imports and CLI parsed"

echo "[3/5] TCP port check ($HOST:$PORT)"
if nc -vz -w 3 "$HOST" "$PORT" >/dev/null 2>&1; then
  echo "PASS: Bridge TCP port is reachable"
else
  echo "FAIL: Bridge TCP port is not reachable"
  exit 2
fi

echo "[4/5] Health endpoint check"
HEALTH_OUTPUT="$(curl -sS -m 8 -H "X-API-KEY: $MT5_BRIDGE_API_KEY" "$MT5_BRIDGE_URL/health" -w $'\nHTTP_STATUS:%{http_code}\n' || true)"
echo "$HEALTH_OUTPUT"
HEALTH_STATUS="$(echo "$HEALTH_OUTPUT" | awk -F: '/HTTP_STATUS/ {print $2}' | tr -d '[:space:]')"
if [[ "$HEALTH_STATUS" != "200" ]]; then
  echo "FAIL: /health returned HTTP $HEALTH_STATUS"
  exit 3
fi

echo "[5/5] Prices endpoint check"
PRICES_OUTPUT="$(curl -sS -m 12 -G \
  -H "X-API-KEY: $MT5_BRIDGE_API_KEY" \
  --data-urlencode "ticker=$SYMBOL" \
  --data-urlencode "start_date=$START_DATE" \
  --data-urlencode "end_date=$END_DATE" \
  --data-urlencode "timeframe=D1" \
  "$MT5_BRIDGE_URL/prices" \
  -w $'\nHTTP_STATUS:%{http_code}\n' || true)"
echo "$PRICES_OUTPUT"
PRICES_STATUS="$(echo "$PRICES_OUTPUT" | awk -F: '/HTTP_STATUS/ {print $2}' | tr -d '[:space:]')"
if [[ "$PRICES_STATUS" != "200" ]]; then
  echo "FAIL: /prices returned HTTP $PRICES_STATUS"
  exit 4
fi

echo "PASS: MT5 diagnostics completed successfully"
