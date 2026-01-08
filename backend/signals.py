import random
import yfinance as yf
from .push_manager import push_new_signals

def generate_signals(holdings, all_assets, lang="de"):
    signals = []

    # Assets, die du bereits besitzt
    owned_assets = set(holdings.keys())

    # Alle Crypto & Aktien zusammenführen
    for category in all_assets:
        for asset in all_assets[category]:
            # Prüfen, ob Asset neu ist
            is_new = asset not in owned_assets

            # Wert übernehmen oder simulieren
            info = holdings.get(asset, {"börse": "N/A", "value_eur": random.uniform(10, 300)})

            # Signal generieren
            confidence = random.randint(80, 100)
            if is_new and confidence > 85:
                action = "BUY"  # Smart Buy nur für neue Assets
                suggested_amount = round(random.uniform(1, 5), 2)
            else:
                action = "HOLD"
                suggested_amount = None

            signal = {
                "asset": asset,
                "börse": info.get("börse", "N/A"),
                "action": action,
                "confidence_score": confidence,
                "risk": "konservativ",
                "suggested_amount_eur": suggested_amount,
                "reason": "Mehrere Marktindikatoren stimmen überein" if lang=="de" else "Multiple market indicators align",
                "is_new_asset": is_new
            }
            signals.append(signal)

    # Push nur für neue BUY-Assets
    new_buys = [s for s in signals if s["action"] == "BUY" and s["is_new_asset"]]
    push_new_signals(new_buys, lang)

    return {"signale": signals, "sprache": lang}
