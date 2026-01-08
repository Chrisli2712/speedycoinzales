import requests
from .push_manager import send_push

# Einfache technische Indikatoren
def simple_moving_average(prices, window=3):
    if len(prices) < window:
        return sum(prices) / len(prices)
    return sum(prices[-window:]) / window

def fetch_crypto_price(asset, exchange):
    """
    Holt Live-Preis von CoinGecko API
    """
    # CoinGecko-ID Mapping (kann man erweitern)
    mapping = {"BTC": "bitcoin", "LTC": "litecoin", "IOTA": "iota", "SOL": "solana"}
    asset_id = mapping.get(asset.upper())
    if not asset_id:
        return None

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={asset_id}&vs_currencies=eur"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        return data[asset_id]["eur"]
    except Exception as e:
        print(f"[Fetch Error] {asset} {e}")
        return None

def generate_signals(holdings, lang="de"):
    signals = []

    for asset, info in holdings.items():
        live_price = fetch_crypto_price(asset, info["börse"])
        if live_price is None:
            continue

        # Dummy Historie für SMA
        history = [info["value_eur"]] * 5  # in Zukunft echte Preis-Historie
        sma = simple_moving_average(history, window=3)

        # Logik: Preis > SMA -> HOLD, Preis < SMA -> BUY
        if live_price < sma:
            action = "BUY"
            suggested_amount_eur = 10  # Beispielwert
        else:
            action = "HOLD"
            suggested_amount_eur = None

        signal = {
            "asset": asset,
            "börse": info["börse"],
            "action": action,
            "confidence_score": 100,
            "risk": "konservativ",
            "current_price_eur": live_price,
            "sma": sma,
            "suggested_amount_eur": suggested_amount_eur,
            "reason": f"Live Preis {live_price} EUR vs SMA {sma} EUR"
        }

        signals.append(signal)

    # Push-Benachrichtigung
    send_push(signals)

    return {"signale": signals, "sprache": lang}
