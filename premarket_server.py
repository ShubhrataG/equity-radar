#!/usr/bin/env python3
"""
Pre-Market Live Dashboard  —  Full Universe Edition
Run:  python premarket_server.py
Open: http://localhost:5173
"""

from flask import Flask, jsonify, request as req, send_file
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import pytz, threading, webbrowser, time, os, re, json

# ── Anthropic (optional — enables AI-powered Ask the Market) ──
try:
    import anthropic as _anthropic
    _ANT_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    _ANT_CLIENT = _anthropic.Anthropic(api_key=_ANT_KEY) if _ANT_KEY else None
except ImportError:
    _ANT_CLIENT = None

app = Flask(__name__)
CORS(app)

# ── ALL TICKERS ───────────────────────────────────────────────────────────────
ALL_TICKERS = [
    # AI / Semiconductors
    "NVDA","AMD","MU","AVGO","TSM","ARM","SMCI","AMAT","KLAC","LRCX","INTC","QCOM","MCHP","ON","WOLF",
    # Mega-Cap Tech
    "AAPL","MSFT","META","AMZN","GOOGL","NFLX","ORCL","IBM","CRM","NOW",
    # AI / Cloud / SaaS
    "PLTR","SNOW","AI","PATH","DDOG","NET","ZS","CRWD","GTLB","MNDY",
    # EV / Auto
    "TSLA","RIVN","GM","F","LCID","NIO","LI","XPEV",
    # Space
    "RKLB","LUNR","ASTS","PL","SPCX","RDW","KTOS","AJRD",
    # Finance / Crypto
    "JPM","GS","BAC","V","MA","COIN","HOOD","MSTR","SQ","PYPL",
    # Energy
    "XOM","CVX","OXY","SLB","HAL","BP",
    # Consumer / Retail
    "AMZN","NKE","HD","WMT","TGT","COST","MCD","SBUX","CMG",
    # Healthcare / Biotech
    "UNH","LLY","JNJ","PFE","MRNA","ABBV","ISRG","DXCM",
    # Defense / Aerospace
    "LMT","RTX","NOC","GD","BA","AXON",
    # ETFs — Broad Market
    "SPY","QQQ","QQQM","IWM","VOO","VTI","VXUS","DIA","SCHD","JEPI","JEPQ",
    # ETFs — Semiconductors
    "SOXL","SMH","SOXX","SOXS",
    # ETFs — Leveraged/Inverse
    "TQQQ","SQQQ","UPRO","SPXU",
    # ETFs — Sector (SPDR)
    "XLK","XLF","XLE","XLV","XLC","XLI","XLB","XLRE",
    # ETFs — ARK
    "ARKK","ARKW","ARKG","ARKX","ARKF",
    # ETFs — Thematic
    "BOTZ","ROBT","CIBR","BUG","WCLD","CLOU","FINX","DRIV",
    # ETFs — Space
    "UFO","ROKT","NASA","MARS",
    # ETFs — Commodities
    "GLD","SLV","USO","PDBC","IAU",
    # ETFs — Bonds
    "TLT","HYG","LQD","BND",
]
# dedupe while preserving order
seen_t = set()
TICKERS_UNIQ = [t for t in ALL_TICKERS if t not in seen_t and not seen_t.add(t)]

