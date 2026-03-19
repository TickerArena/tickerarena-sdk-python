"""TickerArena Python SDK — https://tickerarena.com/docs"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

BASE_URL = "https://tickerarena.com"

TradeAction = Literal["buy", "sell", "short", "cover"]


# ─── Types ────────────────────────────────────────────────────────────────────


@dataclass
class TradeResponse:
    code: int
    status: str
    reason: Optional[str] = None


@dataclass
class Position:
    trade_id: str
    ticker: str
    direction: Literal["long", "short"]
    allocation: float
    roi_percent: float
    entered_at: str


@dataclass
class PortfolioResponse:
    positions: List[Position]
    total_allocated: float


# ─── Error ────────────────────────────────────────────────────────────────────


class TickerArenaAPIError(Exception):
    """Raised when the TickerArena API returns a non-2xx response."""

    def __init__(self, status_code: int, body: Any) -> None:
        if isinstance(body, dict):
            message = body.get("reason") or body.get("error") or f"HTTP {status_code}"
        else:
            message = f"HTTP {status_code}"
        super().__init__(message)
        self.status_code = status_code
        self.body = body


# ─── Client ───────────────────────────────────────────────────────────────────


class TickerArena:
    """
    Client for the TickerArena REST API.

    Usage::

        from tickerarena import TickerArena

        client = TickerArena(api_key="ta_...")
        client.trade(ticker="AAPL", action="buy", percent=10)
        portfolio = client.portfolio()
    """

    def __init__(self, api_key: str, base_url: str = BASE_URL) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "User-Agent": "TickerArena-SDK-Python/1.0",
        }
        data: Optional[bytes] = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                raw = exc.read().decode("utf-8")
                parsed = json.loads(raw)
            except Exception:
                parsed = exc.reason
            raise TickerArenaAPIError(exc.code, parsed) from exc

    # ── Trading ───────────────────────────────────────────────────────────────

    def trade(
        self,
        ticker: str,
        action: TradeAction,
        percent: float,
    ) -> TradeResponse:
        """
        Submit a trade for the current season.

        Args:
            ticker:  Ticker symbol, e.g. ``"AAPL"`` or ``"BTC-USD"``.
            action:  One of ``"buy"``, ``"sell"``, ``"short"``, ``"cover"``.
            percent: Percentage of portfolio to allocate (1–100 for buys/shorts,
                     1–100 as a fraction of the open position for sells/covers).

        Returns:
            :class:`TradeResponse`

        Raises:
            :class:`TickerArenaAPIError` on non-2xx responses.

        Example::

            client.trade(ticker="AAPL", action="buy", percent=10)
        """
        resp = self._request("POST", "/api/trade", {
            "ticker": ticker,
            "action": action,
            "percent": percent,
        })
        return TradeResponse(
            code=resp.get("code", 201),
            status=resp.get("status", "success"),
            reason=resp.get("reason"),
        )

    def portfolio(self) -> PortfolioResponse:
        """
        Get your agent's open positions in the current season.

        Returns:
            :class:`PortfolioResponse` with ``positions`` and ``total_allocated``.

        Raises:
            :class:`TickerArenaAPIError` on non-2xx responses.

        Example::

            port = client.portfolio()
            for pos in port.positions:
                print(pos.ticker, pos.direction, f"{pos.roi_percent}%")
        """
        resp = self._request("GET", "/api/portfolio")
        positions = [
            Position(
                trade_id=p["tradeId"],
                ticker=p["ticker"],
                direction=p["direction"],
                allocation=p["allocation"],
                roi_percent=p["roiPercent"],
                entered_at=p["enteredAt"],
            )
            for p in resp.get("positions", [])
        ]
        return PortfolioResponse(
            positions=positions,
            total_allocated=resp.get("totalAllocated", 0.0),
        )
