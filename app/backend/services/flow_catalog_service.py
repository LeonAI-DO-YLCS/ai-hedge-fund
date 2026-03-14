"""
Flow Catalog Service
====================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
sections 5 (Catalog), 6 (Flow Authoring Surface), 10 (Backend API).

Exposes backend-owned, machine-readable catalogs covering:
- Agent / analyst definitions
- Node type registry
- Swarm templates (source-controlled YAML)
- Output sinks
- MT5-backed symbol catalog

Contracts:
- `specs/011-cli-flow-manifest/contracts/flow-catalog-api.md`

TODO: Implement full catalog service logic (T011, T012).
"""

import os
import yaml
from glob import glob
from datetime import datetime
from app.backend.services.mt5_bridge_service import mt5_bridge_service
from src.utils.analysts import ANALYST_CONFIG


class FlowCatalogService:
    """Provides discoverable catalog payloads for all five contract families.

    Blueprint reference: sections 5, 6, 10.
    Contract family: flow-catalog-api.md
    """

    def __init__(self, swarm_config_dir: str = "app/backend/config/swarms") -> None:
        self.swarm_config_dir = swarm_config_dir

    def get_agents(self) -> list[dict]:
        """Return analyst/agent catalog entries."""
        items = []
        for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1].get("order", 0)):
            items.append({
                "agent_key": key,
                "display_name": config["display_name"],
                "description": config["description"],
                "agent_type": config.get("type", "analyst"),
                "default_order": config.get("order", 0),
                "supported_node_category": "analyst",
                "configurable_runtime_fields": [
                    "model_name",
                    "model_provider",
                    "fallback_model_name",
                    "fallback_model_provider",
                    "system_prompt_override",
                    "temperature",
                    "max_tokens"
                ]
            })
        return items

    def get_node_types(self) -> list[dict]:
        """Return node type registry entries."""
        return [
            {
                "type_key": "stock_input",
                "category": "input",
                "display_name": "Stock Input",
                "allowed_inbound": [],
                "allowed_outbound": ["analysis"],
                "required_fields": ["node_id"],
                "optional_fields": ["static_tickers", "resolution_mode"],
                "compiler_strategy": "input-resolver"
            },
            {
                "type_key": "analyst",
                "category": "analysis",
                "display_name": "Analyst Node",
                "allowed_inbound": ["input", "swarm"],
                "allowed_outbound": ["analysis", "swarm"],
                "required_fields": ["node_id", "agent_key"],
                "optional_fields": ["config", "runtime_overrides"],
                "compiler_strategy": "graph-runtime-node"
            },
            {
                "type_key": "swarm",
                "category": "analysis",
                "display_name": "Swarm Node",
                "allowed_inbound": ["input"],
                "allowed_outbound": ["analysis", "decision"],
                "required_fields": ["node_id", "swarm_id"],
                "optional_fields": ["config_overrides"],
                "compiler_strategy": "swarm-expansion-macro"
            },
            {
                "type_key": "portfolio_manager",
                "category": "decision",
                "display_name": "Portfolio Manager",
                "allowed_inbound": ["analysis"],
                "allowed_outbound": ["execution", "risk"],
                "required_fields": ["node_id"],
                "optional_fields": ["risk_threshold", "max_position_size"],
                "compiler_strategy": "graph-runtime-node"
            },
            {
                "type_key": "risk_manager",
                "category": "risk",
                "display_name": "Risk Manager",
                "allowed_inbound": ["decision"],
                "allowed_outbound": ["execution", "rejection"],
                "required_fields": ["node_id"],
                "optional_fields": ["limit_rules"],
                "compiler_strategy": "graph-runtime-node"
            },
            {
                "type_key": "output_sink",
                "category": "output",
                "display_name": "Output Sink",
                "allowed_inbound": ["decision", "analysis", "risk"],
                "allowed_outbound": [],
                "required_fields": ["node_id", "sink_id"],
                "optional_fields": ["format", "retention"],
                "compiler_strategy": "post-run-processor"
            }
        ]

    def get_swarms(self) -> list[dict]:
        """Return swarm template catalog entries loaded from YAML."""
        items = []
        pattern = os.path.join(self.swarm_config_dir, "*.yaml")
        for file_path in glob(pattern):
            try:
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)
                    if data:
                        items.append(data)
            except Exception:
                continue
        return items

    def get_output_sinks(self) -> list[dict]:
        """Return output sink catalog entries."""
        return [
            {
                "sink_key": "run-journal",
                "display_name": "Standard Run Journal",
                "delivery_modes": ["persisted", "streamed"],
                "artifact_types": ["audit-logs", "portfolio-snapshots"]
            },
            {
                "sink_key": "mt5-executor",
                "display_name": "MT5 Trade Executor",
                "delivery_modes": ["paper", "live-intent"],
                "artifact_types": ["trade-records", "order-logs"]
            }
        ]

    def get_mt5_symbols(self) -> dict:
        """Return MT5 symbol catalog entries with availability status."""
        return mt5_bridge_service.get_symbols()
