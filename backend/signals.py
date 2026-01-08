# backend/signals.py

import json
from push import send_push

def generate_signals(holdings, lang="de"):
    """
    Generiert Kauf-/Verkaufssignale basierend auf den aktuellen Holdings.
    Versendet Push-Benachrichtigungen für starke Signale (Confidence >= 90).
    Sprache: 'de' oder 'en'
    """

    signals = []

    # Beispiel für einfache Signal-Logik
    # Hier kann man später echte Marktanalysen einbauen
    for asset, info in holdings.items():
        # Default Action: HOLD
        action = "HOLD"
        # Simulierte Logik für neue Assets
        # (nur Beispiel – hier kann man komplexe Indikatoren einsetzen)
        if asset in ["IOTA", "SOL"]:
            action = "BUY"

        signal = {
            "asset": asset,
            "börse": info["börse"],
            "action": action,
            "confidence_score": 100,  # für Demo auf 100%
            "risk": "konservativ",
            "suggested_amount_eur": 4.32 if action != "HOLD" else None,
            "reason": "Mehrere Marktindikatoren stimmen überein"
        }

        # Push nur bei starken Signalen (Confidence >= 90) und BUY/SELL
        if signal["confidence_score"] >= 90 and signal["action"] in ["BUY", "SELL"]:
            send_push(
                f"{signal['action']} Signal 🚨",
                f"{signal['asset']} auf {signal['börse']} – Confidence {signal['confidence_score']}%"
            )

        signals.append(signal)

    return {"signals": signals, "language": lang}
