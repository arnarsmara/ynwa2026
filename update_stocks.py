"""
update_stocks.py -- StockBreak
Saekir gogn fra Yahoo Finance + soguleg gogn fyrir linurit
Skrifar stocks_data.json sem vefsidan les.

Keyra:  python update_stocks.py
"""

import yfinance as yf
import json
import os
import ssl
from datetime import datetime, timedelta
from pathlib import Path

# Leyfir SSL a fyrirtaekjanetum med sjalfundirritadar skirteini (t.d. Reykjanesbae proxy)
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

# Les .env skra ef hun er til (API lyklar -- fer aldrei a GitHub)
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8-sig").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# -----------------------------------------------------------------------------
#  STILLINGAR
# -----------------------------------------------------------------------------

STOCKS_US = [
    ("AAPL",  "Apple Inc.",         "Tech"),
    ("MSFT",  "Microsoft Corp.",    "Tech"),
    ("NVDA",  "NVIDIA Corp.",       "Tech"),
    ("TSLA",  "Tesla Inc.",         "Tech"),
    ("GOOGL", "Alphabet Inc.",      "Tech"),
    ("AMZN",  "Amazon.com Inc.",    "Tech"),
    ("META",  "Meta Platforms",     "Tech"),
    ("NFLX",  "Netflix Inc.",       "Tech"),
    ("JPM",   "JPMorgan Chase",     "Finance"),
    ("GS",    "Goldman Sachs",      "Finance"),
    ("V",     "Visa Inc.",          "Finance"),
    ("BAC",   "Bank of America",    "Finance"),
    ("JNJ",   "Johnson & Johnson",  "Health"),
    ("PFE",   "Pfizer Inc.",        "Health"),
    ("UNH",   "UnitedHealth",       "Health"),
    ("WMT",   "Walmart Inc.",       "Consumer"),
    ("KO",    "Coca-Cola",          "Consumer"),
    ("XOM",   "ExxonMobil",         "Energy"),
    ("CVX",   "Chevron Corp.",      "Energy"),
]

ETFS = [
    ("VTI",     "Vanguard Total Market", "ETF"),
    ("VOO",     "Vanguard S&P 500",      "ETF"),
    ("QQQ",     "Invesco Nasdaq-100",    "ETF"),
    ("IWDA.AS", "iShares MSCI World",    "ETF"),
    ("IQQH.DE", "iShares Clean Energy",  "ETF"),
]

INDICES = [
    ("^GSPC",  "S&P 500"),
    ("^IXIC",  "Nasdaq"),
    ("^DJI",   "Dow Jones"),
    ("^FTSE",  "FTSE 100"),
    ("^VIX",   "VIX"),
]

OUTPUT_FILE = "stocks_data.json"

# -----------------------------------------------------------------------------
#  SOGULEG GOGN -- fyrir linurit
# -----------------------------------------------------------------------------
def fetch_history(ticker_sym, period="6mo", interval="1d"):
    """Skilar lista af {date, close} fyrir linurit."""
    try:
        t = yf.Ticker(ticker_sym)
        hist = t.history(period=period, interval=interval)
        if hist.empty:
            return []
        result = []
        for date, row in hist.iterrows():
            result.append({
                "d": date.strftime("%Y-%m-%d"),
                "c": round(float(row["Close"]), 2)
            })
        return result
    except:
        return []


