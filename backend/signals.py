CANDIDATES = [
    {"asset": "SOL", "börse": "Coinbase"},
    {"asset": "LINK", "börse": "Kraken"},
    {"asset": "NEAR", "börse": "Coinbase"},
]

def generate_signals(holdings, lang="de"):
    signals = []

    btc_value = holdings.get("BTC", {}).get("value_eur", 0)

    # 1️⃣ Eigene Holdings
    for asset, data in holdings.items():
        action = "HOLD"
        confidence = "hoch"
        reason = "Position aktiv, Markt stabil"

        if asset != "BTC" and btc_value > 0:
            action = "WATCH"
            confidence = "mittel"
            reason = "BTC stabil – Altcoin-Bewegung möglich"

        signals.append({
            "asset": asset,
            "börse": data["börse"],
            "action": action,
            "confidence": confidence,
            "reason": reason
        })

    # 2️⃣ Neue Kaufideen
    if btc_value > 20:
        for c in CANDIDATES:
            signals.append({
                "asset": c["asset"],
                "börse": c["börse"],
                "action": "BUY",
                "confidence": "hoch",
                "suggested_amount_eur": round(btc_value * 0.15, 2),
                "reason": "Kapitalrotation aus BTC in starken Altcoin"
            })

    if lang == "en":
        return {"signals": signals, "language": "en"}

    return {"signale": signals, "sprache": "de"}