# ── METADATA ──────────────────────────────────────────────────────────────────
META = {
    # AI Semis
    "NVDA": ("NVIDIA Corporation",        "AI Chips",    "semi"),
    "AMD":  ("Advanced Micro Devices",    "AI Chips",    "semi"),
    "MU":   ("Micron Technology",         "AI Chips",    "memory"),
    "AVGO": ("Broadcom Inc.",             "AI Chips",    "semi"),
    "TSM":  ("Taiwan Semiconductor",      "AI Chips",    "semi"),
    "ARM":  ("Arm Holdings",              "AI Chips",    "semi"),
    "SMCI": ("Super Micro Computer",      "AI Chips",    "semi"),
    "AMAT": ("Applied Materials",         "AI Chips",    "semi"),
    "KLAC": ("KLA Corporation",           "AI Chips",    "semi"),
    "LRCX": ("Lam Research",              "AI Chips",    "semi"),
    "INTC": ("Intel Corporation",         "AI Chips",    "semi"),
    "QCOM": ("Qualcomm",                  "AI Chips",    "semi"),
    "MCHP": ("Microchip Technology",      "AI Chips",    "semi"),
    "ON":   ("ON Semiconductor",          "AI Chips",    "semi"),
    "WOLF": ("Wolfspeed",                 "AI Chips",    "semi"),
    # Mega-Cap Tech
    "AAPL": ("Apple Inc.",                "Mega-Tech",   "mega"),
    "MSFT": ("Microsoft",                 "Mega-Tech",   "mega"),
    "META": ("Meta Platforms",            "Mega-Tech",   "mega"),
    "AMZN": ("Amazon",                    "Mega-Tech",   "mega"),
    "GOOGL":("Alphabet (Google)",         "Mega-Tech",   "mega"),
    "NFLX": ("Netflix",                   "Mega-Tech",   "mega"),
    "ORCL": ("Oracle",                    "Mega-Tech",   "mega"),
    "IBM":  ("IBM",                       "Mega-Tech",   "mega"),
    "CRM":  ("Salesforce",                "Mega-Tech",   "mega"),
    "NOW":  ("ServiceNow",                "Mega-Tech",   "mega"),
    # AI / Cloud / SaaS
    "PLTR": ("Palantir Technologies",     "AI / SaaS",   "ai"),
    "SNOW": ("Snowflake",                 "AI / SaaS",   "ai"),
    "AI":   ("C3.ai",                     "AI / SaaS",   "ai"),
    "PATH": ("UiPath",                    "AI / SaaS",   "ai"),
    "DDOG": ("Datadog",                   "AI / SaaS",   "ai"),
    "NET":  ("Cloudflare",                "AI / SaaS",   "ai"),
    "ZS":   ("Zscaler",                   "AI / SaaS",   "ai"),
    "CRWD": ("CrowdStrike",               "AI / SaaS",   "ai"),
    "GTLB": ("GitLab",                    "AI / SaaS",   "ai"),
    "MNDY": ("Monday.com",                "AI / SaaS",   "ai"),
    # EV / Auto
    "TSLA": ("Tesla",                     "EV / Auto",   "ev"),
    "RIVN": ("Rivian",                    "EV / Auto",   "ev"),
    "GM":   ("General Motors",            "EV / Auto",   "ev"),
    "F":    ("Ford Motor",                "EV / Auto",   "ev"),
    "LCID": ("Lucid Group",               "EV / Auto",   "ev"),
    "NIO":  ("NIO Inc.",                  "EV / Auto",   "ev"),
    "LI":   ("Li Auto",                   "EV / Auto",   "ev"),
    "XPEV": ("XPeng",                     "EV / Auto",   "ev"),
    # Space
    "RKLB": ("Rocket Lab",                "Space",       "space"),
    "LUNR": ("Intuitive Machines",        "Space",       "space"),
    "ASTS": ("AST SpaceMobile",           "Space",       "space"),
    "PL":   ("Planet Labs",               "Space",       "space"),
    "RDW":  ("Redwire Corp",              "Space",       "space"),
    "KTOS": ("Kratos Defense",            "Space",       "space"),
    "AJRD": ("Aerojet Rocketdyne",        "Space",       "space"),
    # Finance / Crypto
    "JPM":  ("JPMorgan Chase",            "Finance",     "finance"),
    "GS":   ("Goldman Sachs",             "Finance",     "finance"),
    "BAC":  ("Bank of America",           "Finance",     "finance"),
    "V":    ("Visa",                      "Finance",     "finance"),
    "MA":   ("Mastercard",                "Finance",     "finance"),
    "COIN": ("Coinbase",                  "Crypto",      "crypto"),
    "HOOD": ("Robinhood",                 "Crypto",      "crypto"),
    "MSTR": ("MicroStrategy",             "Crypto",      "crypto"),
    "SQ":   ("Block (Square)",            "Crypto",      "crypto"),
    "PYPL": ("PayPal",                    "Finance",     "finance"),
    # Energy
    "XOM":  ("ExxonMobil",                "Energy",      "energy"),
    "CVX":  ("Chevron",                   "Energy",      "energy"),
    "OXY":  ("Occidental Petroleum",      "Energy",      "energy"),
    "SLB":  ("SLB (Schlumberger)",        "Energy",      "energy"),
    # Consumer
    "NKE":  ("Nike",                      "Consumer",    "consumer"),
    "HD":   ("Home Depot",                "Consumer",    "consumer"),
    "WMT":  ("Walmart",                   "Consumer",    "consumer"),
    "TGT":  ("Target",                    "Consumer",    "consumer"),
    "COST": ("Costco",                    "Consumer",    "consumer"),
    "MCD":  ("McDonald's",                "Consumer",    "consumer"),
    "SBUX": ("Starbucks",                 "Consumer",    "consumer"),
    "CMG":  ("Chipotle",                  "Consumer",    "consumer"),
    # Healthcare
    "UNH":  ("UnitedHealth Group",        "Healthcare",  "health"),
    "LLY":  ("Eli Lilly",                 "Healthcare",  "health"),
    "JNJ":  ("Johnson & Johnson",         "Healthcare",  "health"),
    "PFE":  ("Pfizer",                    "Healthcare",  "health"),
    "MRNA": ("Moderna",                   "Healthcare",  "health"),
    "ABBV": ("AbbVie",                    "Healthcare",  "health"),
    "ISRG": ("Intuitive Surgical",        "Healthcare",  "health"),
    "DXCM": ("Dexcom",                    "Healthcare",  "health"),
    # Defense
    "LMT":  ("Lockheed Martin",           "Defense",     "defense"),
    "RTX":  ("RTX Corporation",           "Defense",     "defense"),
    "NOC":  ("Northrop Grumman",          "Defense",     "defense"),
    "GD":   ("General Dynamics",          "Defense",     "defense"),
    "BA":   ("Boeing",                    "Defense",     "defense"),
    "AXON": ("Axon Enterprise",           "Defense",     "defense"),
    # ETFs — Broad Market
    "SPY":  ("SPDR S&P 500 ETF",          "ETFs",        "etf"),
    "QQQ":  ("Invesco Nasdaq 100 ETF",    "ETFs",        "etf"),
    "QQQM": ("Invesco QQQ Mini",          "ETFs",        "etf"),
    "IWM":  ("iShares Russell 2000 ETF",  "ETFs",        "etf"),
    "VOO":  ("Vanguard S&P 500 ETF",      "ETFs",        "etf"),
    "VTI":  ("Vanguard Total Mkt ETF",    "ETFs",        "etf"),
    "VXUS": ("Vanguard Intl Stock ETF",   "ETFs",        "etf"),
    "DIA":  ("SPDR Dow Jones ETF",        "ETFs",        "etf"),
    "SCHD": ("Schwab Dividend ETF",       "ETFs",        "etf"),
    "JEPI": ("JPMorgan Equity Prem Inc",  "ETFs",        "etf"),
    "JEPQ": ("JPMorgan Nasdaq Prem Inc",  "ETFs",        "etf"),
    # ETFs — Semiconductors
    "SOXL": ("Direxion Semi Bull 3x ETF", "ETFs",        "etf"),
    "SMH":  ("VanEck Semiconductor ETF",  "ETFs",        "etf"),
    "SOXX": ("iShares Semiconductor ETF", "ETFs",        "etf"),
    "SOXS": ("Direxion Semi Bear 3x ETF", "ETFs",        "etf"),
    # ETFs — Leveraged/Inverse
    "TQQQ": ("ProShares UltraPro QQQ 3x", "ETFs",       "etf"),
    "SQQQ": ("ProShares Short QQQ 3x",    "ETFs",       "etf"),
    "UPRO": ("ProShares S&P 500 Bull 3x", "ETFs",       "etf"),
    "SPXU": ("ProShares S&P 500 Bear 3x", "ETFs",       "etf"),
    # ETFs — Sector SPDR
    "XLK":  ("Technology Select SPDR",    "ETFs",        "etf"),
    "XLF":  ("Financial Select SPDR",     "ETFs",        "etf"),
    "XLE":  ("Energy Select SPDR",        "ETFs",        "etf"),
    "XLV":  ("Health Care Select SPDR",   "ETFs",        "etf"),
    "XLC":  ("Comm Services Select SPDR", "ETFs",        "etf"),
    "XLI":  ("Industrial Select SPDR",    "ETFs",        "etf"),
    "XLB":  ("Materials Select SPDR",     "ETFs",        "etf"),
    "XLRE": ("Real Estate Select SPDR",   "ETFs",        "etf"),
    # ETFs — ARK
    "ARKK": ("ARK Innovation ETF",        "ETFs",        "etf"),
    "ARKW": ("ARK Next Gen Internet ETF", "ETFs",        "etf"),
    "ARKG": ("ARK Genomic Revolution ETF","ETFs",        "etf"),
    "ARKX": ("ARK Space Exploration ETF", "ETFs",        "etf"),
    "ARKF": ("ARK Fintech Innovation ETF","ETFs",        "etf"),
    # ETFs — Thematic
    "BOTZ": ("Global X Robotics & AI ETF","ETFs",        "etf"),
    "ROBT": ("First Trust Robotics & AI", "ETFs",        "etf"),
    "CIBR": ("First Trust Cybersecurity", "ETFs",        "etf"),
    "BUG":  ("Global X Cybersecurity ETF","ETFs",        "etf"),
    "WCLD": ("WisdomTree Cloud ETF",       "ETFs",        "etf"),
    "CLOU": ("Global X Cloud ETF",         "ETFs",        "etf"),
    "FINX": ("Global X FinTech ETF",       "ETFs",        "etf"),
    "DRIV": ("Global X EV & Tech ETF",     "ETFs",        "etf"),
    # ETFs — Space
    "UFO":  ("Procure Space ETF",          "ETFs",        "etf"),
    "ROKT": ("MiQ Space & Tech ETF",       "ETFs",        "etf"),
    "NASA": ("Tema Space Innovators ETF",  "ETFs",        "etf"),
    "MARS": ("Roundhill Space & Tech ETF", "ETFs",        "etf"),
    # ETFs — Commodities
    "GLD":  ("SPDR Gold ETF",              "ETFs",        "etf"),
    "SLV":  ("iShares Silver ETF",         "ETFs",        "etf"),
    "USO":  ("US Oil Fund ETF",            "ETFs",        "etf"),
    "PDBC": ("Invesco Commodity ETF",      "ETFs",        "etf"),
    "IAU":  ("iShares Gold Trust ETF",     "ETFs",        "etf"),
    # ETFs — Bonds
    "TLT":  ("iShares 20yr Treasury ETF",  "ETFs",        "etf"),
    "HYG":  ("iShares High Yield Bond",    "ETFs",        "etf"),
    "LQD":  ("iShares Corp Bond ETF",      "ETFs",        "etf"),
    "BND":  ("Vanguard Total Bond ETF",    "ETFs",        "etf"),
    # Space stocks
    "SPCX": ("SpaceX / Space ETF",         "Space",       "space"),
}

