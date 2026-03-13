"""Tests for app.backend.services.mt5_bridge_service."""

from unittest.mock import patch


class TestMT5BridgeServiceConnectionStatus:
    @patch("src.tools.mt5_client.MT5BridgeClient.check_health")
    def test_bridge_ready(self, mock_health):
        mock_health.return_value = {
            "connected": True,
            "authorized": True,
            "broker": "TestBroker",
            "account_id": 12345,
            "balance": 10000.0,
            "latency_ms": 5,
        }
        from app.backend.services.mt5_bridge_service import MT5BridgeService

        svc = MT5BridgeService()
        result = svc.get_connection_status()

        assert result["status"] == "ready"
        assert result["connected"] is True
        assert result["authorized"] is True
        assert result["broker"] == "TestBroker"
        assert result["error"] is None

    @patch("src.tools.mt5_client.MT5BridgeClient.check_health")
    def test_bridge_unreachable_includes_profile_hint(self, mock_health, monkeypatch):
        mock_health.side_effect = Exception("Connection refused")
        monkeypatch.setenv("MT5_BRIDGE_URL", "http://host.docker.internal:8001")
        from app.backend.services.mt5_bridge_service import MT5BridgeService

        svc = MT5BridgeService()
        result = svc.get_connection_status()

        assert result["status"] == "unavailable"
        assert "host.docker.internal" in result["error"]
        assert "localhost" in result["error"]

    @patch("src.tools.mt5_client.MT5BridgeClient.check_health")
    def test_bridge_auth_error_detail(self, mock_health):
        mock_health.return_value = {"detail": "Invalid API key", "connected": False}
        from app.backend.services.mt5_bridge_service import MT5BridgeService

        svc = MT5BridgeService()
        result = svc.get_connection_status()

        assert result["status"] == "unavailable"
        assert "Invalid API key" in result["error"]


class TestMT5BridgeServiceMetrics:
    @patch("src.tools.mt5_client.MT5BridgeClient.get_metrics")
    def test_metrics_ready(self, mock_metrics):
        mock_metrics.return_value = {
            "uptime_seconds": 3600.0,
            "total_requests": 150,
            "requests_by_endpoint": {"/prices": 100, "/execute": 50},
            "errors_count": 2,
            "last_request_at": "2026-03-13T12:00:00Z",
            "retention_days": 90,
        }
        from app.backend.services.mt5_bridge_service import MT5BridgeService

        svc = MT5BridgeService()
        result = svc.get_metrics()

        assert result["status"] == "ready"
        assert result["total_requests"] == 150
        assert result["error"] is None


class TestMT5BridgeServiceSymbols:
    @patch("src.tools.mt5_client.MT5BridgeClient.get_symbols_catalog")
    @patch("src.tools.mt5_client.MT5BridgeClient.check_health")
    def test_symbols_with_connected_bridge(self, mock_health, mock_symbols):
        mock_health.return_value = {"connected": True, "authorized": True}
        mock_symbols.return_value = {
            "symbols": [
                {
                    "ticker": "AAPL",
                    "mt5_symbol": "AAPL",
                    "category": "equity",
                    "lot_size": 1.0,
                },
                {
                    "ticker": "V75",
                    "mt5_symbol": "Volatility 75 Index",
                    "category": "synthetic",
                    "lot_size": 0.01,
                },
            ]
        }
        from app.backend.services.mt5_bridge_service import MT5BridgeService

        svc = MT5BridgeService()
        result = svc.get_symbols(category="equity")

        assert result["status"] == "ready"
        assert result["count"] == 1
        assert result["symbols"][0]["ticker"] == "AAPL"
        assert result["symbols"][0]["source"] == "bridge"


class TestMT5BridgeAdministrativeViews:
    @patch("src.tools.mt5_client.MT5BridgeClient.get_logs")
    def test_logs_proxy(self, mock_logs):
        mock_logs.return_value = {
            "total": 1,
            "offset": 0,
            "limit": 50,
            "entries": [
                {
                    "timestamp": "2026-03-13T00:00:00Z",
                    "request": {"ticker": "V75"},
                    "response": {"success": True},
                    "metadata": {"state": "fill_confirmed"},
                }
            ],
        }
        from app.backend.services.mt5_bridge_service import MT5BridgeService

        svc = MT5BridgeService()
        result = svc.get_logs(limit=50, offset=0)

        assert result["status"] == "ready"
        assert result["total"] == 1
        assert result["entries"][0]["metadata"]["state"] == "fill_confirmed"

    @patch("src.tools.mt5_client.MT5BridgeClient.get_runtime_diagnostics")
    def test_runtime_diagnostics_proxy(self, mock_runtime):
        mock_runtime.return_value = {"worker_state": "AUTHORIZED", "queue_depth": 0}
        from app.backend.services.mt5_bridge_service import MT5BridgeService

        svc = MT5BridgeService()
        result = svc.get_runtime_diagnostics()

        assert result["status"] == "ready"
        assert result["diagnostics"]["worker_state"] == "AUTHORIZED"

    @patch("src.tools.mt5_client.MT5BridgeClient.get_symbol_diagnostics")
    def test_symbol_diagnostics_proxy(self, mock_diagnostics):
        mock_diagnostics.return_value = {
            "generated_at": "2026-03-13T00:00:00Z",
            "worker_state": "AUTHORIZED",
            "configured_symbols": 1,
            "checked_count": 1,
            "items": [{"ticker": "AAPL", "reason_code": "OK"}],
        }
        from app.backend.services.mt5_bridge_service import MT5BridgeService

        svc = MT5BridgeService()
        result = svc.get_symbol_diagnostics()

        assert result["status"] == "ready"
        assert result["checked_count"] == 1
        assert result["items"][0]["reason_code"] == "OK"
