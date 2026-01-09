from backend.push_manager import push_new_signals

def generate_signals(holdings, lang="de"):
    # Beispielhafte Signale
    signals = [
        {"asset": "BTC", "börse": "Coinbase", "action": "HOLD", "confidence_score": 90, "risk": "konservativ", "suggested_amount_eur": None, "reason": "Stabile Position"},
        {"asset": "LTC", "börse": "Coinbase", "action": "HOLD", "confidence_score": 90, "risk": "konservativ", "suggested_amount_eur": None, "reason": "Stabile Position"},
        {"asset": "IOTA", "börse": "Bitunix", "action": "BUY", "confidence_score": 90, "risk": "konservativ", "suggested_amount_eur": 4.15, "reason": "Konservatives Kaufsignal"}
    ]
    
    # Push senden
    push_new_signals(signals)
    
    return {"signale": signals, "sprache": lang}