# ── ANALYSIS ──────────────────────────────────────────────────────────────────
def bias(pct):
    if   pct >=  2.5: return "bullish","high"
    elif pct >=  0.75: return "bullish","medium"
    elif pct >=  0.15: return "bullish","low"
    elif pct <= -2.5: return "bearish","high"
    elif pct <= -0.75: return "bearish","medium"
    elif pct <= -0.15: return "bearish","low"
    return "neutral","low"

def driver(sym, pct, b, news):
    arrow = "▲" if pct >= 0 else "▼"
    tag   = f"{arrow} {abs(pct):.2f}%"
    if news:
        t = news[0]["title"]
        return f"{tag} · {t[:100]}{'…' if len(t)>100 else ''}"
    msgs = {
        "bullish": f"{tag} pre-mkt — buyers active; momentum carry likely",
        "bearish": f"{tag} pre-mkt — sellers leading; watch for open breakdown",
        "neutral": "Flat — no dominant catalyst; watching for open direction",
    }
    return msgs.get(b, tag)

def watch(price, prev, pct):
    if pct >  0.3: return f"${round(prev*.99,2)} support · ${round(price*1.025,2)} +2.5% ext"
    if pct < -0.3: return f"${round(price*.975,2)} flush · ${round(prev,2)} reclaim"
    return f"${round(price*.99,2)}–${round(price*1.01,2)} range · ${round(prev,2)} pivot"

