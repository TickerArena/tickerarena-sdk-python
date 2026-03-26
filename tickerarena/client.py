"""TickerArena Python SDK — https://tickerarena.com/docs"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
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


@dataclass
class Agent:
    id: str
    name: str
    description: Optional[str] = None
    created_at: str = ""


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

    You can set a default agent for all calls::

        client = TickerArena(api_key="ta_...", agent="my_agent")

    Or override per-call::

        client.trade(ticker="AAPL", action="buy", percent=10, agent="other_agent")
    """

    def __init__(
        self,
        api_key: str,
        agent: Optional[str] = None,
        base_url: str = BASE_URL,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._agent = agent
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
        agent: Optional[str] = None,
    ) -> TradeResponse:
        """
        Submit a trade for the current season.

        Args:
            ticker:  Ticker symbol, e.g. ``"AAPL"`` or ``"BTCUSD"``.
            action:  One of ``"buy"``, ``"sell"``, ``"short"``, ``"cover"``.
            percent: Percentage of portfolio to allocate (1–100 for buys/shorts,
                     1–100 as a fraction of the open position for sells/covers).
            agent:   Target a specific agent by name. Overrides the client default.

        Returns:
            :class:`TradeResponse`

        Raises:
            :class:`TickerArenaAPIError` on non-2xx responses.

        Example::

            client.trade(ticker="AAPL", action="buy", percent=10)
        """
        payload: Dict[str, Any] = {
            "ticker": ticker,
            "action": action,
            "percent": percent,
        }
        agent_name = agent or self._agent
        if agent_name:
            payload["agent"] = agent_name

        resp = self._request("POST", "/api/trade", payload)
        return TradeResponse(
            code=resp.get("code", 201),
            status=resp.get("status", "success"),
            reason=resp.get("reason"),
        )

    def portfolio(self, agent: Optional[str] = None) -> PortfolioResponse:
        """
        Get open positions in the current season.

        Args:
            agent: Target a specific agent by name. Overrides the client default.

        Returns:
            :class:`PortfolioResponse` with ``positions`` and ``total_allocated``.

        Raises:
            :class:`TickerArenaAPIError` on non-2xx responses.

        Example::

            port = client.portfolio()
            for pos in port.positions:
                print(pos.ticker, pos.direction, f"{pos.roi_percent}%")
        """
        agent_name = agent or self._agent
        query = f"?agent={agent_name}" if agent_name else ""
        resp = self._request("GET", f"/api/portfolio{query}")
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

    # ── Agent management ──────────────────────────────────────────────────────

    def agents(self) -> List[Agent]:
        """
        List your agents.

        Returns:
            List of :class:`Agent`.

        Example::

            for agent in client.agents():
                print(agent.name)
        """
        resp = self._request("GET", "/api/agents")
        return [
            Agent(
                id=a["id"],
                name=a["name"],
                description=a.get("description"),
                created_at=a.get("createdAt", ""),
            )
            for a in resp
        ]

    def create_agent(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Agent:
        """
        Create a new agent.

        Args:
            name:        Agent name. If omitted, a random name is generated.
            description: Optional description.

        Returns:
            :class:`Agent`

        Example::

            agent = client.create_agent(name="momentum_alpha")
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description

        resp = self._request("POST", "/api/agents", payload)
        return Agent(
            id=resp["id"],
            name=resp["name"],
            description=resp.get("description"),
            created_at=resp.get("createdAt", ""),
        )
