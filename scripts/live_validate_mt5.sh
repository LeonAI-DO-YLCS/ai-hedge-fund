#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

JOURNAL="docs/mt5-validation-journal-2026-03-02.md"
RUN_LOG="tmp_ignore/deepseek_analysts_all_validation.log"

mkdir -p docs tmp_ignore
touch "$JOURNAL" "$RUN_LOG"

event() {
  printf '[%s] %s\n' "$(date -Iseconds)" "$1" | tee -a "$JOURNAL"
}

event "Step 9: Live validation runner started (deepseek-chat, analysts-all, ticker=V75)."
event "Step 10: Launching app with unbuffered output and per-line journal logging."

set +e
PYTHONUNBUFFERED=1 uv run python -u -m src.main \
  --tickers V75 \
  --analysts-all \
  --start-date 2026-02-01 \
  --end-date 2026-02-10 \
  --model deepseek-chat 2>&1 | while IFS= read -r line; do
    printf '%s\n' "$line" >> "$RUN_LOG"
    printf '[%s] APP: %s\n' "$(date -Iseconds)" "$line" >> "$JOURNAL"
    printf '%s\n' "$line"
  done
EXIT_CODE=${PIPESTATUS[0]}
set -e

event "Step 11: Live validation command finished with exit code $EXIT_CODE."
exit "$EXIT_CODE"