# -----------------------------------------------------------------------------
#  YAHOO FINANCE -- quote + history
# -----------------------------------------------------------------------------
def fetch_yahoo(pairs, fetch_hist=True):
    results = []
    tickers_list = [t for t, *_ in pairs]
    extras = {t: rest for t, *rest in pairs}
    print(f"  Saeki {len(tickers_list)} tickers...")

    data = yf.Tickers(" ".join(tickers_list))

    for ticker in tickers_list:
        extra = extras[ticker]
        name   = extra[0] if extra else ticker
        sector = extra[1] if len(extra) > 1 else ""
        try:
            info = data.tickers[ticker].info
            fi   = data.tickers[ticker].fast_info

            price    = fi.last_price or info.get("currentPrice") or info.get("regularMarketPrice")
            prev     = fi.previous_close or info.get("previousClose") or price
            chg_pct  = round(((price - prev) / prev * 100), 2) if prev else 0
            hi52     = fi.year_high or info.get("fiftyTwoWeekHigh")
            lo52     = fi.year_low  or info.get("fiftyTwoWeekLow")
            mktcap   = info.get("marketCap")
            pe       = info.get("trailingPE") or info.get("forwardPE")
            volume   = info.get("volume") or info.get("regularMarketVolume")
            avg_vol  = info.get("averageVolume")
            dividend = info.get("dividendYield")
            beta     = info.get("beta")
            desc     = info.get("longBusinessSummary", "")[:300] if info.get("longBusinessSummary") else ""

            hist_6m = []
            if fetch_hist:
                print(f"    Saeki sogu {ticker}...")
                hist_6m = fetch_history(ticker, period="6mo", interval="1d")

            results.append({
                "sym":      ticker,
                "name":     name,
                "sector":   sector,
                "market":   "us",
                "price":    round(price, 2) if price else None,
                "chgPct":   chg_pct,
                "up":       chg_pct >= 0,
                "hi52":     round(hi52, 2) if hi52 else None,
                "lo52":     round(lo52, 2) if lo52 else None,
                "mktcapB":  round(mktcap/1e9, 1) if mktcap else None,
                "pe":       round(pe, 1) if pe else None,
                "volume":   volume,
                "avgVol":   avg_vol,
                "dividend": round(dividend*100, 2) if dividend else None,
                "beta":     round(beta, 2) if beta else None,
                "desc":     desc,
                "hist":     hist_6m,
                "ok":       True,
            })
            print(f"    OK  {ticker:12s}  {price:.2f}  ({chg_pct:+.2f}%)  {len(hist_6m)} dagar sogu")

        except Exception as e:
            results.append({
                "sym": ticker, "name": name, "sector": sector, "market": "us",
                "ok": False, "error": str(e),
                "price": None, "chgPct": None, "up": True,
                "hi52": None, "lo52": None, "mktcapB": None, "pe": None,
                "volume": None, "avgVol": None, "dividend": None, "beta": None,
                "desc": "", "hist": [],
            })
            print(f"    VILLA  {ticker:12s}  {e}")

    return results


def fetch_indices(index_list):
    results = []
    tickers_list = [sym for sym, _ in index_list]
    names = {sym: name for sym, name in index_list}
    data = yf.Tickers(" ".join(tickers_list))
    for sym in tickers_list:
        try:
            fi = data.tickers[sym].fast_info
            price   = fi.last_price
            prev    = fi.previous_close or price
            chg_pct = round(((price - prev) / prev * 100), 2) if prev else 0
            print(f"    Saeki sogu {sym}...")
            hist_6m = fetch_history(sym, period="6mo", interval="1d")
            results.append({
                "sym": sym, "name": names[sym],
                "price": round(price, 2) if price else None,
                "chgPct": chg_pct, "up": chg_pct >= 0, "ok": True,
                "sector": "Index", "market": "idx",
                "hi52": None, "lo52": None, "mktcapB": None, "pe": None,
                "volume": None, "avgVol": None, "dividend": None, "beta": None,
                "desc": "", "hist": hist_6m
            })
            print(f"    OK  {sym:12s}  {price:.2f}  ({chg_pct:+.2f}%)  {len(hist_6m)} dagar sogu")
        except Exception as e:
            results.append({"sym": sym, "name": names[sym],
                            "price": None, "chgPct": 0, "up": True,
                            "ok": False, "sector": "Index", "market": "idx",
                            "hi52": None, "lo52": None, "mktcapB": None, "pe": None,
                            "volume": None, "avgVol": None, "dividend": None, "beta": None,
                            "desc": "", "hist": []})
            print(f"    VILLA  {sym:12s}  {e}")
    return results


# -----------------------------------------------------------------------------
#  AI AGENT
# -----------------------------------------------------------------------------
def build_market_ctx(us, etfs, indices):
    all_stocks = us + etfs
    movers = sorted([r for r in all_stocks if r.get("chgPct") is not None],
                    key=lambda r: abs(r["chgPct"]), reverse=True)[:6]
    movers_str = ", ".join(f"{r['sym']} {r['chgPct']:+.2f}%" for r in movers)
    sp500 = next((r for r in indices if r["sym"] == "^GSPC"), None)
    vix   = next((r for r in indices if r["sym"] == "^VIX"), None)
    return (
        f"Dagsetning: {datetime.now().strftime('%d.%m.%Y')} "
        f"S&P 500: {(str(sp500['price']) + ' (' + str(sp500['chgPct']) + '%)') if sp500 else 'okunnur'} "
        f"VIX: {vix['price'] if vix else 'okunnur'} "
        f"Staerstu hreyfingar: {movers_str or 'engar'}"
    )

