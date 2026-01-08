from backend.push_manager import push_new_signals

def generate_signals(holdings: dict, lang: str = "de"):
    signals = []

    for asset, data in holdings.items():
        signal = {
            "asset": asset,
            "börse": data.get("börse"),
            "action": "HOLD",
            "confidence_score": 90,
            "risk": "konservativ",
            "suggested_amount_eur": None,
            "reason": "Stabile Position"
        }

        # einfache Demo-Logik
        if asset in ["IOTA", "SOL"]:
            signal["action"] = "BUY"
            signal["suggested_amount_eur"] = round(data["value_eur"] * 0.02, 2)
            signal["reason"] = "Konservatives Kaufsignal"

        signals.append(signal)

    push_new_signals(signals)

    return {
        "signale": signals,
        "sprache": lang
    }
