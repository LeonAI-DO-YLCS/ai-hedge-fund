"""
Flow Manifest Service
=====================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
sections 5 (Manifest Schema), 7 (Validation), 10 (Backend API).

Manages the lifecycle of canonical flow manifests:
- Authoring, loading, storing, versioning, and exporting
- Legacy flow projection (compatibility view) translation
- Identifier normalization and compatibility mappings
- Run-profile persistence and resolution

Contracts:
- `specs/011-cli-flow-manifest/contracts/flow-manifest-schema-and-lifecycle.md`
- `specs/011-cli-flow-manifest/contracts/identifier-compatibility-and-instance-resolution.md`

TODO: Implement full manifest service logic (T013, T014, T009, T021).
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from app.backend.repositories.flow_manifest_repository import FlowManifestRepository
from app.backend.services.graph import extract_base_agent_key


class FlowManifestService:
    """Manages canonical manifest lifecycle and legacy compatibility projections.

    Blueprint reference: sections 5, 7, 10.
    Contracts: flow-manifest-schema-and-lifecycle.md,
               identifier-compatibility-and-instance-resolution.md
    """

    def __init__(self, manifest_repo: FlowManifestRepository) -> None:
        self.repo = manifest_repo

    def normalize_canonical_id(self, raw_id: str) -> str:
        """
        Produce a stable, slug-based ID from a raw (often UI-generated) ID.
        Blueprint Section 6.3: IDs should be stable and slug-based.
        """
        # If it's already a clean slug without a 6-char random suffix, use it
        base = extract_base_agent_key(raw_id)
        if base == raw_id:
            return raw_id
            
        # If it had a suffix, we keep the base but we might need to de-duplicate 
        # in the calling context (import_manifest). This helper just cleans the suffix.
        return base

    def get_legacy_mapping(self, flow_id: int, canonical_id: str) -> str | None:
        """Look up a registered legacy ID for a canonical reference."""
        mappings = self.repo.get_compatibility_mappings(flow_id)
        for m in mappings:
            if m.canonical_id == canonical_id:
                return m.legacy_id
        return None

    def establish_mappings(self, flow_id: int, manifest: dict) -> list[dict]:
        """Establish compatibility mappings for a newly imported manifest."""
        mappings = []
        
        # Nodes
        for i, node in enumerate(manifest.get("nodes", []), 1):
            can_id = node.get("id")
            if not can_id:
                continue
            
            # If manifest has an explicit legacy mapping hint, use it
            legacy_id = can_id
            if "-" not in can_id:
                legacy_id = f"{can_id}-{i}"
            
            mappings.append({
                "mapping_scope": "node",
                "canonical_id": can_id,
                "legacy_id": legacy_id,
                "source": "import"
            })
            
        self.repo.upsert_compatibility_mapping(flow_id, mappings)
        return mappings

    def create_manifest(self, payload: dict) -> dict:
        """Author and store a new canonical manifest."""
        # Ensure manifest version
        if "manifest_version" not in payload:
            payload["manifest_version"] = "1.0"
            
        manifest = self.repo.create_manifest(payload)
        return manifest.payload

    def get_manifest(self, flow_id: int) -> dict:
        """Load a canonical manifest by flow reference."""
        manifest = self.repo.get_manifest_by_flow_id(flow_id)
        if not manifest:
            return {}
        return manifest.payload

    def export_manifest(self, flow_id: int, include_runtime: bool = False) -> dict:
        """Export a canonical manifest, stripping secrets and env-specific values.

        Rules (blueprint section 11):
        - Strip keys like 'api_key', 'broker_password', 'bridge_secret'.
        - Optionally include compiled snapshots.
        """
        bundle = self.repo.compose_export_bundle(flow_id, include_runtime=include_runtime)
        if not bundle:
            return {}
            
        # Recursive secret stripping
        def strip_secrets(obj):
            if isinstance(obj, dict):
                return {k: strip_secrets(v) for k, v in obj.items() if not any(s in k.lower() for s in ["api_key", "secret", "password", "token"])}
            elif isinstance(obj, list):
                return [strip_secrets(i) for i in obj]
            return obj
            
        if "manifest" in bundle:
            bundle["manifest"] = strip_secrets(bundle["manifest"])
            
        return bundle

    def import_manifest(self, manifest_payload: dict) -> dict:
        """Import a canonical manifest and materialize a legacy compatibility projection."""
        # Note: True import involves validation (T018) and legacy model creation (T014).
        # For now, we store if valid (assuming valid for this step).
        
        # 1. Store canonical
        manifest_record = self.repo.create_manifest(manifest_payload)
        
        # 2. Establish mappings
        if manifest_record.flow_id:
            self.establish_mappings(manifest_record.flow_id, manifest_payload)
            
        return manifest_record.payload

    def to_legacy_projection(self, manifest: dict) -> dict:
        """Translate a canonical manifest into the legacy /flows payload shape."""
        nodes = []
        edges = []
        
        # 1. Map Nodes
        for i, m_node in enumerate(manifest.get("nodes", []), 1):
            can_id = m_node.get("id")
            if not can_id:
                continue
                
            # Use established legacy mapping if available (requires flow_id context usually,
            # but here we generate a stable one for the projection)
            legacy_id = f"{can_id}-{i}"
            
            nodes.append({
                "id": legacy_id,
                "type": m_node.get("type", "analyst"),
                "data": m_node.get("config", {}),
                "position": m_node.get("metadata", {}).get("position", {"x": i * 250, "y": 100}),
                "dragging": False,
                "selected": False,
            })
            
        # 2. Map Edges (requires ID translation)
        # For simplicity, we assume edge sources/targets in manifest are canonical IDs
        # We need to find their legacy counterparts
        id_map = {n["id"].split("-")[0]: n["id"] for n in nodes if "-" in n["id"]}
        
        for i, m_edge in enumerate(manifest.get("edges", []), 1):
            source_can = m_edge.get("source")
            target_can = m_edge.get("target")
            
            source_legacy = id_map.get(source_can, source_can)
            target_legacy = id_map.get(target_can, target_can)
            
            edges.append({
                "id": f"e-{source_legacy}-{target_legacy}",
                "source": source_legacy,
                "target": target_legacy,
                "animated": True,
            })
            
        return {
            "name": manifest.get("name", "Imported Flow"),
            "description": manifest.get("description"),
            "nodes": nodes,
            "edges": edges,
            "data": {
                "agent_runtime": manifest.get("agent_runtime", {}),
                "swarms": manifest.get("swarms", []),
                "inputs": manifest.get("input_resolution", {})
            }
        }

    def get_run_profiles(self, flow_id: int) -> list[dict]:
        """Return named run profiles attached to a saved flow."""
        manifest = self.get_manifest(flow_id)
        return manifest.get("run_profiles", [])
