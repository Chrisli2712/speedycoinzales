from .push_manager import push_new_signals

def generate_signals(holdings, lang="de"):
    """
    Dummy-Signalgenerator.
    - HOLT die aktuellen Signale aus holdings
    - Gibt eine Liste von Kauf/Verkauf/Hold zurück
    """
    signals = []

    for asset, info in holdings.items():
        # Dummy-Logik: wenn Wert < 100 -> BUY, sonst HOLD
        if info["value_eur"] < 100:
            action = "BUY"
            suggested_amount_eur = 10  # Beispiel
        else:
            action = "HOLD"
            suggested_amount_eur = None

        signals.append({
            "asset": asset,
            "börse": info["börse"],
            "action": action,
            "confidence_score": 100,
            "risk": "konservativ",
            "suggested_amount_eur": suggested_amount_eur,
            "reason": "Dummy-Regel: Wert < 100 -> BUY, sonst HOLD"
        })

    # Push-Benachrichtigung für BUY/SELL
    push_new_signals(signals)

    # API-Ausgabe
    return {"signale": signals, "sprache": lang}