def fetch(sym):
    try:
        t  = yf.Ticker(sym)
        fi = t.fast_info

        # ── Previous close (anchor for % change) ──
        prev = getattr(fi, "previous_close", None) or 0

        # ── Most current price via 1-min bars (pre + post market included) ──
        # This is more current than fast_info.last_price which only returns
        # the regular-session close even during extended hours.
        disp      = 0
        session   = "closed"
        price_age = "—"
        try:
            hist = t.history(period="1d", interval="1m", prepost=True)
            if not hist.empty:
                last_row  = hist.iloc[-1]
                disp      = float(last_row["Close"])
                last_ts   = hist.index[-1]
                # Determine session from timestamp
                et_now    = datetime.now(pytz.timezone("US/Eastern"))
                h_et      = et_now.hour + et_now.minute / 60
                if   4   <= h_et < 9.5:  session = "pre"
                elif 9.5 <= h_et < 16:   session = "regular"
                elif 16  <= h_et < 20:   session = "post"
                # Human-readable age
                age_s = int((et_now.timestamp() - last_ts.timestamp()))
                price_age = f"{age_s}s ago" if age_s < 120 else f"{age_s//60}m ago"
        except Exception:
            pass

        # Fallback: fast_info scalar prices
        if disp == 0:
            pre  = getattr(fi, "pre_market_price",  None)
            post = getattr(fi, "post_market_price", None)
            last = getattr(fi, "last_price", None) or 0
            disp = pre if (pre and pre > 1) else (post if (post and post > 1) else last)
            if disp == 0: disp = prev

        if not prev:
            prev = getattr(fi, "last_price", None) or disp

        pct  = round(((disp - prev) / prev) * 100, 2) if prev else 0
        chg  = round(disp - prev, 2)
        b, c = bias(pct)

        news = []
        try:
            for n in (t.news or [])[:5]:
                ct   = n.get("content", {})
                titl = ct.get("title", "")
                url  = (ct.get("canonicalUrl") or {}).get("url", "") or \
                       (ct.get("clickThroughUrl") or {}).get("url", "")
                pub  = (ct.get("provider") or {}).get("displayName", "")
                age  = ct.get("pubDate", "")
                if titl: news.append({"title": titl, "url": url, "publisher": pub, "age": age})
        except: pass

        name, sector, skey = META.get(sym, (sym, "Other", "default"))
        is_pre = (session == "pre")
        is_post = (session == "post")

        return {
            "ticker": sym, "name": name,
            "price": round(disp, 2), "prev_close": round(prev, 2),
            "change_pct": pct, "change_abs": chg,
            "bias": b, "confidence": c,
            "driver": driver(sym, pct, b, news),
            "key_level": watch(disp, prev, pct),
            "sector": sector, "sector_key": skey,
            "news": news[:3], "is_pre": is_pre, "is_post": is_post,
            "session": session, "price_age": price_age,
        }
    except Exception as e:
        name, sector, skey = META.get(sym, (sym, "Other", "default"))
        return {
            "ticker": sym, "name": name, "price": 0, "prev_close": 0,
            "change_pct": 0, "change_abs": 0,
            "bias": "neutral", "confidence": "low",
            "driver": f"Error: {str(e)[:60]}",
            "key_level": "—", "sector": sector, "sector_key": skey,
            "news": [], "is_pre": False, "is_post": False,
            "session": "error", "price_age": "—",
        }

