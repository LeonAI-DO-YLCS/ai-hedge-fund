"""
CLI Main Entry Point: src/cli/__main__.py
=========================================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:405-410`.

Entry point for the management CLI.
"""

import argparse
from src.cli.flow_control import catalog_command, manifest_command
from src.cli.run_control import start_run_command, stop_run_command, monitor_run_command, audit_run_command

def main():
    parser = argparse.ArgumentParser(prog="hedge-fund-cli", description="AI Hedge Fund Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Catalog command
    cat_parser = subparsers.add_parser("catalog", help="Query backend catalogs")
    cat_parser.add_argument("category", nargs="?", default="all", choices=["all", "agents", "node-types", "swarms", "output-sinks", "mt5-symbols"], help="Catalog category")
    cat_parser.set_defaults(func=catalog_command)

    # Manifest command
    man_parser = subparsers.add_parser("manifest", help="Manage flow manifests")
    man_subparsers = man_parser.add_subparsers(dest="subaction", help="Manifest subaction")
    
    # Import
    imp_parser = man_subparsers.add_parser("import", help="Import a manifest file")
    imp_parser.add_argument("--file", required=True, help="Path to manifest JSON")
    
    # Export
    exp_parser = man_subparsers.add_parser("export", help="Export a manifest by flow ID")
    exp_parser.add_argument("flow_id", type=int, help="Backend flow ID")
    exp_parser.add_argument("--file", help="Optional path to save manifest JSON")
    
    # Validate
    val_parser = man_subparsers.add_parser("validate", help="Validate a flow manifest")
    val_parser.add_argument("flow_id", type=int, help="Backend flow ID")
    
    # Compile
    com_parser = man_subparsers.add_parser("compile", help="Compile a flow manifest")
    com_parser.add_argument("flow_id", type=int, help="Backend flow ID")
    
    man_parser.set_defaults(func=manifest_command)

    # Run commands (Placeholders)
    run_parser = subparsers.add_parser("run", help="Control flow runs")
    run_subparsers = run_parser.add_subparsers(dest="subaction", help="Run subaction")
    
    start_parser = run_subparsers.add_parser("start", help="Start a new run")
    start_parser.add_argument("flow_id", type=int, help="Flow ID to run")
    start_parser.add_argument("--profile", default="default", help="Run profile name")
    start_parser.set_defaults(func=start_run_command)

    stop_parser = run_subparsers.add_parser("stop", help="Cancel an in-progress run")
    stop_parser.add_argument("run_id", type=int, help="Run ID to stop")
    stop_parser.set_defaults(func=stop_run_command)

    mon_parser = run_subparsers.add_parser("monitor", help="Monitor a run via SSE")
    mon_parser.add_argument("run_id", type=int, help="Run ID to monitor")
    mon_parser.set_defaults(func=monitor_run_command)

    audit_parser = run_subparsers.add_parser("audit", help="Query run journal data")
    audit_parser.add_argument("run_id", type=int, help="Run ID to audit")
    audit_parser.add_argument("subaction", choices=["decisions", "trades", "artifacts", "provenance"], help="Journal category")
    audit_parser.set_defaults(func=audit_run_command)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if hasattr(args, "func"):
        args.func(args)
    else:
        print(f"No handler for command: {args.command}")

if __name__ == "__main__":
    main()
