def generate_signals(holdings, language="de"):
    signals = []

    for h in holdings:
        asset = h["asset"]
        exchange = h["exchange"]
        amount = h["amount"]

        if amount > 0:
            action = "HOLD"
            confidence = 90
            reason = "Stabile Position"
            suggested_amount = None
        else:
            action = "BUY"
            confidence = 85
            reason = "Konservatives Kaufsignal"
            suggested_amount = 5.0

        signals.append({
            "asset": asset,
            "börse": exchange,
            "action": action,
            "confidence_score": confidence,
            "risk": "konservativ",
            "suggested_amount_eur": suggested_amount,
            "reason": reason
        })

    return {
        "signale": signals,
        "sprache": language
    }
