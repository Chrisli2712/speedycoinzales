import requests
from .push_manager import send_push

# --- Technische Indikatoren ---
def simple_moving_average(prices, window=3):
    if len(prices) < window:
        return sum(prices) / len(prices)
    return sum(prices[-window:]) / window

# --- Live Preisabfrage ---
def fetch_price(asset, exchange_type="crypto"):
    """
    Holt Live-Preis:
    - Crypto über CoinGecko
    - Aktien über Yahoo Finance
    """
    try:
        if exchange_type == "crypto":
            mapping = {"BTC": "bitcoin", "LTC": "litecoin", "IOTA": "iota", "SOL": "solana"}
            asset_id = mapping.get(asset.upper())
            if not asset_id:
                return None
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={asset_id}&vs_currencies=eur"
            response = requests.get(url, timeout=5)
            return response.json()[asset_id]["eur"]
        elif exchange_type == "stock":
            # Yahoo Finance API (Public CSV Endpoint)
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={asset}"
            response = requests.get(url, timeout=5).json()
            return float(response["quoteResponse"]["result"][0]["regularMarketPrice"])
    except Exception as e:
        print(f"[Fetch Error] {asset}: {e}")
        return None

# --- Signale generieren ---
def generate_signals(holdings, lang="de"):
    signals = []

    for asset, info in holdings.items():
        exchange_type = info.get("type", "crypto")  # crypto oder stock
        live_price = fetch_price(asset, exchange_type)
        if live_price is None:
            continue

        history = [info["value_eur"]] * 5  # Dummy Historie, kann erweitert werden
        sma = simple_moving_average(history, window=3)

        if live_price < sma:
            action = "BUY"
            suggested_amount_eur = 10  # Beispielwert
        else:
            action = "HOLD"
            suggested_amount_eur = None

        signal = {
            "asset": asset,
            "börse": info.get("börse", "unknown"),
            "action": action,
            "confidence_score": 100,
            "risk": info.get("risk", "konservativ"),
            "current_price_eur": live_price,
            "sma": sma,
            "suggested_amount_eur": suggested_amount_eur,
            "reason": f"Live Preis {live_price} EUR vs SMA {sma} EUR"
        }

        signals.append(signal)

    # Push nur für BUY/SELL
    send_push(signals)

    return {"signale": signals, "sprache": lang}
