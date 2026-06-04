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

        # Ab hier: zusätzliche Demo-Signale für Modus NORMAL
        {
            "asset": "ETH",
            "börse": "Coinbase",
            "action": "HOLD",
            "confidence_score": 85,
            "risk": "normal",
            "suggested_amount_eur": None,
            "reason": "Solides Signal, aber nicht stark genug für Sicher-Modus",
        },
        {
            "asset": "SOL",
            "börse": "Coinbase",
            "action": "HOLD",
            "confidence_score": 82,
            "risk": "normal",
            "suggested_amount_eur": None,
            "reason": "Normales Beobachtungssignal",
        },

        # Ab hier: zusätzliche Demo-Signale für Modus MUTIG
        {
            "asset": "XRP",
            "börse": "Bitunix",
            "action": "BUY",
            "confidence_score": 75,
            "risk": "aggressiv",
            "suggested_amount_eur": 3.50,
            "reason": "Mutiges Kaufsignal mit niedrigerer Sicherheit",
        },
        {
            "asset": "ADA",
            "börse": "Bitunix",
            "action": "HOLD",
            "confidence_score": 72,
            "risk": "aggressiv",
            "suggested_amount_eur": None,
            "reason": "Nur im Mutig-Modus sichtbar",
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
        "anzahl_signale": len(signals),
        "push": {
            "ok": push_ok,
            "detail": push_detail
        }
    }
