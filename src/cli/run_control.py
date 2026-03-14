"""
CLI Run Control: src/cli/run_control.py
=======================================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:411-419`.

Implements run-scoped life-cycle and monitoring commands:
- `run start`: Launch a flow run.
- `run stop`: Cancel an in-progress run.
- `run monitor`: Stream SSE progress.
- `run audit`: Query journal data (decisions, trades, etc.).

TODO: Implement command logic using backend APIs (T032, T034).
"""

import requests
import json
import os
import sys
import time

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

def start_run_command(args):
    """Launch a governed run from a manifest."""
    flow_id = args.flow_id
    profile = getattr(args, "profile", "default")
    
    url = f"{BASE_URL}/runs/launch"
    try:
        response = requests.post(url, json={
            "flow_id": flow_id,
            "profile_name": profile,
            "live_intent_confirmed": True # CLI defaults to confirm if run is called
        })
        response.raise_for_status()
        data = response.json()
        print(f"Run launched successfully!")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error launching run: {e}", file=sys.stderr)
        sys.exit(1)

def stop_run_command(args):
    """Cancel an in-progress run."""
    run_id = args.run_id
    url = f"{BASE_URL}/runs/{run_id}/cancel"
    try:
        response = requests.post(url)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error stopping run: {e}", file=sys.stderr)
        sys.exit(1)

def monitor_run_command(args):
    """Monitor a run via SSE stream."""
    run_id = args.run_id
    url = f"{BASE_URL}/runs/{run_id}/events"
    
    try:
        # requests-sse or just raw stream handling
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        print(f"Started monitoring run {run_id}...")
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data:"):
                    event_data = decoded_line[5:].strip()
                    try:
                        event = json.loads(event_data)
                        print(f"[{event.get('timestamp', 'N/A')}] {event.get('agent', 'system')}: {event.get('status', '')}")
                    except:
                        print(decoded_line)
    except Exception as e:
        print(f"Error monitoring run: {e}", file=sys.stderr)
        sys.exit(1)

def audit_run_command(args):
    """Query journal data (decisions, trades, provenance)."""
    run_id = args.run_id
    subaction = args.subaction
    
    url = f"{BASE_URL}/runs/{run_id}/{subaction}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error fetching audit data: {e}", file=sys.stderr)
        sys.exit(1)