def idx(sym):
    try:
        fi   = yf.Ticker(sym).fast_info
        last = getattr(fi,"last_price",0) or 0
        prev = getattr(fi,"previous_close",last) or last
        pct  = round(((last-prev)/prev)*100,2) if prev else 0
        return round(last,2), pct
    except: return 0,0

# ── API ───────────────────────────────────────────────────────────────────────
@app.route("/api/refresh")
def api_refresh():
    raw     = req.args.get("tickers","")
    tickers = [t.strip().upper() for t in raw.split(",") if t.strip()] if raw else TICKERS_UNIQ

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        results = list(ex.map(fetch, tickers))
    stocks = {s["ticker"]: s for s in results}

    vix_p,_     = idx("^VIX")
    sp_p,sp_c   = idx("^GSPC")
    nq_p,nq_c   = idx("^IXIC")
    dw_p,dw_c   = idx("^DJI")
    rut_p,rut_c = idx("^RUT")

    biases = [s["bias"] for s in stocks.values()]
    bull = biases.count("bullish")
    bear = biases.count("bearish")
    total= len(biases) or 1

    if   bull/total > .60: sent,cls = "RISK-ON","risk-on"
    elif bear/total > .60: sent,cls = "RISK-OFF","risk-off"
    else:                  sent,cls = "MIXED","mixed"

    # top news deduped
    seen_n, top_news = set(), []
    for s in stocks.values():
        for n in s.get("news",[]):
            if n["title"] not in seen_n:
                seen_n.add(n["title"])
                top_news.append({**n,"ticker":s["ticker"]})
    top_news = top_news[:15]

    # sector breakdown
    sectors = {}
    for s in stocks.values():
        sec = s["sector"]
        if sec not in sectors: sectors[sec] = {"bull":0,"bear":0,"neut":0,"tickers":[]}
        sectors[sec]["tickers"].append(s["ticker"])
        if s["bias"]=="bullish": sectors[sec]["bull"]+=1
        elif s["bias"]=="bearish": sectors[sec]["bear"]+=1
        else: sectors[sec]["neut"]+=1

    et = datetime.now(pytz.timezone("US/Eastern"))
    return jsonify({
        "stocks":stocks,"tickers":tickers,
        "vix":vix_p,
        "sp500": {"price":sp_p,"change":sp_c},
        "nasdaq":{"price":nq_p,"change":nq_c},
        "dow":   {"price":dw_p,"change":dw_c},
        "russell":{"price":rut_p,"change":rut_c},
        "sentiment":sent,"sentiment_cls":cls,
        "top_news":top_news,"sectors":sectors,
        "bull_count":bull,"bear_count":bear,"neutral_count":total-bull-bear,
        "total":total,
        "timestamp":et.strftime("%H:%M:%S ET  ·  %b %d, %Y"),
    })

@app.route("/api/tickers")
def api_tickers():
    return jsonify({"all": TICKERS_UNIQ, "meta": META})

