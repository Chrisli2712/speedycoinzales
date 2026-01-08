# backend/signals.py

import json
from push_manager import push_new_signals

def generate_signals(holdings, lang="de"):
    signals = []

    for asset, info in holdings.items():
        action = "HOLD"
        if asset in ["IOTA", "SOL"]:
            action = "BUY"

        signal = {
            "asset": asset,
            "börse": info["börse"],
            "action": action,
            "confidence_score": 100,
            "risk": "konservativ",
            "suggested_amount_eur": 4.32 if action != "HOLD" else None,
            "reason": "Mehrere Marktindikatoren stimmen überein"
        }

        signals.append(signal)

    # 🔔 Jetzt nur neue Signale pushen
    push_new_signals(signals)

    return {"signals": signals, "language": lang}
