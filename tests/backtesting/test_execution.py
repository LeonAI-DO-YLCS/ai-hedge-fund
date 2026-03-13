from typing import Any, cast

from src.backtesting.trader import TradeExecutor


def test_trade_executor_routes_actions(portfolio):
    ex = TradeExecutor()

    assert ex.execute_trade("AAPL", "buy", 10, 100.0, portfolio) == 10
    assert ex.execute_trade("AAPL", "sell", 5, 100.0, portfolio) == 5
    assert ex.execute_trade("MSFT", "short", 4, 200.0, portfolio) == 4
    assert ex.execute_trade("MSFT", "cover", 1, 200.0, portfolio) == 1


def test_trade_executor_guards_and_unknown_action(portfolio):
    ex = TradeExecutor()

    assert ex.execute_trade("AAPL", "buy", 0, 10.0, portfolio) == 0.0
    assert ex.execute_trade("AAPL", "buy", -5, 10.0, portfolio) == 0.0
    assert ex.execute_trade("AAPL", cast(Any, "unknown"), 10, 10.0, portfolio) == 0.0


def test_fractional_live_execution_updates_portfolio(portfolio, monkeypatch):
    monkeypatch.setenv("LIVE_TRADING", "true")
    ex = TradeExecutor()

    class MockClient:
        def execute_live_trade(self, ticker, action, quantity, current_price):
            return {
                "success": True,
                "status": "partial_fill",
                "filled_quantity": 0.5,
                "filled_price": 101.5,
                "ticket_id": 321,
            }

    ex._mt5_client = cast(Any, MockClient())

    filled = ex.execute_trade("AAPL", "buy", 1.5, 100.0, portfolio)

    assert filled == 0.5
    snap = portfolio.get_snapshot()
    assert snap["positions"]["AAPL"]["long"] == 0.5
    assert snap["positions"]["AAPL"]["long_cost_basis"] == 101.5
    assert snap["cash"] == 100000.0 - (0.5 * 101.5)

    execution = portfolio.get_last_execution_result("AAPL")
    assert execution is not None
    assert execution["status"] == "partial_fill"
    assert execution["ticket_id"] == 321
    assert execution["filled_price"] == 101.5


def test_failed_live_execution_is_portfolio_noop(portfolio, monkeypatch):
    monkeypatch.setenv("LIVE_TRADING", "true")
    ex = TradeExecutor()
    before = portfolio.get_snapshot()

    class MockClient:
        def execute_live_trade(self, ticker, action, quantity, current_price):
            return {
                "success": False,
                "status": "rejected",
                "filled_quantity": 0.0,
                "filled_price": None,
                "ticket_id": None,
                "error": "broker_rejected",
            }

    ex._mt5_client = cast(Any, MockClient())

    filled = ex.execute_trade("AAPL", "buy", 1.0, 100.0, portfolio)

    assert filled == 0.0
    assert portfolio.get_snapshot() == before
    execution = portfolio.get_last_execution_result("AAPL")
    assert execution is not None
    assert execution["status"] == "rejected"
    assert execution["error"] == "broker_rejected"
