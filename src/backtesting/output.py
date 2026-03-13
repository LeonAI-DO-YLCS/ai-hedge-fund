from __future__ import annotations

from typing import List, Mapping, Sequence

from .portfolio import Portfolio
from .types import AgentOutput
from src.utils.display import format_backtest_row, print_backtest_results
from .valuation import compute_portfolio_summary


class OutputBuilder:
    """Builds daily output rows and prints results using display utils.

    Stateless: callers provide inputs and receive rows back.
    """

    def __init__(self, *, initial_capital: float | None = None) -> None:
        self._initial_capital = initial_capital

    def build_day_rows(
        self,
        *,
        date_str: str,
        tickers: Sequence[str],
        agent_output: AgentOutput,
        executed_trades: Mapping[str, float],
        current_prices: Mapping[str, float],
        portfolio: Portfolio,
        performance_metrics: Mapping[str, float | None],
        total_value: float,
        benchmark_return_pct: float | None = None,
    ) -> List[list]:
        date_rows: List[list] = []

        analyst_signals = agent_output.get("analyst_signals", {})
        decisions = agent_output.get("decisions", {})

        for ticker in tickers:
            # Analyst signal counts removed from day table

            pos = portfolio.get_positions()[ticker]
            long_val = pos["long"] * current_prices[ticker]
            short_val = pos["short"] * current_prices[ticker]
            net_position_value = long_val - short_val

            action = decisions.get(ticker, {}).get("action", "hold")
            quantity = executed_trades.get(ticker, 0)
            price = current_prices[ticker]
            execution_result = portfolio.get_last_execution_result(ticker)
            if execution_result:
                quantity = execution_result.get("filled_quantity", quantity)
                price = execution_result.get("filled_price") or price
                status = execution_result.get("status")
                requested_qty = decisions.get(ticker, {}).get("quantity", quantity)
                if status == "partial_fill" and requested_qty != quantity:
                    action = f"{action} (partial)"
                elif (
                    status in {"rejected", "failed"}
                    and decisions.get(ticker, {}).get("action", "hold") != "hold"
                ):
                    action = f"{action} ({status})"

            date_rows.append(
                format_backtest_row(
                    date=date_str,
                    ticker=ticker,
                    action=action,
                    quantity=quantity,
                    price=price,
                    long_shares=pos["long"],
                    short_shares=pos["short"],
                    position_value=net_position_value,
                )
            )

        # Summary row
        initial_value = (
            self._initial_capital if self._initial_capital is not None else total_value
        )
        summary = compute_portfolio_summary(
            portfolio=portfolio,
            total_value=total_value,
            initial_value=initial_value,
            performance_metrics=performance_metrics,
        )

        date_rows.append(
            format_backtest_row(
                date=date_str,
                ticker="",
                action="",
                quantity=0,
                price=0,
                long_shares=0,
                short_shares=0,
                position_value=0,
                is_summary=True,
                total_value=summary["total_value"],
                return_pct=summary["return_pct"],
                cash_balance=summary["cash_balance"],
                total_position_value=summary["total_position_value"],
                sharpe_ratio=summary["sharpe_ratio"],
                sortino_ratio=summary["sortino_ratio"],
                max_drawdown=summary["max_drawdown"],
                benchmark_return_pct=benchmark_return_pct,
            )
        )

        return date_rows

    def print_rows(self, rows: List[list]) -> None:
        print_backtest_results(rows)
