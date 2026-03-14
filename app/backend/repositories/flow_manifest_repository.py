"""
Flow Manifest Repository
=========================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
sections 10 (Persistence), lines 69, 393.

Provides canonical manifest persistence and lifecycle query helpers.
All database access for manifest domain must go through here — never in routes.

Contracts:
- `specs/011-cli-flow-manifest/contracts/flow-manifest-schema-and-lifecycle.md`
- `specs/011-cli-flow-manifest/contracts/identifier-compatibility-and-instance-resolution.md`

TODO: Implement full CRUD and query operations (T008, T030).
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.backend.database.models import CanonicalManifest, IdentifierMapping


class FlowManifestRepository:
    """Persistence helpers for canonical manifests and compatibility mappings.

    Blueprint reference: sections 10 (lines 69, 393).
    Contracts: flow-manifest-schema-and-lifecycle.md,
               identifier-compatibility-and-instance-resolution.md
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_manifest(self, payload: dict) -> CanonicalManifest:
        """Create a new canonical manifest record."""
        manifest = CanonicalManifest(
            flow_id=payload.get("flow_id"),
            manifest_version=payload.get("manifest_version", "1.0"),
            name=payload.get("name", "Unnamed Flow"),
            description=payload.get("description"),
            payload=payload,  # The whole thing
            is_template=payload.get("is_template", False),
            tags=payload.get("tags", []),
        )
        self.db.add(manifest)
        self.db.commit()
        self.db.refresh(manifest)
        return manifest

    def get_manifest_by_flow_id(self, flow_id: int) -> CanonicalManifest | None:
        """Fetch the latest canonical manifest for a given flow reference."""
        return (
            self.db.query(CanonicalManifest)
            .filter(CanonicalManifest.flow_id == flow_id)
            .order_by(desc(CanonicalManifest.created_at))
            .first()
        )

    def get_manifest_by_version(self, flow_id: int, version: str) -> CanonicalManifest | None:
        """Fetch a specific manifest version."""
        return (
            self.db.query(CanonicalManifest)
            .filter(
                CanonicalManifest.flow_id == flow_id,
                CanonicalManifest.manifest_version == version
            )
            .first()
        )

    def update_manifest(self, flow_id: int, payload: dict) -> CanonicalManifest:
        """Update an existing canonical manifest by creating a new versioned entry."""
        # Note: In a versioned system, "update" often means insert new.
        # But if we want to update the latest one if it hasn't been used yet?
        # The blueprint suggests versioned records.
        return self.create_manifest(payload)

    def upsert_compatibility_mapping(self, flow_id: int, mappings: list[dict]) -> None:
        """Insert or update identifier compatibility mappings for a flow.

        Each mapping dict should have: mapping_scope, canonical_id, legacy_id, source.
        """
        for m in mappings:
            existing = (
                self.db.query(IdentifierMapping)
                .filter(
                    IdentifierMapping.flow_id == flow_id,
                    IdentifierMapping.mapping_scope == m["mapping_scope"],
                    IdentifierMapping.canonical_id == m["canonical_id"]
                )
                .first()
            )
            if existing:
                existing.legacy_id = m["legacy_id"]
                existing.source = m.get("source", existing.source)
                existing.active = m.get("active", True)
            else:
                mapping = IdentifierMapping(
                    flow_id=flow_id,
                    mapping_scope=m["mapping_scope"],
                    canonical_id=m["canonical_id"],
                    legacy_id=m["legacy_id"],
                    source=m.get("source"),
                    active=m.get("active", True)
                )
                self.db.add(mapping)
        self.db.commit()

    def get_compatibility_mappings(self, flow_id: int) -> list[IdentifierMapping]:
        """Return all compatibility mappings for a flow."""
        return (
            self.db.query(IdentifierMapping)
            .filter(IdentifierMapping.flow_id == flow_id, IdentifierMapping.active == True)
            .all()
        )

    def compose_export_bundle(
        self,
        flow_id: int,
        include_compiled: bool = False,
        include_runtime: bool = False,
    ) -> dict:
        """Compose an export bundle for a flow with optional compiled/runtime context.

        TODO (T030): Integrate with RunJournalRepository for runtime snapshots.
        """
        manifest = self.get_manifest_by_flow_id(flow_id)
        if not manifest:
            return {}

        bundle = {
            "manifest": manifest.payload,
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "flow_id": flow_id,
                "version": manifest.manifest_version
            }
        }
        
        if include_compiled:
            # Placeholder for compiled view logic
            bundle["compiled_view"] = {}

        return bundle
