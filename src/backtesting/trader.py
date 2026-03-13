from __future__ import annotations

import logging
import os

from .portfolio import Portfolio
from .types import ActionLiteral, Action, ExecutionStatus, TradeExecutionResult
from src.tools.mt5_client import MT5BridgeClient

logger = logging.getLogger("backtesting.trader")


class TradeExecutor:
    """Executes trades against a Portfolio with Backtester-identical semantics."""

    def __init__(self) -> None:
        self._live_trading_enabled = (
            os.environ.get("LIVE_TRADING", "false").strip().lower() == "true"
        )
        self._mt5_client: MT5BridgeClient | None = (
            MT5BridgeClient() if self._live_trading_enabled else None
        )

    def execute_trade(
        self,
        ticker: str,
        action: ActionLiteral,
        quantity: float,
        current_price: float,
        portfolio: Portfolio,
    ) -> float:
        result = self.execute_trade_result(
            ticker, action, quantity, current_price, portfolio
        )
        return float(result.get("filled_quantity") or 0.0)

    def execute_trade_result(
        self,
        ticker: str,
        action: ActionLiteral,
        quantity: float,
        current_price: float,
        portfolio: Portfolio,
    ) -> TradeExecutionResult:
        if quantity is None or quantity <= 0:
            result: TradeExecutionResult = {
                "ticker": ticker,
                "action": action,
                "requested_quantity": float(quantity or 0.0),
                "requested_price": float(current_price),
                "filled_quantity": 0.0,
                "filled_price": None,
                "success": False,
                "status": "skipped",
                "ticket_id": None,
                "error": None,
            }
            portfolio.record_execution_result(ticker, result)
            return result

        # Coerce to enum if strings provided
        try:
            action_enum = Action(action) if not isinstance(action, Action) else action
        except Exception:
            action_enum = Action.HOLD

        if (
            self._live_trading_enabled
            and self._mt5_client
            and action_enum != Action.HOLD
        ):
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
                result = self._normalize_live_result(
                    ticker=ticker,
                    action=action_enum.value,
                    quantity=float(quantity),
                    current_price=float(current_price),
                    response=response,
                )
                if (
                    bool(result.get("success"))
                    and float(result.get("filled_quantity") or 0.0) > 0
                ):
                    filled_qty = float(result.get("filled_quantity") or 0.0)
                    applied_qty = portfolio.reconcile_live_fill(
                        ticker,
                        action_enum.value,
                        filled_qty,
                        float(result.get("filled_price") or current_price),
                    )
                    if applied_qty < filled_qty:
                        result["error"] = (
                            f"reconciliation_applied_{applied_qty}_of_{filled_qty}"
                        )
                    result["filled_quantity"] = applied_qty
                portfolio.record_execution_result(ticker, result)
                return result
            except Exception as exc:
                logger.exception(
                    "Live trade failed for %s %s: %s", ticker, action_enum.value, exc
                )
                result = self._build_result(
                    ticker=ticker,
                    action=action_enum.value,
                    requested_quantity=float(quantity),
                    requested_price=float(current_price),
                    success=False,
                    status="failed",
                    error=str(exc),
                )
                portfolio.record_execution_result(ticker, result)
                return result

        executed_qty = 0.0
        if action_enum == Action.BUY:
            executed_qty = portfolio.apply_long_buy(
                ticker, float(quantity), float(current_price)
            )
        elif action_enum == Action.SELL:
            executed_qty = portfolio.apply_long_sell(
                ticker, float(quantity), float(current_price)
            )
        elif action_enum == Action.SHORT:
            executed_qty = portfolio.apply_short_open(
                ticker, float(quantity), float(current_price)
            )
        elif action_enum == Action.COVER:
            executed_qty = portfolio.apply_short_cover(
                ticker, float(quantity), float(current_price)
            )
        else:
            result = self._build_result(
                ticker=ticker,
                action=action_enum.value,
                requested_quantity=float(quantity),
                requested_price=float(current_price),
                success=False,
                status="skipped",
                error=None,
            )
            portfolio.record_execution_result(ticker, result)
            return result

        result = self._build_result(
            ticker=ticker,
            action=action_enum.value,
            requested_quantity=float(quantity),
            requested_price=float(current_price),
            filled_quantity=float(executed_qty),
            filled_price=float(current_price) if executed_qty > 0 else None,
            success=executed_qty > 0,
            status="filled" if executed_qty > 0 else "skipped",
            error=None,
        )
        portfolio.record_execution_result(ticker, result)
        return result

    @staticmethod
    def _build_result(
        *,
        ticker: str,
        action: ActionLiteral,
        requested_quantity: float,
        requested_price: float,
        filled_quantity: float = 0.0,
        filled_price: float | None = None,
        success: bool,
        status: ExecutionStatus,
        ticket_id: int | None = None,
        error: str | None = None,
    ) -> TradeExecutionResult:
        return {
            "ticker": ticker,
            "action": action,
            "requested_quantity": float(requested_quantity),
            "requested_price": float(requested_price),
            "filled_quantity": float(max(filled_quantity, 0.0)),
            "filled_price": None if filled_price is None else float(filled_price),
            "success": bool(success),
            "status": status,
            "ticket_id": ticket_id,
            "error": error,
        }

    def _normalize_live_result(
        self,
        *,
        ticker: str,
        action: ActionLiteral,
        quantity: float,
        current_price: float,
        response: dict,
    ) -> TradeExecutionResult:
        filled_qty = float(response.get("filled_quantity") or 0.0)
        filled_price = response.get("filled_price")
        if filled_price is None:
            filled_price = response.get("price")
        ticket_raw = response.get("ticket_id")
        ticket_id = int(ticket_raw) if ticket_raw not in (None, "") else None
        success = bool(response.get("success")) and filled_qty > 0

        if success:
            status: ExecutionStatus = "filled"
            if (
                str(response.get("status") or "") == "partial_fill"
                or 0 < filled_qty < quantity
            ):
                status = "partial_fill"
            return self._build_result(
                ticker=ticker,
                action=action,
                requested_quantity=quantity,
                requested_price=current_price,
                filled_quantity=filled_qty,
                filled_price=float(
                    filled_price if filled_price is not None else current_price
                ),
                success=True,
                status=status,
                ticket_id=ticket_id,
                error=response.get("error"),
            )

        return self._build_result(
            ticker=ticker,
            action=action,
            requested_quantity=quantity,
            requested_price=current_price,
            filled_quantity=filled_qty,
            filled_price=float(filled_price) if filled_price is not None else None,
            success=False,
            status="failed"
            if str(response.get("status") or "") == "failed"
            else "rejected",
            ticket_id=ticket_id,
            error=response.get("error"),
        )
