"""
CLI Flow Control: src/cli/flow_control.py
=========================================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:397-404`.

Implements catalog discovery and manifest lifecycle commands:
- `catalog` (agents, nodes, swarms, sinks, symbols)
- `validate`
- `compile`
- `import`
- `export`

TODO: Implement command logic using backend APIs (T019, T033).
"""

import requests
import json
import os
import sys

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 15

def catalog_command(args):
    """Retrieve and display catalog information."""
    category = args.category
    url = f"{BASE_URL}/flow-catalog"
    if category != "all":
        url = f"{BASE_URL}/flow-catalog/{category}"
        
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, indent=2))
    except requests.exceptions.ConnectionError:
        print(f"Error: Unable to connect to backend at {BASE_URL}. Is it running?", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"Error: Request to backend timed out.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"API Error fetching catalog: {e}", file=sys.stderr)
        if 'response' in locals() and hasattr(response, "text"):
            print(f"Details: {response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error fetching catalog: {e}", file=sys.stderr)
        sys.exit(1)

def manifest_command(args):
    """Manage flow manifests: import, export, validate, compile."""
    subaction = args.subaction
    flow_id = getattr(args, "flow_id", None)
    file_path = getattr(args, "file", None)
    
    try:
        if subaction == "import":
            if not file_path:
                print("Error: --file required for import", file=sys.stderr)
                sys.exit(1)
            with open(file_path, "r") as f:
                manifest = json.load(f)
            url = f"{BASE_URL}/flows/import"
            response = requests.post(url, json={"manifest": manifest, "options": {}}, timeout=TIMEOUT)
            
        elif subaction == "export":
            url = f"{BASE_URL}/flows/export/{flow_id}"
            response = requests.get(url, timeout=TIMEOUT)
            
        elif subaction == "validate":
            url = f"{BASE_URL}/flows/{flow_id}/validate"
            response = requests.post(url, timeout=TIMEOUT)
            
        elif subaction == "compile":
            url = f"{BASE_URL}/flows/{flow_id}/compile"
            response = requests.post(url, timeout=TIMEOUT)
            
        else:
            print(f"Unknown subaction: {subaction}", file=sys.stderr)
            sys.exit(1)
            
        response.raise_for_status()
        data = response.json()
        
        if subaction == "export" and file_path:
            dir_name = os.path.dirname(file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Manifest exported to {file_path}")
        else:
            print(json.dumps(data, indent=2))
            
    except requests.exceptions.ConnectionError:
        print(f"Error: Unable to connect to backend at {BASE_URL}. Is it running?", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"Error: Request to backend timed out.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"API Error during {subaction}: {e}", file=sys.stderr)
        if 'response' in locals() and hasattr(response, "text"):
            print(f"Details: {response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during {subaction}: {e}", file=sys.stderr)
        sys.exit(1)
