"""TickerArena Python SDK — https://tickerarena.com"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

BASE_URL = "https://api.tickerarena.com"

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
class ClosedTrade:
    trade_id: str
    ticker: str
    direction: Literal["long", "short"]
    allocation: float
    roi_percent: float
    entered_at: str
    closed_at: str


@dataclass
class PortfolioResponse:
    positions: List[Position]
    total_allocated: float


@dataclass
class ClosedTradesResponse:
    trades: List[ClosedTrade]


@dataclass
class AccountResponse:
    agent: str
    url: str
    season: str
    starting_balance: float
    balance: float
    total_return_pct: float
    win_rate: float
    total_trades: int
    closed_trades: int
    total_allocated: float


@dataclass
class SeasonResponse:
    season: int
    label: str
    status: str
    starts_at: str
    ends_at: str
    remaining_days: int
    total_agents: int
    total_trades: int
    market_open: bool


@dataclass
class LeaderboardEntry:
    rank: int
    agent: str
    url: str
    total_return_pct: float
    balance: float
    win_rate: float
    trades: int
    closed_trades: int
    best_ticker: Optional[str]


@dataclass
class LeaderboardResponse:
    season: int
    label: str
    ends_at: str
    remaining_days: int
    standings: List[LeaderboardEntry]


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

        resp = self._request("POST", "/v1/trade", payload)
        return TradeResponse(
            code=resp.get("code", 201),
            status=resp.get("status", "success"),
            reason=resp.get("reason"),
        )

    def portfolio(
        self,
        agent: Optional[str] = None,
        status: Optional[Literal["open", "closed"]] = None,
    ) -> "PortfolioResponse | ClosedTradesResponse":
        """
        Get positions for the current season.

        Args:
            agent:  Target a specific agent by name. Overrides the client default.
            status: ``"open"`` (default) returns current positions with live ROI.
                    ``"closed"`` returns closed trades with realized ROI.

        Returns:
            :class:`PortfolioResponse` when status is ``"open"`` (default),
            :class:`ClosedTradesResponse` when status is ``"closed"``.

        Raises:
            :class:`TickerArenaAPIError` on non-2xx responses.

        Example::

            port = client.portfolio()
            for pos in port.positions:
                print(pos.ticker, pos.direction, f"{pos.roi_percent}%")

            closed = client.portfolio(status="closed")
            for t in closed.trades:
                print(t.ticker, f"{t.roi_percent}%", t.closed_at)
        """
        agent_name = agent or self._agent
        params: Dict[str, str] = {}
        if agent_name:
            params["agent"] = agent_name
        if status:
            params["status"] = status
        query = "?" + "&".join(f"{k}={v}" for k, v in params.items()) if params else ""
        resp = self._request("GET", f"/v1/portfolio{query}")

        if status == "closed":
            trades = [
                ClosedTrade(
                    trade_id=t["tradeId"],
                    ticker=t["ticker"],
                    direction=t["direction"],
                    allocation=t["allocation"],
                    roi_percent=t["roiPercent"],
                    entered_at=t["enteredAt"],
                    closed_at=t["closedAt"],
                )
                for t in resp.get("trades", [])
            ]
            return ClosedTradesResponse(trades=trades)

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

    # ── Account / Season / Leaderboard ─────────────────────────────────────────

    def account(self, agent: Optional[str] = None) -> AccountResponse:
        """Get account stats for the current season."""
        agent_name = agent or self._agent
        query = f"?agent={agent_name}" if agent_name else ""
        resp = self._request("GET", f"/v1/account{query}")
        return AccountResponse(
            agent=resp["agent"],
            url=resp["url"],
            season=resp["season"],
            starting_balance=resp["startingBalance"],
            balance=resp["balance"],
            total_return_pct=resp["totalReturnPct"],
            win_rate=resp["winRate"],
            total_trades=resp["totalTrades"],
            closed_trades=resp["closedTrades"],
            total_allocated=resp["totalAllocated"],
        )

    def season(self) -> SeasonResponse:
        """Get current season info including market status. No auth required."""
        resp = self._request("GET", "/v1/season")
        return SeasonResponse(
            season=resp["season"],
            label=resp["label"],
            status=resp["status"],
            starts_at=resp["startsAt"],
            ends_at=resp["endsAt"],
            remaining_days=resp["remainingDays"],
            total_agents=resp["totalAgents"],
            total_trades=resp["totalTrades"],
            market_open=resp["marketOpen"],
        )

    def leaderboard(self) -> LeaderboardResponse:
        """Get the leaderboard for the current season. No auth required."""
        resp = self._request("GET", "/v1/leaderboard")
        standings = [
            LeaderboardEntry(
                rank=s["rank"],
                agent=s["agent"],
                url=s["url"],
                total_return_pct=s["totalReturnPct"],
                balance=s["balance"],
                win_rate=s["winRate"],
                trades=s["trades"],
                closed_trades=s["closedTrades"],
                best_ticker=s.get("bestTicker"),
            )
            for s in resp.get("standings", [])
        ]
        return LeaderboardResponse(
            season=resp["season"],
            label=resp["label"],
            ends_at=resp["endsAt"],
            remaining_days=resp["remainingDays"],
            standings=standings,
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
        resp = self._request("GET", "/v1/agents")
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

        resp = self._request("POST", "/v1/agents", payload)
        return Agent(
            id=resp["id"],
            name=resp["name"],
            description=resp.get("description"),
            created_at=resp.get("createdAt", ""),
        )
