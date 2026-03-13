"""
Tests for app.backend.services.mt5_bridge_service
Covers: T006 (bridge disconnect / empty-response normalization),
        T017 (backend metrics proxy).
"""
import pytest
from unittest.mock import patch, MagicMock


class TestMT5BridgeServiceConnectionStatus:
    """T006: Verify connection status normalization under various bridge states."""

    @patch("src.tools.mt5_client.MT5BridgeClient.check_health")
    def test_bridge_ready(self, mock_health):
        """When bridge returns healthy payload, status is 'ready'."""
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
    def test_bridge_connected_not_authorized(self, mock_health):
        """When bridge returns connected but not authorized, status is 'degraded'."""
        mock_health.return_value = {
            "connected": True,
            "authorized": False,
        }
        from app.backend.services.mt5_bridge_service import MT5BridgeService
        svc = MT5BridgeService()
        result = svc.get_connection_status()

        assert result["status"] == "degraded"
        assert result["connected"] is True
        assert result["authorized"] is False

    @patch("src.tools.mt5_client.MT5BridgeClient.check_health")
    def test_bridge_unreachable(self, mock_health):
        """When bridge throws an exception, status is 'unavailable' with informative error."""
        mock_health.side_effect = Exception("Connection refused")
        from app.backend.services.mt5_bridge_service import MT5BridgeService
        svc = MT5BridgeService()
        result = svc.get_connection_status()

        assert result["status"] == "unavailable"
        assert result["connected"] is False
        assert "unreachable" in result["error"].lower() or "unavailable" in result["error"].lower()

    @patch("src.tools.mt5_client.MT5BridgeClient.check_health")
    def test_bridge_auth_error_detail(self, mock_health):
        """When bridge returns an error detail (e.g. bad API key), it's surfaced clearly."""
        mock_health.return_value = {
            "detail": "Invalid API key",
            "connected": False,
        }
        from app.backend.services.mt5_bridge_service import MT5BridgeService
        svc = MT5BridgeService()
        result = svc.get_connection_status()

        assert result["status"] == "unavailable"
        assert "Bridge Error" in result["error"]
        assert "Invalid API key" in result["error"]


class TestMT5BridgeServiceMetrics:
    """T017: Verify metrics proxy correctly normalizes bridge responses."""

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
        assert result["uptime_seconds"] == 3600.0
        assert result["total_requests"] == 150
        assert result["errors_count"] == 2
        assert result["error"] is None

    @patch("src.tools.mt5_client.MT5BridgeClient.get_metrics")
    def test_metrics_unavailable(self, mock_metrics):
        mock_metrics.side_effect = Exception("Connection refused")
        from app.backend.services.mt5_bridge_service import MT5BridgeService
        svc = MT5BridgeService()
        result = svc.get_metrics()

        assert result["status"] == "unavailable"
        assert result["uptime_seconds"] == 0.0
        assert "Failed to fetch" in result["error"]


class TestMT5BridgeServiceSymbols:
    """Verify symbol catalog loading and filtering."""

    @patch("src.tools.mt5_client.MT5BridgeClient.check_health")
    def test_symbols_with_connected_bridge(self, mock_health):
        mock_health.return_value = {"connected": True, "authorized": True}
        from app.backend.services.mt5_bridge_service import MT5BridgeService
        svc = MT5BridgeService()
        result = svc.get_symbols()

        # Should return a dict with status/symbols/count keys
        assert "status" in result
        assert "symbols" in result
        assert "count" in result
        assert isinstance(result["symbols"], list)
