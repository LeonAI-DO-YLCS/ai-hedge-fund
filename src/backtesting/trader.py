from __future__ import annotations

import logging
import os

from .portfolio import Portfolio
from .types import ActionLiteral, Action
from src.tools.mt5_client import MT5BridgeClient

logger = logging.getLogger("backtesting.trader")


class TradeExecutor:
    """Executes trades against a Portfolio with Backtester-identical semantics."""

    def __init__(self) -> None:
        self._live_trading_enabled = os.environ.get("LIVE_TRADING", "false").strip().lower() == "true"
        self._mt5_client: MT5BridgeClient | None = MT5BridgeClient() if self._live_trading_enabled else None

    def execute_trade(
        self,
        ticker: str,
        action: ActionLiteral,
        quantity: float,
        current_price: float,
        portfolio: Portfolio,
    ) -> int:
        if quantity is None or quantity <= 0:
            return 0

        # Coerce to enum if strings provided
        try:
            action_enum = Action(action) if not isinstance(action, Action) else action
        except Exception:
            action_enum = Action.HOLD

        if self._live_trading_enabled and self._mt5_client and action_enum != Action.HOLD:
            try:
                response = self._mt5_client.execute_live_trade(
                    ticker=ticker,
                    action=action_enum.value,
                    quantity=float(quantity),
                    current_price=float(current_price),
                )
                logger.info(
                    "Live trade attempt ticker=%s action=%s qty=%s response=%s",
                    ticker,
                    action_enum.value,
                    quantity,
                    response,
                )
                if bool(response.get("success")):
                    filled_qty = float(response.get("filled_quantity") or quantity)
                    return int(max(filled_qty, 0))
            except Exception as exc:
                logger.exception("Live trade failed for %s %s: %s", ticker, action_enum.value, exc)
            return 0

        if action_enum == Action.BUY:
            return portfolio.apply_long_buy(ticker, int(quantity), float(current_price))
        if action_enum == Action.SELL:
            return portfolio.apply_long_sell(ticker, int(quantity), float(current_price))
        if action_enum == Action.SHORT:
            return portfolio.apply_short_open(ticker, int(quantity), float(current_price))
        if action_enum == Action.COVER:
            return portfolio.apply_short_cover(ticker, int(quantity), float(current_price))

        # hold or unknown action
        return 0

