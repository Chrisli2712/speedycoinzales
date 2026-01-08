def generate_signals(holdings, lang="de"):
    signals = []

    for asset, data in holdings.items():
        signals.append({
            "asset": asset,
            "börse": data["börse"],
            "action": "HOLD",
            "confidence": "neutral",
            "reason": "Basis-Setup aktiv"
        })

    if lang == "en":
        return {"signals": signals, "language": "en"}

    return {"signale": signals, "sprache": "de"}