# ── ASK THE MARKET ─────────────────────────────────────────────────────────────
def _extract_ticker(question):
    """Pull the most likely ticker symbol from free-text question.

    Priority order:
      1. Explicit $TICKER (e.g. $LUNR)
      2. Uppercase words in the ORIGINAL question that match a known ticker
         — "LUNR" typed in caps = intentional ticker; "now" in lowercase ≠ NOW
      3. Company name lookup (e.g. "Rocket Lab" → RKLB)
      4. Last resort: uppercased scan filtered by stopwords
    """
    # Words that are common English but NOT stock tickers.
    # Note: "NOW" is intentionally absent — it IS a valid ticker (ServiceNow).
    # Step 2 already guards against lowercase "now" by only scanning caps in
    # the original question, so lowercase common usage never hits this list.
    STOPWORDS = {
        "SHOULD","WHAT","WHEN","WHERE","WHY","HOW","THE","FOR","AND","OR",
        "BUY","SELL","HOLD","WAIT","THIS","GOOD","BEST","NEW","TOP",
        "WEEK","NEXT","ENTRY","STOP","LOSS","PRICE","TARGET","AT","IN","ON",
        "IS","ARE","WILL","HAVE","BEEN","CAN","COULD","WOULD","INTO","NEAR",
        "HIGH","LOW","RICH","RISE","FALL","GIVE","TAKE","MAKE","JUST","EVEN",
        "VERY","ALSO","ONLY","SOME","WELL","REAL","OVER","FULL","FAST","LONG",
        "RATE","MOVE","PUSH","PULL","PAST","LAST","EACH","BOTH","SHOW","TELL",
        "LOOK","SEEM","FEEL","COME","BACK","THEN","THAN","THAT","THEM","THEY",
        "WITH","FROM","DOES","RISK","HUGE","YEAR","DAYS","STOCK","STOCKS",
        "DATA","PLAY","SAFE","OPEN","AREA","SIDE","LEAD","BEAT","MISS","KEEP",
        "GAIN","JUMP","DROP","PUMP","DUMP","BULL","BEAR","FLAT","PEAK","TELL",
        "ANALYSIS","ABOUT","RIGHT","PRICE","POINT","TRADE","TREND","LEVEL",
        # Short common English words that must not be mistaken for tickers
        "BE","ME","MY","IT","DO","IF","BY","UP","GO","NO","SO",
        "AS","TO","OF","AM","AN","US","WE","HE","RE","ID","I",
        "HI","OK","VS","CO","TV","LA","HA","EH","AH",
    }

    # 1. Explicit $TICKER anywhere in original text
    m = re.search(r'\$([A-Za-z]{1,5})\b', question)
    if m: return m.group(1).upper()

    TICKER_SET = set(TICKERS_UNIQ)

    # 2. Uppercase words in the ORIGINAL (pre-upcase) question → intentional tickers
    #    "LUNR" typed in ALL CAPS = deliberate ticker, even if not in our 120-ticker list.
    #    "now" in lowercase = English word, never reaches this step.
    caps_in_original = re.findall(r'\b([A-Z]{2,5})\b', question)
    for word in caps_in_original:
        if word not in STOPWORDS:
            return word   # Explicitly capitalised → trust the user

    q_up = question.upper()

    # 3. Company-name lookup (case-insensitive)
    name_map = {
        "NVIDIA":"NVDA","APPLE":"AAPL","MICROSOFT":"MSFT","TESLA":"TSLA",
        "AMAZON":"AMZN","GOOGLE":"GOOGL","ALPHABET":"GOOGL",
        "AMD":"AMD","MICRON":"MU","PALANTIR":"PLTR","COINBASE":"COIN",
        "ROCKET LAB":"RKLB","INTUITIVE MACHINES":"LUNR","LUNR":"LUNR",
        "CROWDSTRIKE":"CRWD","NETFLIX":"NFLX","BROADCOM":"AVGO",
        "QUALCOMM":"QCOM","INTEL":"INTC","ROBINHOOD":"HOOD",
        "SERVICENOW":"NOW","SNOWFLAKE":"SNOW","CLOUDFLARE":"NET",
        "DATADOG":"DDOG","ZSCALER":"ZS","GITLAB":"GTLB",
        "AST SPACEMOBILE":"ASTS","PLANET LABS":"PL","REDWIRE":"RDW",
    }
    for name, sym in name_map.items():
        if name in q_up: return sym

    # Tickers that are also extremely common English words — only accept them when
    # explicitly typed in uppercase (step 2) or via company-name map (step 3).
    # Step 4 (full-string uppercase scan) would false-match e.g. "right now" → NOW.
    AMBIGUOUS = {"NOW", "AI", "GO", "NET", "GS", "MA", "V", "F", "PL"}

    # 4. Last resort: scan uppercased question, filter stopwords + known tickers only
    candidates = re.findall(r'\b([A-Z]{1,5})\b', q_up)
    for c in candidates:
        if c not in STOPWORDS and c not in AMBIGUOUS and c in TICKER_SET:
            return c

    # No confident match — caller will ask user to clarify
    return None

