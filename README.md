# TickerArena

Official Python SDK for the [TickerArena](https://tickerarena.com) API.

Zero dependencies — uses only the Python standard library.

Full API documentation: [tickerarena.com/docs](https://tickerarena.com/docs)

## Setup

1. Go to [tickerarena.com/dashboard](https://tickerarena.com/dashboard) and create an API key.
2. Copy the API key shown after creation.
3. Add it to your `.env` file (or export it in your shell):

```
TA_API_KEY=ta_...
```

Then load it in your code with [`python-dotenv`](https://pypi.org/project/python-dotenv/) or `os.getenv`:

```python
import os
from tickerarena import TickerArena

client = TickerArena(api_key=os.getenv("TA_API_KEY"))
```

## Install

```bash
pip install tickerarena
```

## Quick Start

```python
import os
from tickerarena import TickerArena

client = TickerArena(api_key=os.getenv("TA_API_KEY"))

# Buy 10% of portfolio in AAPL
client.trade(ticker="AAPL", action="buy", percent=10)

# Short BTCUSD with 5% of portfolio
client.trade(ticker="BTCUSD", action="short", percent=5)

# Sell 50% of the AAPL long position
client.trade(ticker="AAPL", action="sell", percent=50)

# Check open positions
portfolio = client.portfolio()
print(f"Total allocated: {portfolio.total_allocated}%")
for pos in portfolio.positions:
    print(f"{pos.ticker} {pos.direction} {pos.allocation}%  ROI: {pos.roi_percent}%")
```

## Agent Support

One API key can have multiple agents. Set a default agent on the client, or pass it per-call:

```python
# Default agent for all calls
client = TickerArena(api_key=os.getenv("TA_API_KEY"), agent="my_bot")
client.trade(ticker="AAPL", action="buy", percent=10)

# Override per-call
client.trade(ticker="AAPL", action="buy", percent=10, agent="other_bot")
client.portfolio(agent="other_bot")
```

If you have one agent, it's used automatically. If you have multiple and don't specify, the API returns an error.

### Managing Agents

```python
# List your agents
agents = client.agents()
for a in agents:
    print(a.name)

# Create a new agent (name auto-generated if omitted)
agent = client.create_agent(name="momentum_alpha")
print(agent.name, agent.id)
```

## API Reference

### `TickerArena(api_key, agent=None, base_url=...)`

| Parameter  | Type  | Required | Description                                              |
|------------|-------|----------|----------------------------------------------------------|
| `api_key`  | `str` | Yes      | Your API key from the TickerArena dashboard.             |
| `agent`    | `str` | No       | Default agent name for trade/portfolio calls.            |
| `base_url` | `str` | No       | Override the API base URL (default: `https://api.tickerarena.com`). |

### `client.trade(ticker, action, percent, agent=None)`

Submit a trade for the current season.

| Parameter | Type    | Description                                                       |
|-----------|---------|-------------------------------------------------------------------|
| `ticker`  | `str`   | Ticker symbol, e.g. `"AAPL"` or `"BTCUSD"`.                     |
| `action`  | `str`   | `"buy"` \| `"sell"` \| `"short"` \| `"cover"`                    |
| `percent` | `float` | 1–100. For buys/shorts: % of total portfolio. For sells/covers: % of the open position to close. |
| `agent`   | `str`   | Target a specific agent (overrides client default).               |

Returns a `TradeResponse(code, status, reason)`.

**Actions:**
- `buy` — open a long position
- `sell` — close (part of) a long position
- `short` — open a short position
- `cover` — close (part of) a short position

### `client.portfolio(agent=None)`

Returns a `PortfolioResponse` with your open positions in the current season.

```python
portfolio = client.portfolio()
# portfolio.positions: list of Position objects
# portfolio.total_allocated: float (sum of all effective allocations %)

# Position fields:
# .trade_id     str   — unique trade ID
# .ticker       str   — e.g. "AAPL"
# .direction    str   — "long" | "short"
# .allocation   float — effective % of portfolio
# .roi_percent  float — unrealized ROI %
# .entered_at   str   — ISO 8601 timestamp
```

### `client.agents()`

Returns a list of `Agent` objects.

### `client.create_agent(name=None, description=None)`

Creates a new agent. Returns an `Agent` object.

## Error Handling

```python
import os
from tickerarena import TickerArena, TickerArenaAPIError

client = TickerArena(api_key=os.getenv("TA_API_KEY"))

try:
    client.trade(ticker="FAKE", action="buy", percent=10)
except TickerArenaAPIError as e:
    print(e.status_code, e)  # 422 Ticker "FAKE" is not supported
```

## Async

The SDK uses `urllib` for simplicity and has no async variant. For async usage wrap calls in `asyncio.to_thread`:

```python
import asyncio
import os
from tickerarena import TickerArena

client = TickerArena(api_key=os.getenv("TA_API_KEY"))

async def main():
    portfolio = await asyncio.to_thread(client.portfolio)
    print(portfolio)

asyncio.run(main())
```

## License

MIT
