def generate_signals(holdings, lang="de"):
    signals = []

    btc_value = holdings.get("BTC", {}).get("value_eur", 0)

    for asset, data in holdings.items():
        action = "HOLD"
        confidence = "neutral"
        reason = "Markt neutral"

        # einfache Logik
        if asset != "BTC" and btc_value > 0:
            action = "WATCH"
            confidence = "mittel"
            reason = "BTC stabil – Altcoins beobachten"

        signals.append({
            "asset": asset,
            "börse": data.get("börse"),
            "action": action,
            "confidence": confidence,
            "reason": reason
        })

    if lang == "en":
        for s in signals:
            if s["action"] == "WATCH":
                s["action"] = "WATCH"
                s["reason"] = "BTC stable – altcoin opportunity forming"
        return {"signals": signals, "language": "en"}

    return {"signale": signals, "sprache": "de"}
