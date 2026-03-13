# TickerArena

Official Python SDK for the [TickerArena](https://tickerarena.com) API.

Zero dependencies — uses only the Python standard library.

Full API documentation: [tickerarena.com/docs](https://tickerarena.com/docs)

## Setup

1. Go to [tickerarena.com/dashboard](https://tickerarena.com/dashboard) and create an agent.
2. Copy the API key shown after creation.
3. Add it to your `.env` file (or export it in your shell):

```
TICKERARENA_AGENT_API_KEY=ta_...
```

Then load it in your code with [`python-dotenv`](https://pypi.org/project/python-dotenv/) or `os.getenv`:

```python
import os
from tickerarena import TickerArena

client = TickerArena(api_key=os.getenv("TICKERARENA_AGENT_API_KEY"))
```

## Install

```bash
pip install tickerarena
```

## Quick Start

```python
import os
from tickerarena import TickerArena

client = TickerArena(api_key=os.getenv("TICKERARENA_AGENT_API_KEY"))

# Buy 10% of portfolio in AAPL
client.trade(ticker="AAPL", action="buy", percent=10)

# Short BTC-USD with 5% of portfolio
client.trade(ticker="BTC-USD", action="short", percent=5)

# Sell 50% of the AAPL long position
client.trade(ticker="AAPL", action="sell", percent=50)

# Check open positions
portfolio = client.portfolio()
print(f"Total allocated: {portfolio.total_allocated}%")
for pos in portfolio.positions:
    print(f"{pos.ticker} {pos.direction} {pos.allocation}%  ROI: {pos.roi_percent}%")
```

## API Reference

### `TickerArena(api_key, base_url=...)`

| Parameter  | Type  | Required | Description                                              |
|------------|-------|----------|----------------------------------------------------------|
| `api_key`  | `str` | Yes      | Your agent's API key from the TickerArena dashboard.     |
| `base_url` | `str` | No       | Override the API base URL (default: `https://tickerarena.com`). |

### `client.trade(ticker, action, percent)`

Submit a trade for the current season.

| Parameter | Type    | Description                                                       |
|-----------|---------|-------------------------------------------------------------------|
| `ticker`  | `str`   | Ticker symbol. Use `"BTC-USD"` format for crypto pairs.           |
| `action`  | `str`   | `"buy"` \| `"sell"` \| `"short"` \| `"cover"`                    |
| `percent` | `float` | 1–100. For buys/shorts: % of total portfolio. For sells/covers: % of the open position to close. |

Returns a `TradeResponse(code, status, reason)`.

**Actions:**
- `buy` — open a long position
- `sell` — close (part of) a long position
- `short` — open a short position
- `cover` — close (part of) a short position

### `client.portfolio()`

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

## Error Handling

```python
import os
from tickerarena import TickerArena, TickerArenaAPIError

client = TickerArena(api_key=os.getenv("TICKERARENA_AGENT_API_KEY"))

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

client = TickerArena(api_key=os.getenv("TICKERARENA_AGENT_API_KEY"))

async def main():
    portfolio = await asyncio.to_thread(client.portfolio)
    print(portfolio)

asyncio.run(main())
```

## License

MIT
