"""
update_stocks.py — StockBreak
Sækir gögn frá Yahoo Finance + söguleg gögn fyrir línurit
Skrifar stocks_data.json sem vefsíðan les.

Keyra:  python update_stocks.py
"""

import yfinance as yf
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
#  STILLINGAR
# ─────────────────────────────────────────────────────────────────────────────

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

ICELANDIC = [
    ("MAREL",   "Marel hf.",                "IS0000000388"),
    ("ARION",   "Arion banki hf.",           "IS0000028302"),
    ("ICEAIR",  "Icelandair Group hf.",      "IS0000003808"),
    ("SIMINN",  "Siminn hf.",                "IS0000000701"),
    ("EIMSKIP", "Eimskipafélag Íslands hf.", "IS0000000594"),
    ("REGINN",  "Reiknir hf.",               "IS0000018675"),
    ("HAGA",    "Hagar hf.",                 "IS0000017123"),
    ("VIS",     "Vátryggingafélag Íslands",  "IS0000004269"),
]

OUTPUT_FILE = "stocks_data.json"

# ─────────────────────────────────────────────────────────────────────────────
#  SÖGULEG GÖGN — fyrir línurit
# ─────────────────────────────────────────────────────────────────────────────
def fetch_history(ticker_sym, period="6mo", interval="1d"):
    """Skilar lista af {date, close} fyrir línurit."""
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


# ─────────────────────────────────────────────────────────────────────────────
#  YAHOO FINANCE — quote + history
# ─────────────────────────────────────────────────────────────────────────────
def fetch_yahoo(pairs, fetch_hist=True):
    results = []
    tickers_list = [t for t, *_ in pairs]
    extras = {t: rest for t, *rest in pairs}
    print(f"  Sæki {len(tickers_list)} tickers...")

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

            # Söguleg gögn
            hist_6m = []
            if fetch_hist:
                print(f"    📈 Sæki sögu {ticker}...")
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
            print(f"    ✅  {ticker:12s}  {price:.2f}  ({chg_pct:+.2f}%)  {len(hist_6m)} dagar sögu")

        except Exception as e:
            results.append({
                "sym": ticker, "name": name, "sector": sector, "market": "us",
                "ok": False, "error": str(e),
                "price": None, "chgPct": None, "up": True,
                "hi52": None, "lo52": None, "mktcapB": None, "pe": None,
                "volume": None, "avgVol": None, "dividend": None, "beta": None,
                "desc": "", "hist": [],
            })
            print(f"    ⚠️   {ticker:12s}  VILLA: {e}")

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
            print(f"    📈 Sæki sögu {sym}...")
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
            print(f"    ✅  {sym:12s}  {price:.2f}  ({chg_pct:+.2f}%)  {len(hist_6m)} dagar sögu")
        except Exception as e:
            results.append({"sym": sym, "name": names[sym],
                            "price": None, "chgPct": 0, "up": True,
                            "ok": False, "sector": "Index", "market": "idx",
                            "hi52": None, "lo52": None, "mktcapB": None, "pe": None,
                            "volume": None, "avgVol": None, "dividend": None, "beta": None,
                            "desc": "", "hist": []})
            print(f"    ⚠️   {sym:12s}  VILLA: {e}")
    return results


# ─────────────────────────────────────────────────────────────────────────────
#  NASDAQ NORDIC — íslenskar hlutabréf
# ─────────────────────────────────────────────────────────────────────────────
def fetch_icelandic(icelandic_list):
    results = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for ticker, name, isin in icelandic_list:
        price = None
        chg_pct = None
        hi52 = None
        lo52 = None

        try:
            url = f"https://www.nasdaqomxnordic.com/api/instruments/search?query={ticker}&markets=XICE"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                d = r.json()
                rows = d.get("rows", d.get("instruments", d if isinstance(d, list) else []))
                if rows:
                    item = rows[0]
                    def pn(v):
                        if v is None: return None
                        try: return float(str(v).replace(",",".").replace(" ",""))
                        except: return None
                    price   = pn(item.get("lastPrice") or item.get("last") or item.get("price"))
                    prev    = pn(item.get("previousClose") or item.get("prevClose"))
                    chg_raw = pn(item.get("changePercent") or item.get("changePercentage"))
                    if chg_raw is not None:
                        chg_pct = round(chg_raw, 2)
                    elif price and prev and prev != 0:
                        chg_pct = round((price - prev) / prev * 100, 2)
                    hi52 = pn(item.get("high52w") or item.get("fiftyTwoWeekHigh"))
                    lo52 = pn(item.get("low52w")  or item.get("fiftyTwoWeekLow"))
        except:
            pass

        if not price:
            try:
                r2 = requests.get(
                    f"https://www.keldan.is/Markadir/Hlutabref/{ticker}",
                    headers={"User-Agent": "Mozilla/5.0"}, timeout=10, verify=False
                )
                if r2.status_code == 200:
                    soup = BeautifulSoup(r2.text, "html.parser")
                    for table in soup.find_all("table"):
                        for row in table.find_all("tr"):
                            cells = row.find_all(["td","th"])
                            if len(cells) >= 2:
                                label = cells[0].get_text(strip=True).lower()
                                val_txt = cells[1].get_text(strip=True)
                                try:
                                    val = float(val_txt.replace(".","").replace(",",".").replace(" ","").replace("kr",""))
                                    if any(x in label for x in ["síðasta","last","verð"]) and not price:
                                        price = val
                                    elif any(x in label for x in ["breyting","%"]) and chg_pct is None:
                                        chg_pct = val
                                except:
                                    pass
            except:
                pass

        if price:
            results.append({
                "sym": ticker, "name": name, "sector": "Íslenskt", "market": "is",
                "price": int(price),
                "chgPct": round(chg_pct, 2) if chg_pct is not None else 0,
                "up": (chg_pct or 0) >= 0,
                "hi52": int(hi52) if hi52 else None,
                "lo52": int(lo52) if lo52 else None,
                "mktcapB": None, "pe": None,
                "volume": None, "avgVol": None, "dividend": None, "beta": None,
                "desc": "", "hist": [], "ok": True
            })
            chg_str = f"{chg_pct:+.2f}%" if chg_pct is not None else "?"
            print(f"    ✅  {ticker:12s}  {price:.0f} kr  ({chg_str})")
        else:
            results.append({
                "sym": ticker, "name": name, "sector": "Íslenskt", "market": "is",
                "price": None, "chgPct": None, "up": True,
                "hi52": None, "lo52": None, "mktcapB": None, "pe": None,
                "volume": None, "avgVol": None, "dividend": None, "beta": None,
                "desc": "", "hist": [], "ok": False
            })
            print(f"    ⚠️   {ticker:12s}  Gat ekki sótt verð")

    return results




