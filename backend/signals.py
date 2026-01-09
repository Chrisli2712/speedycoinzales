def generate_signals(holdings: dict, lang: str = "de"):
    signals = []

    for asset, data in holdings.items():
        signals.append({
            "asset": asset,
            "börse": data.get("börse"),
            "action": "HOLD",
            "confidence_score": 90,
            "risk": "konservativ",
            "suggested_amount_eur": None,
            "reason": "Stabile Position"
        })

    return {
        "signale": signals,
        "sprache": lang
    }
