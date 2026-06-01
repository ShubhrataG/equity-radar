# ⚡ Equity Radar

> Bloomberg-style pre-market stock intelligence terminal — 120+ tickers, live yFinance data, AI-powered bias analysis, sector heat map, portfolio P&L tracker, and auto-refresh. All in a single-page dark terminal UI.

![Equity Radar](https://img.shields.io/badge/stack-Python%20%7C%20Flask%20%7C%20Vanilla%20JS-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Data](https://img.shields.io/badge/data-Yahoo%20Finance%20%7E15min%20delay-yellow)

> 🖥️ **[Open animated terminal preview →](preview.html)** — clone the repo and open `preview.html` in your browser to see the full UI before running the server.

---

## What It Does

Equity Radar is a self-hosted financial intelligence dashboard that gives you a professional-grade pre-market overview every morning before the bell. It fetches live (≈15 min delayed) price data from Yahoo Finance, applies rule-based bias scoring, and renders everything in a Bloomberg-inspired dark terminal UI.

**At a glance you get:**
- Current price, % change, and session label (PRE / LIVE / POST / CLOSED) for 120+ tickers
- Directional bias (Bullish / Bearish / Neutral) with High / Medium / Low confidence
- Driver narrative: the dominant catalyst behind each move
- Key levels to watch: support, resistance, and extension targets
- Market-wide risk gauge (0–100 score combining VIX + bear ratio)
- Sector heat map showing which sectors are leading and lagging
- Best Buy spotlight: highest-conviction bullish opportunity of the session
- Sentiment-tagged news feed (🟢 Bull / 🔴 Bear / 🟡 Neutral per headline)
- Portfolio P&L tracker with daily gain/loss, persisted in localStorage
- Interactive portfolio builder with a live donut pie chart
- Scrolling ticker tape across the top (Bloomberg-style)
- Auto-refresh countdown timer (5 / 10 / 15 / 30 min intervals)

---

## How It Works

```
Browser  ──[click Refresh]──▶  Flask /api/refresh
                                    │
                         ThreadPoolExecutor (16 workers)
                                    │
                    ┌───────────────┴───────────────┐
                    │  yfinance.Ticker per symbol   │
                    │  history(1m, prepost=True)    │  ← most current candle
                    │  fast_info.previous_close     │  ← anchor for % change
                    │  ticker.news[:5]              │  ← latest headlines
                    └───────────────┬───────────────┘
                                    │
                         Bias scoring + driver text
                         Sector aggregation
                         VIX + index fetching
                                    │
                         JSON response  ──▶  Browser renders
                                              ├─ Ticker tape
                                              ├─ Macro strip
                                              ├─ Risk gauge (SVG)
                                              ├─ Sector heat map
                                              ├─ Best Buy spotlight
                                              ├─ Stock cards grid
                                              ├─ News feed
                                              └─ Portfolio P&L
```

### Bias Scoring Logic

```python
def bias(pct):
    if   pct >=  2.5:  return "bullish", "high"
    elif pct >=  0.75: return "bullish", "medium"
    elif pct >=  0.15: return "bullish", "low"
    elif pct <= -2.5:  return "bearish", "high"
    elif pct <= -0.75: return "bearish", "medium"
    elif pct <= -0.15: return "bearish", "low"
    return "neutral", "low"
```

### Market Risk Score

Combines two signals into a 0–100 composite:
- **VIX score** (50% weight): maps VIX 10–50 onto 0–100
- **Bear ratio** (50% weight): % of tracked tickers with bearish bias

Zones: Low (0–20) → Moderate (20–40) → Elevated (40–60) → High (60–80) → Extreme (80–100)

### Price Freshness

Uses `yfinance.Ticker.history(period='1d', interval='1m', prepost=True)` to get the most recent 1-minute candle including pre-market and after-hours sessions — more current than `fast_info.last_price` which only returns the regular-session close.

> ⚠️ Yahoo Finance data is approximately 15 minutes delayed vs real-time broker feeds.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11 · Flask · flask-cors |
| **Data** | yfinance · pandas · pytz |
| **Concurrency** | `concurrent.futures.ThreadPoolExecutor` (16 workers) |
| **Frontend** | Vanilla JavaScript (ES2022) · CSS custom properties |
| **Charts** | Canvas 2D API (pie chart) · SVG (risk gauge) |
| **Persistence** | `localStorage` (portfolio holdings) |
| **Fonts** | JetBrains Mono · Inter |

No React, no Node, no webpack, no database. Single Python file + single HTML file.

---

## Tickers Covered (120+)

| Sector | Examples |
|---|---|
| AI / Semiconductors | NVDA AMD MU AVGO TSM ARM SMCI AMAT KLAC LRCX |
| Mega-Cap Tech | AAPL MSFT META AMZN GOOGL NFLX ORCL IBM CRM NOW |
| AI / Cloud / SaaS | PLTR SNOW DDOG NET ZS CRWD GTLB MNDY |
| EV / Auto | TSLA RIVN GM F LCID NIO LI XPEV |
| Space | RKLB LUNR ASTS PL RDW KTOS |
| Finance | JPM GS BAC V MA PYPL |
| Crypto | COIN HOOD MSTR SQ |
| Energy | XOM CVX OXY SLB HAL |
| Consumer | NKE HD WMT TGT COST MCD SBUX CMG |
| Healthcare | UNH LLY JNJ PFE MRNA ABBV ISRG |
| Defense | LMT RTX NOC GD BA AXON |
| ETFs — Broad | SPY QQQ QQQM VOO VTI VXUS DIA SCHD JEPI |
| ETFs — Semis | SOXL SMH SOXX SOXS |
| ETFs — Leveraged | TQQQ SQQQ UPRO SPXU |
| ETFs — ARK | ARKK ARKW ARKG ARKX ARKF |
| ETFs — Sector | XLK XLF XLE XLV XLC XLI XLB XLRE |
| ETFs — Space | NASA MARS UFO ROKT ARKX |
| ETFs — Thematic | BOTZ CIBR BUG WCLD CLOU FINX DRIV |
| ETFs — Bonds | TLT HYG LQD BND |
| ETFs — Commodities | GLD SLV USO IAU |

---

## How to Run

### Prerequisites

```bash
pip install flask flask-cors yfinance pytz pandas
```

### Start the server

```bash
python premarket_server.py
```

Then open **http://localhost:5173** in your browser.

The terminal auto-opens in your default browser on startup. Hit **Refresh Analysis** to pull live data.

### Run with a custom ticker list

Add tickers to the input field (comma-separated) and hit Refresh, or use the preset buttons:
- 🤖 AI / Chips, 🚀 Space, 💎 Mag-7, 🔲 Semi ETFs, 📊 Broad ETFs, ⚡ Leveraged, 🦄 ARK, 🗂 Sector SPDRs, 🌐 Thematic, 🏛 Bonds, 🥇 Commodities

### File structure

```
equity-radar/
├── premarket_server.py   # Flask backend — data fetching, bias scoring, API
└── premarket_live.html   # Single-page frontend — all UI, charts, portfolio
```

---

## Portfolio Features

### P&L Tracker
Add any holding (ticker + shares + avg cost) and get:
- Real-time market value using current yFinance price
- Total P&L ($) and return %
- Daily P&L (vs previous close)
- Summary bar: Total Value · Total P&L · Daily P&L · Return %
- Persists across browser sessions via `localStorage`

### Portfolio Builder
Allocate by percentage across any tickers. Live donut chart updates as you add. Hover slices to inspect individual allocations. Also persists in `localStorage`.

---

## Configuration

Edit `premarket_server.py` to:
- Add/remove tickers from `ALL_TICKERS`
- Add metadata (name, sector, sector key) to `META`
- Adjust bias thresholds in the `bias()` function
- Change the server port (default `5173`)

---

## Limitations & Disclaimer

- **Data delay**: Yahoo Finance data is approximately 15 minutes delayed. This dashboard is not suitable for day-trading or execution decisions.
- **Bias labels are rule-based**: The bullish/bearish/neutral classification is purely algorithmic (% change thresholds). It is not a buy/sell recommendation.
- **News sentiment**: Sentiment tags are keyword-matched, not AI-classified.
- **Not financial advice**: This tool is for informational and educational purposes only. Always do your own due diligence and consult a licensed financial advisor.

---

## License

MIT — free to use, modify, and distribute.

---

*Built with Python, Flask, yfinance, and vanilla JS. Inspired by Bloomberg Terminal's information density.*
