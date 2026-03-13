from unittest.mock import patch

import pytest

from src.tools.api import (
    get_company_news,
    get_financial_metrics,
    get_insider_trades,
    get_market_cap,
    get_prices,
    search_line_items,
)
from src.tools.provider_config import (
    get_instrument_category,
    get_mt5_bridge_api_key,
    get_mt5_bridge_url,
    get_mt5_connection_profile,
    get_mt5_profile_hint,
    is_mt5_native_symbol,
    is_mt5_provider,
    should_route_to_mt5_bridge,
)


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_DATA_PROVIDER", "mt5")
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://localhost:8001")
    monkeypatch.setenv("MT5_BRIDGE_API_KEY", "test-key")


def test_mt5_native_fundamentals_degradation():
    with patch("src.tools.api._make_api_request") as mock_api:
        assert get_financial_metrics("V75", "2026-01-01") == []
        assert get_insider_trades("V75", "2026-01-01") == []
        assert get_company_news("V75", "2026-01-01") == []
        assert get_financial_metrics("EURUSD", "2026-01-01") == []
        mock_api.assert_not_called()


@patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry")
def test_bridge_unreachable_degradation(mock_bridge_request):
    mock_bridge_request.return_value = None

    assert get_financial_metrics("AAPL", "2026-01-01") == []
    assert get_prices("V75", "2026-01-01", "2026-01-02") == []


@patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry")
def test_bridge_retry_then_safe_empty_without_direct_fallback(mock_bridge_request):
    mock_bridge_request.return_value = None

    with patch("src.tools.api._make_api_request") as mock_direct_api:
        assert get_financial_metrics("AAPL", "2026-01-01") == []
        assert search_line_items("AAPL", ["revenue"], "2026-01-01") == []
        assert get_insider_trades("AAPL", "2026-01-01") == []
        assert get_company_news("AAPL", "2026-01-01") == []
        assert get_prices("AAPL", "2026-01-01", "2026-01-02") == []
        assert get_market_cap("AAPL", "2026-01-01") is None
        mock_direct_api.assert_not_called()
        assert mock_bridge_request.call_count >= 5


@patch("src.tools.mt5_client.MT5BridgeClient._request_with_retry")
def test_all_data_types_route_through_bridge(mock_bridge_request):
    mock_bridge_request.return_value = None

    with patch("src.tools.api._make_api_request") as mock_direct_api:
        get_prices("AAPL", "2026-01-01", "2026-01-02")
        get_financial_metrics("AAPL", "2026-01-01")
        search_line_items("AAPL", ["revenue"], "2026-01-01")
        get_insider_trades("AAPL", "2026-01-01")
        get_company_news("AAPL", "2026-01-01")

        assert mock_bridge_request.call_count >= 5
        mock_direct_api.assert_not_called()


def test_non_mt5_mode_does_not_route_to_bridge(monkeypatch):
    monkeypatch.setenv("DEFAULT_DATA_PROVIDER", "financialdatasets")

    assert not is_mt5_provider()
    assert not should_route_to_mt5_bridge()


def test_wsl_native_url_resolution(monkeypatch):
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://localhost:8001")
    assert get_mt5_bridge_url() == "http://localhost:8001"
    assert get_mt5_connection_profile() == "host-native"


def test_docker_url_resolution(monkeypatch):
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://host.docker.internal:8001")
    assert get_mt5_bridge_url() == "http://host.docker.internal:8001"
    assert get_mt5_connection_profile() == "containerized"


def test_default_url_when_unset(monkeypatch):
    monkeypatch.delenv("MT5_BRIDGE_URL", raising=False)
    assert get_mt5_bridge_url() == "http://localhost:8001"
    assert get_mt5_connection_profile() == "host-native"


def test_profile_hint_for_docker_url(monkeypatch):
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://host.docker.internal:8001")
    assert "localhost" in (get_mt5_profile_hint() or "")


def test_api_key_mismatch_messaging(monkeypatch):
    monkeypatch.setenv("MT5_BRIDGE_API_KEY", "")
    assert get_mt5_bridge_api_key() == ""


def test_trailing_slash_stripped(monkeypatch):
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://localhost:8001/")
    assert get_mt5_bridge_url() == "http://localhost:8001"


def test_instrument_classification():
    assert is_mt5_native_symbol("V75") is True
    assert is_mt5_native_symbol("EURUSD") is True
    assert is_mt5_native_symbol("AAPL") is False

    assert get_instrument_category("V75") == "synthetic"
    assert get_instrument_category("EURUSD") == "forex"
    assert get_instrument_category("AAPL") == "equity"
