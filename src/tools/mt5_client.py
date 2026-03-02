"""
MT5 Bridge Client — Thin HTTP wrapper for the AI Hedge Fund.

This module lives in the **main project** (``src/tools/``) and provides
a clean interface for calling the MT5 Bridge REST API running on the
Windows host.

Usage::

    from src.tools.mt5_client import MT5BridgeClient

    client = MT5BridgeClient()  # reads env vars
    prices = client.get_prices("V75", "2026-01-01", "2026-02-01")
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

from src.data.models import Price

logger = logging.getLogger("mt5_client")


class MT5BridgeClient:
    """HTTP client for the MT5 Bridge microservice.

    Configuration is read from environment variables:

    - ``MT5_BRIDGE_URL``     — base URL (default: ``http://host.docker.internal:8001``)
    - ``MT5_BRIDGE_API_KEY`` — shared API key for authentication
    """

    DEFAULT_BASE_URL = "http://host.docker.internal:8001"
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 1.0  # seconds
    TIMEOUT = 10  # seconds per request

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("MT5_BRIDGE_URL", self.DEFAULT_BASE_URL)).rstrip("/")
        self.api_key = api_key or os.getenv("MT5_BRIDGE_API_KEY", "")
        self._session = requests.Session()
        self._session.headers["X-API-KEY"] = self.api_key

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_prices(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        timeframe: str = "D1",
    ) -> list[Price]:
        """Fetch OHLCV price data from the MT5 Bridge.

        Returns a list of ``Price`` objects compatible with the existing
        data model in ``src/data/models.py``.
        """
        params = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "timeframe": timeframe,
        }
        data = self._request_with_retry("GET", "/prices", params=params)
        if data is None:
            return []

        return [Price(**p) for p in data.get("prices", [])]

    def check_health(self) -> dict[str, Any]:
        """Query the bridge health endpoint.

        Returns the raw JSON response as a dictionary.
        """
        data = self._request_with_retry("GET", "/health")
        return data or {}

    def execute_trade(
        self,
        ticker: str,
        action: str,
        quantity: float,
        current_price: float,
    ) -> dict[str, Any]:
        """Backward-compatible alias for `execute_live_trade`."""
        return self.execute_live_trade(
            ticker=ticker,
            action=action,
            quantity=quantity,
            current_price=current_price,
        )

    def execute_live_trade(
        self,
        ticker: str,
        action: str,
        quantity: float,
        current_price: float,
    ) -> dict[str, Any]:
        """Submit a live trade execution request to the MT5 Bridge."""
        payload = {
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "current_price": current_price,
        }
        data = self._request_with_retry(
            "POST",
            "/execute",
            json=payload,
            raise_on_http_error=True,
        )
        if data is None:
            raise requests.RequestException("No response from MT5 Bridge execute endpoint")
        return data

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request_with_retry(
        self,
        method: str,
        path: str,
        raise_on_http_error: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Make an HTTP request with exponential backoff retry logic.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST).
        path : str
            URL path (e.g., ``/prices``).
        **kwargs
            Passed through to ``requests.Session.request()``.

        Returns
        -------
        dict or None
            Parsed JSON response, or None on failure.
        """
        url = f"{self.base_url}{path}"

        for attempt in range(1, self.MAX_RETRIES + 1):
            resp: requests.Response | None = None
            try:
                resp = self._session.request(
                    method,
                    url,
                    timeout=self.TIMEOUT,
                    **kwargs,
                )
                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.ConnectionError as exc:
                delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "MT5 Bridge connection error (attempt %d/%d, retry in %.1fs): %s",
                    attempt,
                    self.MAX_RETRIES,
                    delay,
                    exc,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(delay)

            except requests.exceptions.HTTPError as exc:
                if raise_on_http_error:
                    raise
                # Don't retry client errors (4xx)
                if resp is not None and resp.status_code < 500:
                    logger.error("MT5 Bridge client error: %s", exc)
                    try:
                        return resp.json()
                    except Exception:
                        return None
                # Retry server errors (5xx)
                delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "MT5 Bridge server error (attempt %d/%d, retry in %.1fs): %s",
                    attempt,
                    self.MAX_RETRIES,
                    delay,
                    exc,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(delay)

            except requests.exceptions.Timeout as exc:
                delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "MT5 Bridge timeout (attempt %d/%d, retry in %.1fs): %s",
                    attempt,
                    self.MAX_RETRIES,
                    delay,
                    exc,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(delay)

            except Exception as exc:
                logger.exception("Unexpected error calling MT5 Bridge: %s", exc)
                return None

        logger.error("All %d retry attempts to MT5 Bridge exhausted.", self.MAX_RETRIES)
        return None
