"""
Flow Compiler Service
======================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
sections 6 (Validation), 8 (Compilation), 10 (Backend API).

Provides two primary compiler boundaries:
- **Validation**: structural, catalog, ID, and live-safety checks returning
  separate `errors[]` and `warnings[]` collections.
- **Compilation**: lowers a validated canonical manifest into runtime-safe
  `HedgeFundRequest` / `BacktestRequest` payloads, expands swarms, and
  produces compatibility projection and resolved-symbols placeholders.

Contracts:
- `specs/011-cli-flow-manifest/contracts/flow-validation-and-compilation-api.md`

TODO: Implement validation and compilation logic (T015, T016).
"""

from __future__ import annotations
from typing import Dict, List, Any
from app.backend.services.flow_catalog_service import FlowCatalogService
from app.backend.services.mt5_symbol_resolver_service import MT5SymbolResolverService


class FlowCompilerService:
    """Validates manifests and compiles them into runtime-safe request payloads.

    Blueprint reference: sections 6, 8, 10.
    Contract: flow-validation-and-compilation-api.md
    """

    def __init__(self, catalog_service: FlowCatalogService, resolver_service: MT5SymbolResolverService) -> None:
        self.catalog = catalog_service
        self.resolver = resolver_service

    def validate(self, manifest: dict) -> dict:
        """Validate a canonical manifest."""
        errors = []
        warnings = []
        
        # 1. Version validation
        v = manifest.get("manifest_version", "1.0")
        if v not in ["1.0"]:
            errors.append({"code": "V001", "path": "manifest_version", "message": f"Unsupported manifest version: {v}"})
            
        # 2. Structural checks
        nodes = manifest.get("nodes", [])
        if not nodes:
            errors.append({"code": "S001", "path": "nodes", "message": "Nodes list cannot be empty"})
            
        # 3. ID Uniqueness
        ids = [n.get("id") for n in nodes if n.get("id")]
        if len(ids) != len(set(ids)):
            errors.append({"code": "S002", "path": "nodes", "message": "Duplicate node IDs detected"})
            
        # 4. Catalog checks (Agents & Node Types)
        agent_keys = {a["agent_key"] for a in self.catalog.get_agents()}
        node_type_keys = {t["type_key"] for t in self.catalog.get_node_types()}
        
        for i, node in enumerate(nodes):
            n_type = node.get("type")
            n_id = node.get("id", f"node[{i}]")
            
            if n_type not in node_type_keys:
                errors.append({
                    "code": "C001", 
                    "path": f"nodes[{i}].type", 
                    "message": f"Unknown node type: {n_type}"
                })
                
            if n_type == "analyst":
                a_key = node.get("agent_key")
                if not a_key:
                    errors.append({
                        "code": "C002", 
                        "path": f"nodes[{i}].agent_key", 
                        "message": "Analyst node missing agent_key"
                    })
                elif a_key not in agent_keys:
                    errors.append({
                        "code": "C003", 
                        "path": f"nodes[{i}].agent_key", 
                        "message": f"Unknown agent key: {a_key}"
                    })
                    
        # 5. Topology legality (Cycles, Isolate nodes)
        adj = {}
        for edge in manifest.get("edges", []):
            s = edge.get("source")
            t = edge.get("target")
            if s and t:
                adj.setdefault(s, []).append(t)
        
        visited = set()
        path = set()
        
        def has_cycle(u):
            visited.add(u)
            path.add(u)
            for v in adj.get(u, []):
                if v not in visited:
                    if has_cycle(v):
                        return True
                elif v in path:
                    return True
            path.remove(u)
            return False
            
        for node in nodes:
            nid = node.get("id")
            if nid and nid not in visited:
                if has_cycle(nid):
                    errors.append({
                        "code": "T001",
                        "path": "edges",
                        "message": f"Cycle detected starting from node: {nid}"
                    })
                    break
        
        # 6. Warnings (e.g. legacy compatibility issues)
        if any("-" in nid for nid in ids):
            warnings.append({
                "code": "W001", 
                "path": "nodes", 
                "message": "Heuristic: using hyphenated IDs in canonical manifest is discouraged as they may conflict with legacy suffixes"
            })
            
        # 7. Symbols availability check (Diagnostic)
        symbol_catalog = self.catalog.get_mt5_symbols()
        if symbol_catalog.get("status") != "ready":
            warnings.append({
                "code": "W002",
                "path": "symbols",
                "message": f"MT5 bridge is {symbol_catalog.get('status')}; symbol resolution may be degraded",
                "details": symbol_catalog.get("error")
            })

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "catalog_versions": {
                "agents": "1.0",
                "node_types": "1.0",
                "mt5_symbols": symbol_catalog.get("count", 0)
            }
        }

    def compile(self, manifest: dict) -> dict:
        """Compile a validated manifest into runtime-safe request structures.

        Lowering logic (blueprint section 8):
        1. Resolve all stable IDs to runtime-safe identifiers.
        2. Expand swarms into individual analyst nodes based on swarm templates.
        3. Resolve instrument tickers to MT5 symbols with provenance capture.
        4. Project the graph into a flat representation compatible with legacy handlers.
        """
        nodes = manifest.get("nodes", [])
        edges = manifest.get("edges", [])
        input_resolution = manifest.get("input_resolution", {})
        
        # 1. Resolve Symbols
        tickers = input_resolution.get("static_tickers", [])
        resolution = self.resolver.resolve_symbols(tickers)
        
        compiled_nodes = []
        expansion_map = {}  # swarm_id -> [node_ids]
        id_map = {}  # canonical -> runtime
        
        # 2. Expand Swarms and Normalize IDs
        swarm_templates = {s["swarm_id"]: s for s in self.catalog.get_swarms()}
        
        for node in nodes:
            can_id = node.get("id")
            n_type = node.get("type")
            
            if n_type == "swarm":
                swarm_id = node.get("swarm_id")
                template = swarm_templates.get(swarm_id)
                
                if not template:
                    # Fallback if template missing, shouldn't happen if validated
                    expansion_map[can_id] = []
                    continue
                
                members = template.get("membership", [])
                expanded_node_ids = []
                
                for i, member in enumerate(members):
                    member_agent_key = member.get("agent_key")
                    # Generate a unique stable ID for the expanded member
                    member_id = f"{can_id}_{member_agent_key}_{i+1}"
                    expanded_node_ids.append(member_id)
                    
                    # Merge template member config with node config overrides
                    member_config = member.copy()
                    overrides = node.get("config_overrides", {})
                    if member_agent_key in overrides:
                        member_config.update(overrides[member_agent_key])
                    
                    compiled_nodes.append({
                        "id": member_id,
                        "type": "analyst",
                        "agent_key": member_agent_key,
                        "config": member_config,
                        "parent_swarm": can_id,
                        "swarm_id": swarm_id
                    })
                
                expansion_map[can_id] = expanded_node_ids
            else:
                # Regular node normalization
                runtime_id = can_id # Keep stable ID as canonical unless collision handling needed
                id_map[can_id] = runtime_id
                
                new_node = node.copy()
                new_node["id"] = runtime_id
                compiled_nodes.append(new_node)
                
        # 3. Map Edges (handling swarm expansion)
        compiled_edges = []
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            
            # Resolve source nodes (could be one or multiple due to swarm)
            sources = expansion_map.get(source, [id_map.get(source, source)])
            # Resolve target nodes
            targets = expansion_map.get(target, [id_map.get(target, target)])
            
            for s in sources:
                for t in targets:
                    new_edge = edge.copy()
                    new_edge["source"] = s
                    new_edge["target"] = t
                    compiled_edges.append(new_edge)
            
        # 4. Build Compatibility Projection
        # This is essentially the legacy payload shape
        compatibility_projection = {
            "name": manifest.get("name"),
            "nodes": compiled_nodes,
            "edges": compiled_edges,
            "data": manifest.get("agent_runtime", {})
        }

        return {
            "compiled_request": {
                "nodes": compiled_nodes,
                "edges": compiled_edges,
                "tickers": tickers,
                "mt5_symbols": [s["mt5_symbol"] for s in resolution.get("symbols", [])],
                "agent_runtime": manifest.get("agent_runtime", {}),
                "provenance": resolution
            },
            "compatibility_projection": compatibility_projection,
            "expansion_map": expansion_map,
            "resolved_symbols": resolution.get("symbols", []),
            "warnings": resolution.get("diagnostics", [])
        }