def _rule_based_ask(ticker, question, price, prev, pct, news_titles):
    """Fallback analysis when no API key is set — uses yfinance data + heuristics."""
    b, c = bias(pct)
    # Verdict
    if   b == "bullish" and c in ("high","medium"): verdict = "BUY"
    elif b == "bearish" and c in ("high","medium"): verdict = "AVOID"
    else:                                            verdict = "WAIT"
    # Confidence
    conf_map = {"high": 78, "medium": 62, "low": 45}
    base_conf = conf_map.get(c, 50)
    confidence = min(88, base_conf + (5 if abs(pct) > 2 else 0))
    # Levels
    entry       = round(price, 2)
    stop_loss   = round(price * (0.935 if b == "bullish" else 0.97), 2)
    take_profit = round(price * (1.08  if b == "bullish" else 1.04), 2)
    target_1w   = round(price * (1.055 if b == "bullish" else 0.97), 2)
    target_2w   = round(price * (1.10  if b == "bullish" else 0.94), 2)
    # Risk
    risk = "HIGH" if abs(pct) > 4 else ("MEDIUM" if abs(pct) > 1.5 else "LOW")
    # Explanation
    arrow = "▲" if pct >= 0 else "▼"
    news_str = f' Latest catalyst: "{news_titles[0]}".' if news_titles else ""
    explanation = (
        f"{ticker} is currently ${price:.2f} ({arrow}{abs(pct):.2f}% vs prev close ${prev:.2f}). "
        f"Bias is {b} with {c} confidence based on current momentum.{news_str} "
        f"{'Buyers are in control — the setup favors continuation if it holds above $' + str(stop_loss) + '.' if b=='bullish' else 'Sellers have the edge — risky to step in front of this move without a clear reversal signal.'} "
        f"{'Target $' + str(take_profit) + ' over the next 1-2 weeks if momentum holds.' if verdict=='BUY' else 'Wait for stabilisation around $' + str(take_profit) + ' before committing.'}"
    )
    name, sector, _ = META.get(ticker, (ticker, "Unknown", "default"))
    return {
        "ticker": ticker, "name": name, "sector": sector,
        "current_price": price, "verdict": verdict, "confidence": confidence,
        "target_1w": target_1w, "target_2w": target_2w,
        "entry": entry, "stop_loss": stop_loss, "take_profit": take_profit,
        "risk": risk, "explanation": explanation,
        "catalysts": news_titles[:3],
        "mode": "rule-based",
    }

def _claude_ask(ticker, question, market_ctx, news_titles):
    """Full AI analysis via Claude claude-sonnet-4-6 with web search."""
    system = """You are a quantitative market analyst embedded in a professional stock intelligence terminal called Equity Radar.

Given a user question about a stock, you:
1. Use web_search to find the LATEST news, analyst price targets, earnings surprises, and technical analysis
2. Combine that with provided live market data
3. Return ONLY a single valid JSON object — no markdown fences, no extra text — in this exact schema:

{
  "ticker": "SYMBOL",
  "name": "Full Company Name",
  "sector": "Sector",
  "current_price": 0.00,
  "verdict": "BUY" | "WAIT" | "AVOID",
  "confidence": 0-100,
  "target_1w": 0.00,
  "target_2w": 0.00,
  "entry": 0.00,
  "stop_loss": 0.00,
  "take_profit": 0.00,
  "risk": "LOW" | "MEDIUM" | "HIGH",
  "explanation": "2-3 sentence plain English. Cite specific price levels, catalysts, and what to watch. Be direct.",
  "catalysts": ["top catalyst 1", "top catalyst 2", "top catalyst 3"],
  "sources": ["headline or source 1", "source 2"],
  "mode": "ai"
}

Verdict rules:
- BUY: bullish momentum, good risk/reward, catalyst confirmed, entry makes sense now
- WAIT: mixed signals, better entry likely, catalyst pending, or unclear direction
- AVOID: bearish trend, poor risk/reward, negative catalyst, or too speculative

Levels: entry should be near current price or on a pullback; stop_loss 4-8% below entry; take_profit 7-15% above entry.
Risk: LOW = large-cap stable; MEDIUM = mid-cap or elevated vol; HIGH = small-cap, biotech, crypto-adjacent, or gap stock."""

    user_msg = f"""Question: "{question}"

Live market data:
{market_ctx}

Search the web for latest news and analyst targets for {ticker}, then return your JSON analysis."""

    resp = _ANT_CLIENT.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=system,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}],
        messages=[{"role": "user", "content": user_msg}],
    )
    # Extract the final text block
    raw = ""
    for block in resp.content:
        if hasattr(block, "text"):
            raw += block.text
    # Parse JSON (strip any accidental markdown)
    raw = re.sub(r"```[a-z]*\n?", "", raw).strip()
    m = re.search(r'\{[\s\S]*\}', raw)
    if not m:
        raise ValueError(f"No JSON in response: {raw[:300]}")
    return json.loads(m.group())

