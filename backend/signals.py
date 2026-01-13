from typing import Dict, List
from .push_manager import push_new_signals


def generate_signals(lang: str = "de") -> Dict:
    signals: List[Dict] = [
        {
            "asset": "BTC",
            "börse": "Coinbase",
            "action": "HOLD",
            "confidence_score": 90,
            "risk": "konservativ",
            "suggested_amount_eur": None,
            "reason": "Stabile Position",
        },
        {
            "asset": "LTC",
            "börse": "Coinbase",
            "action": "HOLD",
            "confidence_score": 90,
            "risk": "konservativ",
            "suggested_amount_eur": None,
            "reason": "Stabile Position",
        },
        {
            "asset": "IOTA",
            "börse": "Bitunix",
            "action": "BUY",
            "confidence_score": 90,
            "risk": "konservativ",
            "suggested_amount_eur": 4.15,
            "reason": "Konservatives Kaufsignal",
        },
    ]

    # Push versuchen (aber nie crashen)
    try:
        ok, detail = push_new_signals(signals, lang=lang)
        print("Push result:", ok, detail)
    except Exception as e:
        print("⚠️ Push-Fehler ignoriert:", str(e))

    return {"signale": signals, "sprache": lang}
