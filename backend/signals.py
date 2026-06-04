from typing import Dict, List
from .push_manager import push_new_signals


def generate_signals(lang: str = "de", mode: str = "konservativ") -> Dict:
    mode_settings = {
        "konservativ": {
            "label": "Konservativ",
            "min_confidence": 90
        },
        "normal": {
            "label": "Normal",
            "min_confidence": 80
        },
        "aggressiv": {
            "label": "Aggressiv",
            "min_confidence": 70
        }
    }

    current_mode = mode_settings.get(mode, mode_settings["konservativ"])
    min_confidence = current_mode["min_confidence"]

    all_signals: List[Dict] = [
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

    signals = [
        signal for signal in all_signals
        if int(signal.get("confidence_score", 0)) >= min_confidence
    ]

    try:
        push_ok, push_detail = push_new_signals(signals, lang=lang)
    except Exception as e:
        push_ok = False
        push_detail = f"Push Fehler ignoriert: {str(e)}"

    return {
        "signale": signals,
        "sprache": lang,
        "mode": mode,
        "modus": current_mode["label"],
        "min_confidence": min_confidence,
        "push": {
            "ok": push_ok,
            "detail": push_detail
        }
    }
