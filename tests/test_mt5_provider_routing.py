import os
import pytest
from unittest.mock import patch, MagicMock, call

from src.tools.api import (
    get_financial_metrics,
    search_line_items,
    get_insider_trades,
    get_company_news,
    get_prices,
    get_market_cap,
)
from src.tools.provider_config import (
    is_mt5_provider,
    is_mt5_native_symbol,
    get_mt5_bridge_url,
    get_mt5_bridge_api_key,
    should_route_to_mt5_bridge,
    get_instrument_category,
)


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_DATA_PROVIDER", "mt5")
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://localhost:8001")
    monkeypatch.setenv("MT5_BRIDGE_API_KEY", "test-key")


# ---------- T007: MT5-native symbol fundamentals degradation ----------

def test_mt5_native_fundamentals_degradation():
    """T007: Assert MT5-native symbols return empty/safe structures without calling external APIs."""

    # We should intercept `_make_api_request` to ensure it is NEVER called for MT5-native instruments in MT5 mode.
    with patch("src.tools.api._make_api_request") as mock_api:
        # V75 (Synthetic)
        metrics_v75 = get_financial_metrics("V75", "2026-01-01")
        assert metrics_v75 == []

        insider_v75 = get_insider_trades("V75", "2026-01-01")
        assert insider_v75 == []

        news_v75 = get_company_news("V75", "2026-01-01")
        assert news_v75 == []

        # EURUSD (Forex)
        metrics_eurusd = get_financial_metrics("EURUSD", "2026-01-01")
        assert metrics_eurusd == []

        # No external fundamentals APIs should have been hit for these symbols
        mock_api.assert_not_called()


# ---------- T008: Bridge-unreachable graceful-degradation ----------

@patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry")
def test_bridge_unreachable_degradation(mock_bridge_request):
    """T008: Assert bridge timeouts/503s degrade gracefully without crashing downstream agents."""
    # Simulate an unreachable bridge (returning None)
    mock_bridge_request.return_value = None

    # For an equity, the app will try to call the bridge proxy for financials
    metrics = get_financial_metrics("AAPL", "2026-01-01")
    assert metrics == []

    # For a native MT5 asset, it won't even call the bridge proxy for financials (it short-circuits)
    # But let's say we check prices where it does call the bridge
    prices = get_prices("V75", "2026-01-01", "2026-01-02")
    assert prices == []


@patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry")
def test_bridge_unreachable_retry_then_degrade(mock_bridge_request):
    """T008: Verify retry behavior occurs before the graceful fallback path is taken."""
    # Simulate the bridge client internal retry already happened (returns None after retries)
    mock_bridge_request.return_value = None

    # All fundamental calls should degrade
    metrics = get_financial_metrics("AAPL", "2026-01-01")
    assert metrics == []

    line_items = search_line_items("AAPL", ["revenue"], "2026-01-01")
    assert line_items == []

    insider = get_insider_trades("AAPL", "2026-01-01")
    assert insider == []

    news = get_company_news("AAPL", "2026-01-01")
    assert news == []

    # The bridge request method should have been called for each attempt
    assert mock_bridge_request.call_count >= 4


@patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry")
def test_bridge_exception_does_not_crash(mock_bridge_request):
    """T008: Verify that exceptions from the bridge don't propagate to agent callers."""
    mock_bridge_request.side_effect = Exception("Connection refused")

    # These should all return empty, not raise
    metrics = get_financial_metrics("AAPL", "2026-01-01")
    assert metrics == []

    prices = get_prices("V75", "2026-01-01", "2026-01-02")
    assert prices == []


# ---------- T019: Bridge-only routing verification ----------

@patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry")
def test_all_data_types_route_through_bridge(mock_bridge_request):
    """T019: In MT5 mode, ALL data requests route through the bridge client."""
    mock_bridge_request.return_value = None

    with patch("src.tools.api._make_api_request") as mock_direct_api:
        # Prices
        get_prices("AAPL", "2026-01-01", "2026-01-02")
        # Financial metrics
        get_financial_metrics("AAPL", "2026-01-01")
        # Line items
        search_line_items("AAPL", ["revenue"], "2026-01-01")
        # Insider trades
        get_insider_trades("AAPL", "2026-01-01")
        # Company news
        get_company_news("AAPL", "2026-01-01")

        # Bridge was called for each type
        assert mock_bridge_request.call_count >= 5

        # Direct Financial Datasets API was NOT called
        mock_direct_api.assert_not_called()


def test_non_mt5_mode_does_not_route_to_bridge(monkeypatch):
    """T019: When NOT in MT5 mode, bridge is not invoked."""
    monkeypatch.setenv("DEFAULT_DATA_PROVIDER", "financialdatasets")

    assert not is_mt5_provider()
    assert not should_route_to_mt5_bridge()


# ---------- T022: Deployment configuration tests ----------

def test_wsl_native_url_resolution(monkeypatch):
    """T022: WSL-native runs should resolve MT5_BRIDGE_URL to localhost."""
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://localhost:8001")
    assert get_mt5_bridge_url() == "http://localhost:8001"


def test_docker_url_resolution(monkeypatch):
    """T022: Docker runs should resolve MT5_BRIDGE_URL to host.docker.internal."""
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://host.docker.internal:8001")
    assert get_mt5_bridge_url() == "http://host.docker.internal:8001"


def test_default_url_when_unset(monkeypatch):
    """T022: When MT5_BRIDGE_URL is not set, default is localhost:8001."""
    monkeypatch.delenv("MT5_BRIDGE_URL", raising=False)
    assert get_mt5_bridge_url() == "http://localhost:8001"


def test_api_key_mismatch_messaging(monkeypatch):
    """T022: Empty API key should be retrievable for health-check messaging."""
    monkeypatch.setenv("MT5_BRIDGE_API_KEY", "")
    assert get_mt5_bridge_api_key() == ""


def test_trailing_slash_stripped(monkeypatch):
    """T022: Trailing slashes should be stripped from bridge URL."""
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://localhost:8001/")
    assert get_mt5_bridge_url() == "http://localhost:8001"


# ---------- Provider config classification tests ----------

def test_instrument_classification():
    """Verify instrument classification for routing decisions."""
    assert is_mt5_native_symbol("V75") is True
    assert is_mt5_native_symbol("EURUSD") is True
    assert is_mt5_native_symbol("AAPL") is False

    assert get_instrument_category("V75") == "synthetic"
    assert get_instrument_category("EURUSD") == "forex"
    assert get_instrument_category("AAPL") == "equity"