# ─────────────────────────────────────────────────────────────────────────────
#  AI AGENT — Gemini + Anthropic fallback
# ─────────────────────────────────────────────────────────────────────────────
def build_market_ctx(us, etfs, indices):
    all_stocks = us + etfs
    movers = sorted([r for r in all_stocks if r.get("chgPct") is not None],
                    key=lambda r: abs(r["chgPct"]), reverse=True)[:6]
    movers_str = ", ".join(f"{r['sym']} {r['chgPct']:+.2f}%" for r in movers)
    sp500 = next((r for r in indices if r["sym"] == "^GSPC"), None)
    vix   = next((r for r in indices if r["sym"] == "^VIX"), None)
    return f"""Dagsetning: {datetime.now().strftime("%d.%m.%Y")}
S&P 500: {(str(sp500["price"]) + " (" + str(sp500["chgPct"]) + "%)") if sp500 else "okunnur"}
VIX: {vix["price"] if vix else "okunnur"}
Staerstu hreyfingar: {movers_str or "engar"}"""

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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
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
        "model": "claude-sonnet-4-20250514",
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

def fetch_ai_suggestions(us, etfs, indices):
    market_ctx = build_market_ctx(us, etfs, indices)
    providers = [
        ("Gemini",    try_gemini),
        ("Anthropic", try_anthropic),
    ]
    for name, fn in providers:
        try:
            suggestions = fn(market_ctx)
            print(f"  ✅  {len(suggestions)} AI tilloglur fengnar via {name}")
            return suggestions
        except Exception as e:
            print(f"  ⚠️  {name} mistokst: {e} — reyni naesta...")
    print("  ⚠️  Allir AI veitur mistokust — engar tilloglur")
    return []
# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n📊  StockBreak — Uppfærsla hafin")
    print("=" * 48)

    print("\n🇺🇸  Amerískar hlutabréf + söguleg gögn:")
    us = fetch_yahoo(STOCKS_US, fetch_hist=True)

    print("\n📈  ETF sjóðir + söguleg gögn:")
    etfs = fetch_yahoo(ETFS, fetch_hist=True)

    print("\n📊  Vísitölur:")
    indices = fetch_indices(INDICES)

    print("\n🇮🇸  Íslenskar hlutabréf:")
    is_stocks = fetch_icelandic(ICELANDIC)

    print("\n🤖  AI Radgjafi:")
    suggestions = fetch_ai_suggestions(us, etfs, indices)

    now = datetime.now()
    output = {
        "updated":      now.strftime("%d.%m.%Y %H:%M:%S"),
        "updated_ts":   int(now.timestamp()),
        "indices":      indices,
        "us":           us,
        "etfs":         etfs,
        "iceland":      is_stocks,
        "suggestions":  suggestions,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    ok_count   = sum(1 for g in [us, etfs, indices, is_stocks] for r in g if r.get("ok"))
    fail_count = sum(1 for g in [us, etfs, indices, is_stocks] for r in g if not r.get("ok"))
    hist_count = sum(len(r.get("hist",[])) for g in [us, etfs] for r in g)

    print(f"\n✅  {OUTPUT_FILE} vistað")
    print(f"   {ok_count} tickers tókust, {fail_count} misheppnuðust")
    print(f"   {hist_count} söguleg gagnaskref")
    print(f"   Tími: {now.strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 48)


if __name__ == "__main__":
    main()

