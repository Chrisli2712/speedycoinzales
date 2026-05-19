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

    try:
        push_ok, push_detail = push_new_signals(signals, lang=lang)
    except Exception as e:
        push_ok = False
        push_detail = f"Push Fehler ignoriert: {str(e)}"

    return {
        "signale": signals,
        "sprache": lang,
        "push": {
            "ok": push_ok,
            "detail": push_detail
        }
    }
