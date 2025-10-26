#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json, requests, datetime, sys
from zoneinfo import ZoneInfo

SYM_LIST = ["XMR","ZEC","BDX","DASH","ZANO","ROSE","SCRT","XVG","PIVX","FIRO","ARRR","BEAM"]
API_KEY = os.getenv("CMC_API_KEY", "").strip()
if not API_KEY:
    print("ERROR: Missing CMC_API_KEY env var", file=sys.stderr)
    sys.exit(1)

def get(url, params=None, expect_key=None):
    """GET עם טיפול בשגיאות והדפסה ידידותית ללוגים."""
    try:
        r = requests.get(url, headers={"X-CMC_PRO_API_KEY": API_KEY}, params=params, timeout=45)
        status = r.status_code
        if status != 200:
            print(f"HTTP {status} on {url}", file=sys.stderr)
            print("Body:", r.text[:500], file=sys.stderr)
            return None
        js = r.json()
        if expect_key and expect_key not in js:
            print(f"Unexpected JSON (missing '{expect_key}') from {url}", file=sys.stderr)
        return js
    except Exception as e:
        print(f"EXC on {url}: {e}", file=sys.stderr)
        return None

out = {"timestamp": datetime.datetime.now(ZoneInfo("Europe/Warsaw")).isoformat()}

# 1) ננסה לקרוא את רשימת הקטגוריות כדי למצוא את Privacy
cats = get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories",
           params={"limit": 5000}, expect_key="data")

privacy_id = None
if cats and isinstance(cats.get("data"), list):
    for c in cats["data"]:
        name = (c.get("name") or "").lower()
        slug = (c.get("slug") or "").lower()
        if "privacy" in name or "privacy" in slug:
            privacy_id = c.get("id")
            break

# 2) אם מצאנו ID – ננסה לשלוף סקטור; אם לא/נכשל – נחשב סכום ידני מה-12 מטבעות
sector = {"name": "Privacy (CMC)", "market_cap": None, "volume_24h": None, "source": None}

if privacy_id:
    cat = get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/category",
              params={"id": privacy_id, "convert": "USD"}, expect_key="data")
    if cat and cat.get("data"):
        sector["market_cap"] = cat["data"].get("market_cap")
        sector["volume_24h"] = cat["data"].get("volume_24h")
        sector["name"] = cat["data"].get("name") or sector["name"]
        sector["source"] = "category_endpoint"
    else:
        sector["source"] = "category_endpoint_failed"
else:
    sector["source"] = "no_category_id"

# 3) תמיד נשלוף את הנתונים ל-12 המטבעות
quotes = get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
             params={"symbol": ",".join(SYM_LIST), "convert": "USD,BTC"}, expect_key="data")

coins = []
if quotes and quotes.get("data"):
    for sym, v in quotes["data"].items():
        USD = v["quote"].get("USD", {})
        BTC = v["quote"].get("BTC", {})
        coins.append({
            "sym": sym,
            "name": v.get("name"),
            "market_cap_usd": USD.get("market_cap"),
            "volume24_usd": USD.get("volume_24h"),
            "price_usd": USD.get("price"),
            "pct_24h_usd": USD.get("percent_change_24h"),
            "pct_7d_usd": USD.get("percent_change_7d"),
            "price_btc": BTC.get("price"),
            "pct_24h_btc": BTC.get("percent_change_24h"),
            "pct_7d_btc": BTC.get("percent_change_7d"),
        })
else:
    print("ERROR: quotes/latest failed – cannot proceed", file=sys.stderr)
    sys.exit(2)

# 4) Fallback: אם סכומי הסקטור חסרים/נכשלו – נחשב כסכום ה-12 מטבעות (עדיין CMC)
if not sector["market_cap"] or not sector["volume_24h"]:
    total_mcap = sum([c["market_cap_usd"] or 0 for c in coins])
    total_vol  = sum([c["volume24_usd"] or 0 for c in coins])
    sector["market_cap"] = total_mcap
    sector["volume_24h"] = total_vol
    if not sector["source"]:
        sector["source"] = "fallback_sum_of_12"

out["sector"] = sector
out["coins"] = coins

with open("latest.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("ok: wrote latest.json")