@app.route("/api/ask")
def api_ask():
    question = req.args.get("q", "").strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400

    # Health-check ping (used by frontend to detect AI mode)
    if question.lower() == "ping":
        return jsonify({"mode": "ai" if _ANT_CLIENT else "rule-based"})

    # 1. Extract ticker
    ticker = _extract_ticker(question)
    if not ticker:
        return jsonify({
            "error": (
                "I couldn't identify a stock ticker in your question. "
                "Please name the stock — e.g. \"Should I take profit on LUNR at $3.16?\" "
                "or \"Is NVDA a good entry right now?\""
            )
        }), 400

    # 2. Fetch live market data
    price, prev, pct, news_titles = 0, 0, 0, []
    market_ctx = ""
    try:
        t  = yf.Ticker(ticker)
        fi = t.fast_info
        prev  = getattr(fi, "previous_close", None) or 0
        try:
            hist = t.history(period="1d", interval="1m", prepost=True)
            price = float(hist.iloc[-1]["Close"]) if not hist.empty else 0
        except Exception:
            price = getattr(fi, "last_price", None) or 0
        if not prev: prev = price
        pct = round(((price - prev) / prev) * 100, 2) if prev else 0

        # ── Price sanity check ─────────────────────────────────────────────────
        # If the user mentioned a specific price (e.g. "at 3.16") and it's way off
        # from what we fetched, the ticker is probably wrong — ask for clarification.
        price_mention = re.search(r'(?<!\w)\$?(\d{1,6}\.?\d{0,4})(?!\w)', question)
        if price_mention and price > 0:
            mentioned = float(price_mention.group(1))
            # Skip: tiny numbers, year-like integers (2000-2035), and very large (>50k)
            is_year = 2000 <= mentioned <= 2035 and mentioned == int(mentioned)
            if mentioned >= 0.5 and not is_year and mentioned <= 50000:
                ratio = max(price, mentioned) / min(price, mentioned)
                if ratio > 10:
                    return jsonify({
                        "error": (
                            f"You mentioned a price around ${mentioned:.2f} but {ticker} is "
                            f"currently at ${price:.2f} — those don't match. "
                            f"Could you name the stock you're watching? "
                            f"e.g. \"Should I take profit on LUNR at ${mentioned:.2f}?\""
                        )
                    }), 400

        # ── News headlines — relevance-filtered ───────────────────────────────
        name_for_filter, sector_for_filter, _ = META.get(ticker, (ticker, "Unknown", "default"))
        # Build keywords: ticker + first meaningful word(s) of company name
        skip_generic = {"CORP","INC","THE","HOLDINGS","TECHNOLOGIES","CORPORATION",
                        "COMPANY","GROUP","GLOBAL","SYSTEMS","TECHNOLOGY","SCIENCES"}
        name_keywords = [
            part for part in name_for_filter.upper().split()
            if len(part) >= 4 and part not in skip_generic
        ][:2]
        relevant_keys = [ticker] + name_keywords
        # Compile word-boundary patterns so "NOW" doesn't match inside "SNOWFLAKE"
        rel_patterns = [re.compile(r'\b' + re.escape(kw) + r'\b') for kw in relevant_keys]

        all_news = []
        for n in (t.news or [])[:10]:
            ct = n.get("content", {})
            titl = ct.get("title", "")
            if not titl: continue
            titl_up = titl.upper()
            # Keep if any relevant keyword appears as a whole word in the headline
            if any(p.search(titl_up) for p in rel_patterns):
                news_titles.append(titl)
            all_news.append(titl)

        # If relevance filter was too strict, fall back to all headlines
        if not news_titles and all_news:
            news_titles = all_news[:4]

        name, sector, _ = META.get(ticker, (ticker, "Unknown", "default"))
        market_ctx = (
            f"Ticker: {ticker} ({name}) | Sector: {sector}\n"
            f"Current price: ${price:.2f} | Prev close: ${prev:.2f} | Change: {pct:+.2f}%\n"
            f"Recent headlines: {'; '.join(news_titles[:3]) if news_titles else 'none available'}"
        )
    except Exception as e:
        market_ctx = f"Live data fetch error for {ticker}: {e}"

    # 3. Generate analysis
    try:
        if _ANT_CLIENT:
            result = _claude_ask(ticker, question, market_ctx, news_titles)
            # Fill in live price if Claude left it as 0
            if result.get("current_price", 0) == 0 and price:
                result["current_price"] = round(price, 2)
        else:
            result = _rule_based_ask(ticker, question, price, prev, pct, news_titles)
        return jsonify(result)
    except Exception as e:
        # Ultimate fallback
        if price:
            return jsonify(_rule_based_ask(ticker, question, price, prev, pct, news_titles))
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route("/")
def index():
    return send_file(os.path.join(os.path.dirname(__file__),"premarket_live.html"))

# ── START ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n  ╔══════════════════════════════════════╗")
    print("  ║  Equity Radar — Full Universe  ║")
    print("  ║  http://localhost:5173               ║")
    print("  ╚══════════════════════════════════════╝\n")
    threading.Thread(target=lambda:(time.sleep(1.8),webbrowser.open("http://localhost:5173")),daemon=True).start()
    app.run(port=5173,debug=False,use_reloader=False)
