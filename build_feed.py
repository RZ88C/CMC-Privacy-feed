import requests, json, datetime, os

API_KEY = os.getenv("CMC_API_KEY")
HEADERS = {"X-CMC_PRO_API_KEY": API_KEY}
BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

# רשימת המטבעות למעקב
SYMBOLS = ["XMR","ZEC","BDX","DASH","ZANO","ROSE","SCRT","XVG","PIVX","FIRO","ARRR","BEAM"]

def fetch_quotes(convert):
    """שולף נתונים לפי מטבע יעד (USD או BTC)"""
    all_data = {}
    for symbol in SYMBOLS:
        try:
            r = requests.get(BASE_URL, params={"symbol": symbol, "convert": convert}, headers=HEADERS)
            data = r.json()
            if "data" in data and symbol in data["data"]:
                q = data["data"][symbol]["quote"][convert]
                all_data[symbol] = {
                    "price": round(q["price"], 8),
                    "market_cap": q["market_cap"],
                    "volume_24h": q["volume_24h"]
                }
        except Exception as e:
            print(f"⚠️ שגיאה בקריאת {symbol}: {e}")
    return all_data

def build_combined():
    usd_data = fetch_quotes("USD")
    btc_data = fetch_quotes("BTC")

    result = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "coins": {}
    }

    for sym in SYMBOLS:
        result["coins"][sym] = {
            "USD_price": usd_data.get(sym, {}).get("price"),
            "BTC_price": btc_data.get(sym, {}).get("price"),
            "market_cap": usd_data.get(sym, {}).get("market_cap"),
            "volume_24h": usd_data.get(sym, {}).get("volume_24h")
        }

    return result

if __name__ == "__main__":
    data = build_combined()
    with open("latest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✅ CMC Privacy feed successfully created at", data["timestamp"])
