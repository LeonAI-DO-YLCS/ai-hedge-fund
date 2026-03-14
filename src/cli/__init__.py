"""
CLI Package: src/cli
====================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
lines 395-407.

Provides a backend-API-driven CLI control plane. All commands talk to the backend
HTTP APIs only — no direct database access or MT5 bridge connections.

Sub-modules:
- flow_control: catalog discovery, manifest lifecycle (create/validate/compile/import/export)
- run_control: run start, stream, status, cancel, artifact inspection
"""
