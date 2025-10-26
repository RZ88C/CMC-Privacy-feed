#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, json, requests, datetime
from zoneinfo import ZoneInfo

SYM_LIST = ["XMR","ZEC","BDX","DASH","ZANO","ROSE","SCRT","XVG","PIVX","FIRO","ARRR","BEAM"]
API_KEY = os.getenv("CMC_API_KEY","").strip()
if not API_KEY:
    raise SystemExit("Missing CMC_API_KEY")

def get(url, params=None):
    r = requests.get(url, headers={"X-CMC_PRO_API_KEY": API_KEY}, params=params, timeout=45)
    r.raise_for_status()
    return r.json()

# 1) find privacy category id
cats = get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories", params={"limit":5000})
privacy = next((c for c in cats.get("data",[]) if "privacy" in (c.get("name","")+c.get("slug","")).lower()), None)
if not privacy: raise SystemExit("Privacy category not found")
cat_id = privacy["id"]

# 2) sector totals
cat = get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/category", params={"id":cat_id,"convert":"USD"})
sector = {
    "name": cat["data"]["name"],
    "market_cap": cat["data"]["market_cap"],
    "volume_24h": cat["data"]["volume_24h"],
}

# 3) coin quotes
q = get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
        params={"symbol":",".join(SYM_LIST), "convert":"USD,BTC"})

coins=[]
for sym, v in q["data"].items():
    USD, BTC = v["quote"]["USD"], v["quote"]["BTC"]
    coins.append({
        "sym": sym,
        "name": v["name"],
        "market_cap_usd": USD.get("market_cap"),
        "volume24_usd": USD.get("volume_24h"),
        "price_usd": USD.get("price"),
        "pct_24h_usd": USD.get("percent_change_24h"),
        "pct_7d_usd": USD.get("percent_change_7d"),
        "price_btc": BTC.get("price"),
        "pct_24h_btc": BTC.get("percent_change_24h"),
        "pct_7d_btc": BTC.get("percent_change_7d"),
    })

payload = {
    "timestamp": datetime.datetime.now(ZoneInfo("Europe/Warsaw")).isoformat(),
    "sector": sector,
    "coins": coins
}

with open("latest.json","w",encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("ok: wrote latest.json")
