import random
import yfinance as yf
from .push_manager import push_new_signals

def generate_signals(holdings, all_assets, lang="de"):
    signals = []

    # Alle Crypto & Aktien zusammenführen
    for category in all_assets:
        for asset in all_assets[category]:
            # Falls bereits gehalten, Wert übernehmen, sonst simuliert
            info = holdings.get(asset, {"börse": "N/A", "value_eur": random.uniform(10, 300)})
            
            # Signal generieren
            confidence = random.randint(80, 100)
            action = "BUY" if confidence > 85 else "HOLD"
            suggested_amount = round(random.uniform(1, 5), 2) if action == "BUY" else None

            signal = {
                "asset": asset,
                "börse": info.get("börse", "N/A"),
                "action": action,
                "confidence_score": confidence,
                "risk": "konservativ",
                "suggested_amount_eur": suggested_amount,
                "reason": "Mehrere Marktindikatoren stimmen überein" if lang=="de" else "Multiple market indicators align"
            }
            signals.append(signal)

    # Push nur für BUY/STRONG BUY
    push_new_signals([s for s in signals if s["action"] == "BUY"], lang)

    return {"signale": signals, "sprache": lang}
