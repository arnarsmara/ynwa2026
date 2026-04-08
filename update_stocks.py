"""
update_stocks.py — StockBreak
Sækir gögn frá Yahoo Finance og Nasdaq Nordic og skrifar stocks_data.json
sem vefsíðan les sjálfkrafa.

Keyra:  python update_stocks.py
Eða:    Setja upp í Windows Task Scheduler til að keyra á 5 mín fresti
"""

import yfinance as yf
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

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
    ("MAREL",   "Marel hf.",               "IS0000000388"),
    ("ARION",   "Arion banki hf.",          "IS0000028302"),
    ("ICEAIR",  "Icelandair Group hf.",     "IS0000003808"),
    ("SIMINN",  "Siminn hf.",               "IS0000000701"),
    ("EIMSKIP", "Eimskipafélag Íslands hf.","IS0000000594"),
    ("REGINN",  "Reiknir hf.",              "IS0000018675"),
    ("HAGA",    "Hagar hf.",                "IS0000017123"),
    ("VIS",     "Vátryggingafélag Íslands", "IS0000004269"),
]

OUTPUT_FILE = "stocks_data.json"

# ─────────────────────────────────────────────────────────────────────────────
#  YAHOO FINANCE
# ─────────────────────────────────────────────────────────────────────────────
def fetch_yahoo(pairs):
    results = []
    tickers_list = [t for t, *_ in pairs]
    extras = {t: rest for t, *rest in pairs}
    print(f"  Sæki {len(tickers_list)} tickers...")

    data = yf.Tickers(" ".join(tickers_list))
    for ticker in tickers_list:
        extra = extras[ticker]
        name = extra[0] if extra else ticker
        sector = extra[1] if len(extra) > 1 else ""
        try:
            info = data.tickers[ticker].info
            fi   = data.tickers[ticker].fast_info
            price   = fi.last_price or info.get("currentPrice") or info.get("regularMarketPrice")
            prev    = fi.previous_close or info.get("previousClose") or price
            chg_pct = round(((price - prev) / prev * 100), 2) if prev else 0
            hi52    = fi.year_high or info.get("fiftyTwoWeekHigh")
            lo52    = fi.year_low  or info.get("fiftyTwoWeekLow")
            mktcap  = info.get("marketCap")
            pe      = info.get("trailingPE") or info.get("forwardPE")

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
                "ok":       True,
            })
            print(f"    ✅  {ticker:12s}  {price:.2f}  ({chg_pct:+.2f}%)")
        except Exception as e:
            results.append({"sym": ticker, "name": name, "sector": sector,
                            "market": "us", "ok": False, "error": str(e),
                            "price": None, "chgPct": None, "up": True,
                            "hi52": None, "lo52": None, "mktcapB": None, "pe": None})
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
            results.append({
                "sym": sym, "name": names[sym],
                "price": round(price, 2) if price else None,
                "chgPct": chg_pct, "up": chg_pct >= 0, "ok": True
            })
            print(f"    ✅  {sym:12s}  {price:.2f}  ({chg_pct:+.2f}%)")
        except Exception as e:
            results.append({"sym": sym, "name": names[sym],
                            "price": None, "chgPct": 0, "up": True, "ok": False})
            print(f"    ⚠️   {sym:12s}  VILLA: {e}")
    return results


# ─────────────────────────────────────────────────────────────────────────────
#  NASDAQ NORDIC — íslenskar hlutabréf
# ─────────────────────────────────────────────────────────────────────────────
def fetch_icelandic(icelandic_list):
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/html",
    }

    for ticker, name, isin in icelandic_list:
        price = None
        chg_pct = None
        hi52 = None
        lo52 = None

        # Leið 1: Nasdaq Nordic JSON API
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

        # Leið 2: keldan.is scraping ef Nasdaq Nordic virkar ekki
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
                "sym": ticker, "name": name, "sector": "Íslenskt",
                "market": "is",
                "price": int(price),
                "chgPct": round(chg_pct, 2) if chg_pct is not None else 0,
                "up": (chg_pct or 0) >= 0,
                "hi52": int(hi52) if hi52 else None,
                "lo52": int(lo52) if lo52 else None,
                "mktcapB": None, "pe": None, "ok": True
            })
            chg_str = f"{chg_pct:+.2f}%" if chg_pct is not None else "?"
            print(f"    ✅  {ticker:12s}  {price:.0f} kr  ({chg_str})")
        else:
            results.append({
                "sym": ticker, "name": name, "sector": "Íslenskt",
                "market": "is", "price": None, "chgPct": None, "up": True,
                "hi52": None, "lo52": None, "mktcapB": None, "pe": None, "ok": False
            })
            print(f"    ⚠️   {ticker:12s}  Gat ekki sótt verð")

    return results


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n📊  StockBreak — Uppfærsla hafin")
    print("=" * 48)

    print("\n🇺🇸  Amerískar hlutabréf:")
    us = fetch_yahoo(STOCKS_US)

    print("\n📈  ETF sjóðir:")
    etfs = fetch_yahoo(ETFS)

    print("\n📊  Vísitölur:")
    indices = fetch_indices(INDICES)

    print("\n🇮🇸  Íslenskar hlutabréf:")
    is_stocks = fetch_icelandic(ICELANDIC)

    now = datetime.now()
    output = {
        "updated":    now.strftime("%d.%m.%Y %H:%M:%S"),
        "updated_ts": int(now.timestamp()),
        "indices":    indices,
        "us":         us,
        "etfs":       etfs,
        "iceland":    is_stocks,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    ok_count   = sum(1 for g in [us, etfs, indices, is_stocks] for r in g if r.get("ok"))
    fail_count = sum(1 for g in [us, etfs, indices, is_stocks] for r in g if not r.get("ok"))

    print(f"\n✅  {OUTPUT_FILE} vistað")
    print(f"   {ok_count} tickers tókust, {fail_count} misheppnuðust")
    print(f"   Tími: {now.strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 48)


if __name__ == "__main__":
    main()
