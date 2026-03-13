"""
T025 — Edge-case handling for MT5 no-data and symbol-map scenarios.
Covers: unknown symbols, empty date ranges, weekend gaps.
"""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mt5_mode(monkeypatch):
    monkeypatch.setenv("DEFAULT_DATA_PROVIDER", "mt5")
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://localhost:8001")
    monkeypatch.setenv("MT5_BRIDGE_API_KEY", "test-key")


@patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry")
def test_unknown_symbol_returns_empty_prices(mock_request):
    """T025: Unknown symbols should return empty prices, not crash."""
    mock_request.return_value = None  # bridge can't find rate data

    from src.tools.api import get_prices
    result = get_prices("UNKNOWN_SYMBOL", "2026-01-01", "2026-01-10")
    assert result == []


@patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry")
def test_weekend_gap_returns_empty_prices(mock_request):
    """T025: Weekend date ranges should return empty but valid."""
    # The bridge would return no data for Sat-Sun
    mock_request.return_value = {"ticker": "V75", "prices": []}

    from src.tools.api import get_prices
    result = get_prices("V75", "2026-03-14", "2026-03-15")  # Sat-Sun
    assert result == []


@patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry")
def test_empty_date_range_returns_empty(mock_request):
    """T025: Same start/end date returns empty without crashing."""
    mock_request.return_value = {"ticker": "V75", "prices": []}

    from src.tools.api import get_prices
    result = get_prices("V75", "2026-01-01", "2026-01-01")
    assert result == []


def test_unmapped_symbol_fundamentals_return_empty():
    """T025: Unmapped symbols return empty fundamentals via bridge facade."""
    from src.tools.api import get_financial_metrics

    with patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry") as mock_req:
        mock_req.return_value = None
        result = get_financial_metrics("TOTALLY_FAKE_TICKER", "2026-01-01")
        assert result == []


def test_instrument_classification_edge_cases():
    """T025: Edge-case instrument classification."""
    from src.tools.provider_config import (
        get_instrument_category,
        is_mt5_native_symbol,
    )
    # Standard cases
    assert get_instrument_category("V75") == "synthetic"
    assert get_instrument_category("V100") == "synthetic"
    assert get_instrument_category("EURUSD") == "forex"
    assert get_instrument_category("GBPUSD") == "forex"
    assert get_instrument_category("AAPL") == "equity"
    assert get_instrument_category("MSFT") == "equity"
    assert get_instrument_category("GOOGL") == "equity"

    # Native symbols should be flagged
    assert is_mt5_native_symbol("V75") is True
    assert is_mt5_native_symbol("EURUSD") is True

    # Equities should NOT be flagged
    assert is_mt5_native_symbol("AAPL") is False
    assert is_mt5_native_symbol("TSLA") is False
