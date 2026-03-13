from __future__ import annotations

from typing import Dict, Mapping
from types import MappingProxyType

from .types import PortfolioSnapshot, PositionState, TickerRealizedGains


class Portfolio:
    """Portfolio state management for backtesting operations.

    Encapsulates cash, positions, and margin tracking.
    Supports both long and short positions with proper cost basis tracking
    and realized gains/losses calculation.
    """

    def __init__(
        self,
        *,
        tickers: list[str],
        initial_cash: float,
        margin_requirement: float,
    ) -> None:
        self._portfolio: PortfolioSnapshot = {
            "cash": float(initial_cash),
            "margin_used": 0.0,
            "margin_requirement": float(margin_requirement),
            "positions": {
                ticker: {
                    "long": 0.0,
                    "short": 0.0,
                    "long_cost_basis": 0.0,
                    "short_cost_basis": 0.0,
                    "short_margin_used": 0.0,
                }
                for ticker in tickers
            },
            "realized_gains": {
                ticker: {"long": 0.0, "short": 0.0}
                for ticker in tickers
            },
        }

    def get_snapshot(self) -> PortfolioSnapshot:
        positions_copy: Dict[str, PositionState] = {
            t: {
                "long": p["long"],
                "short": p["short"],
                "long_cost_basis": p["long_cost_basis"],
                "short_cost_basis": p["short_cost_basis"],
                "short_margin_used": p["short_margin_used"],
            }
            for t, p in self._portfolio["positions"].items()
        }
        gains_copy: Dict[str, TickerRealizedGains] = {
            t: {"long": g["long"], "short": g["short"]}
            for t, g in self._portfolio["realized_gains"].items()
        }
        return {
            "cash": float(self._portfolio["cash"]),
            "margin_used": float(self._portfolio["margin_used"]),
            "margin_requirement": float(self._portfolio["margin_requirement"]),
            "positions": positions_copy,
            "realized_gains": gains_copy,
        }

    def get_cash(self) -> float:
        return float(self._portfolio["cash"])

    def get_margin_used(self) -> float:
        return float(self._portfolio["margin_used"])

    def get_margin_requirement(self) -> float:
        return float(self._portfolio["margin_requirement"])

    def get_positions(self) -> Mapping[str, PositionState]:
        return MappingProxyType(self._portfolio["positions"])  # type: ignore[arg-type]

    def get_realized_gains(self) -> Mapping[str, TickerRealizedGains]:
        return MappingProxyType(self._portfolio["realized_gains"])  # type: ignore[arg-type]

    def apply_long_buy(self, ticker: str, quantity: float, price: float) -> float:
        if quantity <= 0:
            return 0.0
        quantity = float(quantity)
        position = self._portfolio["positions"][ticker]
        
        affordable_qty = self._portfolio["cash"] / price if price > 0 else 0.0
        executed_qty = min(quantity, affordable_qty)
        
        if executed_qty <= 0:
            return 0.0
            
        cost = executed_qty * price
        old_shares = position["long"]
        old_cost_basis = position["long_cost_basis"]
        total_shares = old_shares + executed_qty
        
        if total_shares > 0:
            total_old_cost = old_cost_basis * old_shares
            total_new_cost = cost
            position["long_cost_basis"] = (total_old_cost + total_new_cost) / total_shares
            
        position["long"] = total_shares
        self._portfolio["cash"] -= cost
        return executed_qty

    def apply_long_sell(self, ticker: str, quantity: float, price: float) -> float:
        if quantity <= 0:
            return 0.0
        quantity = float(quantity)
        position = self._portfolio["positions"][ticker]
        
        executed_qty = min(quantity, position["long"])
        if executed_qty <= 0:
            return 0.0
            
        avg_cost = position["long_cost_basis"]
        realized_gain = (price - avg_cost) * executed_qty
        self._portfolio["realized_gains"][ticker]["long"] += realized_gain
        
        position["long"] -= executed_qty
        self._portfolio["cash"] += executed_qty * price
        
        if position["long"] < 1e-8:
            position["long"] = 0.0
            position["long_cost_basis"] = 0.0
            
        return executed_qty

    def apply_short_open(self, ticker: str, quantity: float, price: float) -> float:
        if quantity <= 0:
            return 0.0
        quantity = float(quantity)
        position = self._portfolio["positions"][ticker]

        margin_ratio = self._portfolio["margin_requirement"]
        affordable_qty = self._portfolio["cash"] / (price * margin_ratio) if margin_ratio > 0 and price > 0 else 0.0
        executed_qty = min(quantity, affordable_qty)
        
        if executed_qty <= 0:
            return 0.0
            
        proceeds = price * executed_qty
        margin_required = proceeds * margin_ratio

        old_short_shares = position["short"]
        old_cost_basis = position["short_cost_basis"]
        total_shares = old_short_shares + executed_qty

        if total_shares > 0:
            total_old_cost = old_cost_basis * old_short_shares
            total_new_cost = proceeds
            position["short_cost_basis"] = (total_old_cost + total_new_cost) / total_shares
            
        position["short"] = total_shares
        position["short_margin_used"] += margin_required
        self._portfolio["margin_used"] += margin_required
        self._portfolio["cash"] += proceeds
        self._portfolio["cash"] -= margin_required
        
        return executed_qty

    def apply_short_cover(self, ticker: str, quantity: float, price: float) -> float:
        if quantity <= 0:
            return 0.0
        quantity = float(quantity)
        position = self._portfolio["positions"][ticker]
        
        executed_qty = min(quantity, position["short"])
        if executed_qty <= 0:
            return 0.0
            
        cover_cost = executed_qty * price
        avg_short_price = position["short_cost_basis"]
        realized_gain = (avg_short_price - price) * executed_qty
        
        portion = executed_qty / position["short"] if position["short"] > 0 else 1.0
        margin_to_release = portion * position["short_margin_used"]
        
        position["short"] -= executed_qty
        position["short_margin_used"] -= margin_to_release
        self._portfolio["margin_used"] -= margin_to_release
        self._portfolio["cash"] += margin_to_release
        self._portfolio["cash"] -= cover_cost
        self._portfolio["realized_gains"][ticker]["short"] += realized_gain
        
        if position["short"] < 1e-8:
            residual_margin = position["short_margin_used"]
            self._portfolio["margin_used"] -= residual_margin
            position["short"] = 0.0
            position["short_cost_basis"] = 0.0
            position["short_margin_used"] = 0.0
            
        return executed_qty