SYSTEM_PROMPT = (
    "Thu ert klar hlutabrefaragjafi. Gefdu 4 hlutabrefatilloglur a islensku "
    "grunnadar a heimsatburdium og markadsgognum. Svaradu EINUNGIS med JSON array. "
    "Snid: [{action: BUY eda SELL eda WATCH, ticker: TICKER eins og AAPL, "
    "name: Nafn fyrirtaekis, reason: Skyring a islensku max 20 ord, "
    "trigger: Hvata atburdur max 8 ord}]. "
    "Tickers: AAPL MSFT NVDA TSLA GOOGL AMZN META NFLX JPM GS V BAC JNJ PFE UNH WMT KO XOM CVX VTI VOO QQQ."
)

def parse_suggestions(text):
    start = text.find("[")
    end   = text.rfind("]") + 1
    if start == -1:
        raise ValueError("Engin JSON array i svari")
    return json.loads(text[start:end])

def try_gemini(market_ctx):
    import urllib.request
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY vantar")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + " Markadsgogn: " + market_ctx + ". Svaradu med JSON array eingongu."}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return parse_suggestions(text)

def try_anthropic(market_ctx):
    import urllib.request
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY vantar")
    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 800,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": "Markadsgogn: " + market_ctx + ". Svaradu med JSON array eingongu."}]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        text = data["content"][0]["text"]
        return parse_suggestions(text)

def try_openrouter(market_ctx):
    import urllib.request
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY vantar")
    payload = json.dumps({
        "model": "qwen/qwen3-next-80b-a3b-instruct:free",
        "max_tokens": 800,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Markadsgogn: " + market_ctx + ". Svaradu med JSON array eingongu."}
        ]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
            "HTTP-Referer": "https://arnarsmara.github.io/ynwa2026",
            "X-Title": "StockBreak"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        text = data["choices"][0]["message"]["content"]
        return parse_suggestions(text)

def fetch_ai_suggestions(us, etfs, indices):
    market_ctx = build_market_ctx(us, etfs, indices)
    providers = [
        ("OpenRouter/Qwen", try_openrouter),
        ("Gemini",         try_gemini),
        ("Anthropic",      try_anthropic),
    ]
    for name, fn in providers:
        try:
            suggestions = fn(market_ctx)
            print(f"  OK  {len(suggestions)} AI tilloglur fengnar via {name}")
            return suggestions
        except Exception as e:
            print(f"  VILLA  {name}: {e} -- reyni naesta...")
    print("  VILLA  Allir AI veitur mistokust -- engar tilloglur")
    return []

# -----------------------------------------------------------------------------
#  MAIN
# -----------------------------------------------------------------------------
def main():
    print("\nStockBreak -- Uppfaersla hafin")
    print("=" * 48)

    print("\nAmeriskar hlutabref + soguleg gogn:")
    us = fetch_yahoo(STOCKS_US, fetch_hist=True)

    print("\nETF sjodir + soguleg gogn:")
    etfs = fetch_yahoo(ETFS, fetch_hist=True)

    print("\nVisitolur:")
    indices = fetch_indices(INDICES)

    print("\nAI Radgjafi:")
    suggestions = fetch_ai_suggestions(us, etfs, indices)

    now = datetime.now()
    output = {
        "updated":     now.strftime("%d.%m.%Y %H:%M:%S"),
        "updated_ts":  int(now.timestamp()),
        "indices":     indices,
        "us":          us,
        "etfs":        etfs,
        "suggestions": suggestions,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    ok_count   = sum(1 for g in [us, etfs, indices] for r in g if r.get("ok"))
    fail_count = sum(1 for g in [us, etfs, indices] for r in g if not r.get("ok"))
    hist_count = sum(len(r.get("hist", [])) for g in [us, etfs] for r in g)

    print(f"\nOK  {OUTPUT_FILE} vistad")
    print(f"   {ok_count} tickers tokust, {fail_count} misheppnudust")
    print(f"   {hist_count} soguleg gagnaskref")
    print(f"   Timi: {now.strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 48)


if __name__ == "__main__":
    main()
