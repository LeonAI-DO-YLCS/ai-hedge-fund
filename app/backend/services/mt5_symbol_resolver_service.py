"""
MT5 Symbol Resolver Service
============================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
sections 9 (Symbol Resolution), 10 (Backend API).

Resolves instrument symbol universes for a given flow manifest using one of:
- `static`   — symbols listed directly in the manifest
- `portfolio` — derived from the current portfolio composition
- `mt5`      — queried live from the MT5 bridge
- `external` — future-compatible external data source

Always returns an auditable provenance snapshot, even under degraded MT5 conditions.
Graceful degradation (empty or partial results with explicit diagnostics) is mandatory.

Contracts:
- `specs/011-cli-flow-manifest/contracts/mt5-symbol-resolution-and-provenance.md`

TODO: Implement full resolution and provenance logic (T022).
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Any
from app.backend.services.mt5_bridge_service import mt5_bridge_service


class MT5SymbolResolverService:
    """Handles resolution of tickers to MT5 symbols with provenance and degradation support.

    Blueprint reference: sections 8, 10.
    Contract: mt5-symbol-resolution-and-provenance.md
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}
        self._last_refresh: datetime | None = None

    def resolve_symbols(self, tickers: list[str]) -> dict:
        """Resolve a list of tickers to MT5 symbols.

        Returns: { "status": "ready"|"degraded", "symbols": [...], "diagnostics": [...] }
        """
        # 1. Try to get fresh catalog from bridge
        catalog = mt5_bridge_service.get_symbols()
        status = catalog.get("status", "unavailable")
        
        # 2. Update cache if bridge is healthy
        if status == "ready":
            new_cache = {s["ticker"]: s["mt5_symbol"] for s in catalog.get("symbols", [])}
            self._cache.update(new_cache)
            self._last_refresh = datetime.utcnow()
            
        # 3. Resolve tickers using cache or bridge data
        resolved = []
        diagnostics = []
        
        if status != "ready":
            diagnostics.append(f"Using cached symbol resolution due to bridge status: {status}")
            if catalog.get("error"):
                diagnostics.append(f"Bridge Error: {catalog.get('error')}")

        for ticker in tickers:
            symbol = self._cache.get(ticker)
            if symbol:
                resolved.append({"ticker": ticker, "mt5_symbol": symbol, "source": "cache" if status != "ready" else "bridge"})
            else:
                diagnostics.append(f"Could not resolve ticker: {ticker}")
                
        final_status = "ready" if status == "ready" and len(resolved) == len(tickers) else "degraded"
        
        return {
            "status": final_status,
            "resolved_at": datetime.utcnow().isoformat(),
            "symbols": resolved,
            "diagnostics": diagnostics,
            "bridge_snapshot": {
                "status": status,
                "error": catalog.get("error")
            }
        }

    def get_provenance_snapshot(self) -> dict:
        """Return a snapshot of current symbol resolution state and bridge health."""
        status = mt5_bridge_service.get_connection_status()
        return {
            "resolved_at": datetime.utcnow().isoformat(),
            "bridge": status,
            "cache_size": len(self._cache),
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None
        }
