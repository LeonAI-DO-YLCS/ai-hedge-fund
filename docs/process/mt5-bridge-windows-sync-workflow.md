# MT5 Bridge Windows Sync Workflow

## Purpose

This runbook defines how to keep the MT5 bridge source repository in WSL/Linux and the Windows runtime clone in sync while preserving Git history and a working Windows-native MT5 runtime.

## Canonical Locations

- WSL source repo: `mt5-connection-bridge/`
- Windows runtime clone: `C:\Trading\System-Tools\mt5-connection-bridge`
- GitHub remote: `https://github.com/LeonAI-DO-YLCS/mt5-connection-bridge.git`

## Source Of Truth

- GitHub is the shared source of truth for history and synchronization.
- The WSL repo is the primary development copy.
- The Windows clone is the primary runtime copy for live MT5 execution.
- Do not rely on raw folder copies as a long-term sync strategy.

## Recommended Rule

- Make code changes in the WSL repo first.
- Commit and push from the WSL repo.
- Update the Windows runtime clone from GitHub.
- Keep `.env` and runtime logs local to the Windows runtime clone.

## Helper Script

Use the helper script from the parent repo when you want to refresh the Windows runtime clone from WSL:

```bash
./scripts/refresh_windows_mt5_bridge.sh
```

What it does:

- backs up the Windows clone `.env`
- backs up `logs/runtime_state.json`
- stops the bridge listener on port `8001`
- re-clones `C:\Trading\System-Tools\mt5-connection-bridge` from GitHub
- restores the backed-up runtime files
- reinstalls Windows Python dependencies
- restarts the Windows-native bridge
- checks `/health` after startup when an API key is available

Useful options:

```bash
./scripts/refresh_windows_mt5_bridge.sh --no-start
./scripts/refresh_windows_mt5_bridge.sh --skip-install
./scripts/refresh_windows_mt5_bridge.sh --help
```

## Standard Update Workflow

### 1. Make and validate code changes in WSL

Work in:

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge
```

Run validation as needed, then commit and push:

```bash
git status
git add .
git commit -m "<message>"
git push origin main
```

### 2. Stop the Windows runtime bridge

Stop the running Windows bridge process before updating the runtime clone.

If you are using the helper script, this step is handled automatically.

Example from WSL:

```bash
powershell.exe -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort 8001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
```

### 3. Back up local runtime-only files from the Windows clone

Preserve:

- `C:\Trading\System-Tools\mt5-connection-bridge\.env`
- `C:\Trading\System-Tools\mt5-connection-bridge\logs\runtime_state.json`

Optional preserve:

- `logs\trades.jsonl`
- `logs\metrics.jsonl`
- any launcher or stderr/stdout logs you want to keep

### 4. Update the Windows runtime clone from GitHub

If you are using the helper script, this step is handled automatically with a clean re-clone.

Preferred clean update:

```powershell
cd C:\Trading\System-Tools
if (Test-Path .\mt5-connection-bridge) { Remove-Item -Recurse -Force .\mt5-connection-bridge }
git clone https://github.com/LeonAI-DO-YLCS/mt5-connection-bridge.git
```

Alternative in-place update if the clone is already healthy and clean:

```powershell
cd C:\Trading\System-Tools\mt5-connection-bridge
git fetch origin
git checkout main
git pull --ff-only origin main
```

### 5. Restore runtime-only files

If you are using the helper script, this step is handled automatically.

Restore:

- `.env`
- `logs\runtime_state.json`

Do not restore old `.git` metadata from copied folders.

### 6. Ensure Windows Python dependencies exist

If you are using the helper script, this step is handled automatically unless you pass `--skip-install`.

Recommended interpreter used in this environment:

```text
C:\Users\LeonAI-DO\AppData\Local\Programs\Python\Python312\python.exe
```

Install bridge requirements if needed:

```powershell
cd C:\Trading\System-Tools\mt5-connection-bridge
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pip install requests
```

Note: `requests` must be available because the bridge fundamentals routes import it directly.

### 7. Start the Windows bridge

If you are using the helper script, this step is handled automatically unless you pass `--no-start`.

Example:

```powershell
cd C:\Trading\System-Tools\mt5-connection-bridge
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Or launch it in the background with your preferred PowerShell wrapper.

### 8. Verify runtime health

From WSL:

```bash
curl -sS -H "X-API-KEY: <api-key>" http://localhost:8001/health
curl -sS -H "X-API-KEY: <api-key>" http://localhost:8001/readiness
curl -sS -H "X-API-KEY: <api-key>" http://localhost:8001/diagnostics/runtime
```

Expected:

- `connected=true`
- `authorized=true`
- worker state ready/authorized

## Git Verification Checklist

### WSL repo

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge
git remote -v
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
```

### Windows repo

Use Windows Git for the cleanest status check:

```cmd
cd /d C:\Trading\System-Tools\mt5-connection-bridge
git remote -v
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
git status --short --branch
```

Both repos should show:

- branch `main`
- same `HEAD`
- same `origin`

## Important Operational Notes

### 1. Do not develop primarily in the Windows runtime clone

Treat the Windows clone as deploy/runtime first. If you make emergency changes there, sync them back to GitHub immediately so the WSL repo does not drift.

### 2. Avoid copying `.git` from WSL into Windows

A raw copy from WSL can leave a broken `.git` pointer, especially if the source is a submodule or has repo-relative gitdir metadata.

### 3. Do not trust Linux `git status` on `/mnt/c` for the final cleanliness check

When possible, inspect the Windows clone with Windows Git. Line endings and Windows filesystem behavior can make the Linux-side status look noisy even when the Windows repo is fine.

### 4. Keep runtime secrets local

`.env` should remain local to the Windows runtime clone and should not be committed.

### 5. Runtime state may matter

`logs\runtime_state.json` can preserve execution policy state. Restore it carefully, and always verify whether `execution_enabled` is set correctly after startup.

## Emergency Hotfix Workflow

If you must patch the Windows runtime clone directly:

1. Make the smallest possible code change in `C:\Trading\System-Tools\mt5-connection-bridge`
2. Commit it there with Git
3. Push it to GitHub
4. Pull the same commit into the WSL repo
5. Re-validate both copies show the same `HEAD`

Do not leave Windows-only code changes uncommitted.

## Known Pitfalls From This Session

- The bridge may fail to start when executed from a `\\wsl.localhost\...` path.
- The Linux wrapper can stop early if Linux-side dependencies are missing, even when the real target runtime is Windows.
- The default `python.exe` on Windows may not be the correct interpreter for the bridge.
- The Windows Python runtime can appear mostly ready but still miss an import such as `requests`.
- A copied runtime folder can run successfully for a moment while not being a valid Git clone.

## Recommended Ongoing Practice

- Keep WSL as the dev repo
- Keep Windows as the runtime clone
- Push to GitHub before refreshing Windows
- Refresh Windows from GitHub, not from ad hoc folder copies
- Re-run bridge health, readiness, and a minimal smoke test after every update

## Related Documents

- `docs/planning/mt5-bridge-terminal-testing-blueprint.md`
- `docs/planning/mt5-bridge-terminal-test-checklist.md`
- `docs/reports/008-close-mt5-gaps-2026-03-13/report.md`
