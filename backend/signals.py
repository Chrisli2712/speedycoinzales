# backend/signals.py

import json
from push_manager import push_new_signals

def generate_signals(holdings, lang="de"):
    signals = []

    for asset, info in holdings.items():
        # Wenn du bereits besitzt -> HOLD oder SELL
        if info["stueck"] > 0:
            action = "HOLD"  # oder hier Logik für SELL hinzufügen
        else:
            action = "BUY"  # neue Assets vorschlagen

        signal = {
            "asset": asset,
            "börse": info["börse"],
            "action": action,
            "confidence_score": 100,  # Dummy für jetzt
            "risk": "konservativ",
            "suggested_amount_eur": 4.32 if action != "HOLD" else None,
            "reason": "Mehrere Marktindikatoren stimmen überein"
        }

        signals.append(signal)

    # 🔔 Nur neue Signale pushen
    push_new_signals(signals)

    return {"signals": signals, "language": lang}
