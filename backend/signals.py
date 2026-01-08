from .push_manager import send_push

def generate_signals(holdings, lang="de"):
    signals = []

    for asset, info in holdings.items():
        # Dummy Logik: < 100 -> BUY, >=100 -> HOLD
        if info["value_eur"] < 100:
            action = "BUY"
            suggested_amount_eur = 10
        else:
            action = "HOLD"
            suggested_amount_eur = None

        signal = {
            "asset": asset,
            "börse": info["börse"],
            "action": action,
            "confidence_score": 100,
            "risk": "konservativ",
            "suggested_amount_eur": suggested_amount_eur,
            "reason": "Dummy-Regel: Wert <100 -> BUY, sonst HOLD"
        }
        signals.append(signal)

    # Push-Benachrichtigung für neue Signale
    send_push(signals)

    return {"signale": signals, "sprache": lang}
