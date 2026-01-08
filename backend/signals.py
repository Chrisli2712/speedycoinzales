def score_signal(trend, volatility, btc_stable, relative_strength):
    score = 0

    if trend == "up":
        score += 25
    if volatility == "low":
        score += 20
    if btc_stable:
        score += 20
    if relative_strength == "high":
        score += 20

    score += 15  # konservativer Bonus
    return score


def generate_signals(holdings, lang="de"):
    signals = []

    btc_value = holdings.get("BTC", {}).get("value_eur", 0)

    # Beispielhafte Marktannahmen (werden später live)
    market_trend = "up"
    volatility = "low"
    btc_stable = True

    # Beste Kandidaten (konservativ)
    candidates = [
        {"asset": "BTC", "börse": "Coinbase", "rs": "high"},
        {"asset": "IOTA", "börse": "Bitunix", "rs": "high"},
        {"asset": "SOL", "börse": "Coinbase", "rs": "high"},
    ]

    for c in candidates:
        score = score_signal(
            market_trend,
            volatility,
            btc_stable,
            c["rs"]
        )

        if score >= 80:
            signals.append({
                "asset": c["asset"],
                "börse": c["börse"],
                "action": "BUY" if c["asset"] != "BTC" else "HOLD",
                "confidence_score": score,
                "risk": "konservativ",
                "suggested_amount_eur": round(btc_value * 0.1, 2)
                if c["asset"] != "BTC" else None,
                "reason": "Mehrere Marktindikatoren stimmen überein"
            })

    if lang == "en":
        return {"signals": signals, "language": "en"}

    return {"signale": signals, "sprache": "de"}
