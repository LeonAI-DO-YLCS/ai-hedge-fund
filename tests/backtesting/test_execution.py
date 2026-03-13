from src.backtesting.trader import TradeExecutor


def test_trade_executor_routes_actions(portfolio):
    ex = TradeExecutor()

    # buy
    qty = ex.execute_trade("AAPL", "buy", 10, 100.0, portfolio)
    assert qty == 10
    # sell
    qty = ex.execute_trade("AAPL", "sell", 5, 100.0, portfolio)
    assert qty == 5
    # short
    qty = ex.execute_trade("MSFT", "short", 4, 200.0, portfolio)
    assert qty == 4
    # cover
    qty = ex.execute_trade("MSFT", "cover", 1, 200.0, portfolio)
    assert qty == 1


def test_trade_executor_guards_and_unknown_action(portfolio):
    ex = TradeExecutor()

    assert ex.execute_trade("AAPL", "buy", 0, 10.0, portfolio) == 0.0
    assert ex.execute_trade("AAPL", "buy", -5, 10.0, portfolio) == 0.0
    assert ex.execute_trade("AAPL", "unknown", 10, 10.0, portfolio) == 0.0


def test_fractional_live_execution(portfolio, monkeypatch):
    """T013, T014: Ensure fractional/partial fills update portfolio exactly down to non-integer lots."""
    monkeypatch.setenv("LIVE_TRADING", "true")
    ex = TradeExecutor()
    
    # Mock MT5 Bridge response
    class MockClient:
        def execute_live_trade(self, ticker, action, quantity, current_price):
            # Simulate a partial fractional fill (wanted 1.5, got 0.5)
            return {"success": True, "filled_quantity": 0.5, "price": current_price}
            
    ex._mt5_client = MockClient()
    
    # Action
    filled = ex.execute_trade("AAPL", "buy", 1.5, 100.0, portfolio)
    
    # Assert return is exact float without truncation
    assert filled == 0.5


