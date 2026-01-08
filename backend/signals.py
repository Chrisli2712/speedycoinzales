import random
from .push_manager import push_new_signals

def generate_signals(holdings, all_assets, lang="de"):
    signals = []

    owned_assets = set(holdings.keys())

    for category in all_assets:
        for asset in all_assets[category]:
            is_new = asset not in owned_assets

            info = holdings.get(asset, {"börse": "N/A", "value_eur": random.uniform(10, 300)})

            confidence = random.randint(80, 100)
            if is_new and confidence > 85:
                action = "BUY"
                suggested_amount = round(random.uniform(1, 5), 2)
            else:
                action = "HOLD"
                suggested_amount = None

            reason = "Mehrere Marktindikatoren stimmen überein" if lang=="de" else "Multiple market indicators align"

            signal = {
                "asset": asset,
                "börse": info.get("börse", "N/A"),
                "action": action,
                "confidence_score": confidence,
                "risk": "konservativ",
                "suggested_amount_eur": suggested_amount,
                "reason": reason,
                "is_new_asset": is_new
            }

            signals.append(signal)

    new_buys = [s for s in signals if s["action"] == "BUY" and s["is_new_asset"]]
    push_new_signals(new_buys, lang)

    # Sortieren nach Confidence absteigend
    signals.sort(key=lambda x: x["confidence_score"], reverse=True)

    return {"signale": signals, "sprache": lang}
