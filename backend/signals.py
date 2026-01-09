from typing import List, Dict
from .push_manager import push_new_signals


def generate_signals(
    holdings: Dict[str, float] | None = None,
    lang: str = "de"
) -> Dict:
    """
    Generiert Trading-Signale.
    Aktuell statisch (MVP), später erweiterbar mit echten Marktdaten.
    """

    # 🔹 Statische Beispiel-Signale (stabil & render-sicher)
    signals: List[Dict] = [
        {
            "asset": "BTC",
            "börse": "Coinbase",
            "action": "HOLD",
            "confidence_score": 90,
            "risk": "konservativ",
            "suggested_amount_eur": None,
            "reason": "Stabile Marktstruktur",
        },
        {
            "asset": "LTC",
            "börse": "Coinbase",
            "action": "HOLD",
            "confidence_score": 90,
            "risk": "konservativ",
            "suggested_amount_eur": None,
            "reason": "Geringe Volatilität",
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

    # 🔔 Push senden (darf NIE crashen)
    try:
        push_new_signals(signals)
    except Exception as e:
        print("⚠️ Push-Fehler ignoriert:", str(e))

    # 🌍 API-Response
    return {
        "signale": signals,
        "sprache": lang,
    }
