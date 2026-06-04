from typing import Dict, List, Optional
from datetime import datetime, timezone
import os
import requests

from .push_manager import push_new_signals


COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")


COINS = [
    {
        "id": "bitcoin",
        "asset": "BTC",
        "börse": "Coinbase"
    },
    {
        "id": "litecoin",
        "asset": "LTC",
        "börse": "Coinbase"
    },
    {
        "id": "iota",
        "asset": "IOTA",
        "börse": "Bitunix"
    },
    {
        "id": "ethereum",
        "asset": "ETH",
        "börse": "Coinbase"
    },
    {
        "id": "solana",
        "asset": "SOL",
        "börse": "Coinbase"
    },
    {
        "id": "ripple",
        "asset": "XRP",
        "börse": "Bitunix"
    },
    {
        "id": "cardano",
        "asset": "ADA",
        "börse": "Bitunix"
    },
]


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

    try:
        market_data = fetch_live_market_data()
        all_signals = build_live_signals(market_data)

        signals = [
            signal for signal in all_signals
            if int(signal.get("confidence_score", 0)) >= min_confidence
        ]

        # Wichtig:
        # Push nur für starke BUY/SELL-Signale.
        # Dadurch wird nicht bei jeder kleinen Kursbewegung gespammt.
        push_signals = [
            signal for signal in signals
            if signal.get("action") in ["BUY", "SELL"]
            and int(signal.get("confidence_score", 0)) >= 90
        ]

        try:
            push_ok, push_detail = push_new_signals(push_signals, lang=lang)
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
            "datenquelle": "CoinGecko Live-Marktdaten",
            "live": True,
            "letzte_aktualisierung_utc": datetime.now(timezone.utc).isoformat(),
            "push": {
                "ok": push_ok,
                "detail": push_detail
            }
        }

    except Exception as e:
        return {
            "signale": [],
            "sprache": lang,
            "mode": mode,
            "modus": current_mode["label"],
            "min_confidence": min_confidence,
            "anzahl_signale": 0,
            "datenquelle": "CoinGecko Live-Marktdaten",
            "live": False,
            "error": f"Live-Daten konnten nicht geladen werden: {str(e)}",
            "push": {
                "ok": False,
                "detail": "Kein Push, weil Live-Daten nicht geladen wurden"
            }
        }


def fetch_live_market_data() -> List[Dict]:
    coin_ids = ",".join([coin["id"] for coin in COINS])

    headers = {
        "Accept": "application/json"
    }

    # Optional:
    # Falls du später einen CoinGecko API-Key in Render hinterlegst,
    # wird er automatisch genutzt.
    if COINGECKO_API_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY

    params = {
        "vs_currency": "eur",
        "ids": coin_ids,
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h"
    }

    response = requests.get(
        COINGECKO_URL,
        headers=headers,
        params=params,
        timeout=10
    )

    if response.status_code != 200:
        raise Exception(f"CoinGecko HTTP {response.status_code}: {response.text}")

    data = response.json()

    if not isinstance(data, list):
        raise Exception("Unerwartete CoinGecko-Antwort")

    return data


def build_live_signals(market_data: List[Dict]) -> List[Dict]:
    coin_lookup = {
        coin["id"]: coin for coin in COINS
    }

    signals: List[Dict] = []

    for item in market_data:
        coin_id = item.get("id")

        if coin_id not in coin_lookup:
            continue

        coin_config = coin_lookup[coin_id]

        asset = coin_config["asset"]
        boerse = coin_config["börse"]

        price = safe_float(item.get("current_price"))
        change_24h = safe_float(item.get("price_change_percentage_24h"))
        volume = safe_float(item.get("total_volume"))
        market_cap = safe_float(item.get("market_cap"))

        action = calculate_action(change_24h)
        confidence = calculate_confidence(change_24h, market_cap, volume)
        risk = calculate_risk(confidence)
        amount = calculate_suggested_amount(action, confidence)

        reason = build_reason(
            price=price,
            change_24h=change_24h,
            volume=volume,
            market_cap=market_cap
        )

        signals.append(
            {
                "asset": asset,
                "börse": boerse,
                "action": action,
                "confidence_score": confidence,
                "risk": risk,
                "suggested_amount_eur": amount,
                "reason": reason,
                "live_price_eur": round(price, 6) if price is not None else None,
                "change_24h_percent": round(change_24h, 2) if change_24h is not None else None
            }
        )

    sorted_signals = sorted(
        signals,
        key=lambda s: (
            action_priority(s.get("action")),
            -int(s.get("confidence_score", 0))
        )
    )

    return sorted_signals


def calculate_action(change_24h: Optional[float]) -> str:
    if change_24h is None:
        return "HOLD"

    if change_24h >= 3.0:
        return "BUY"

    if change_24h <= -4.0:
        return "SELL"

    return "HOLD"


def calculate_confidence(
    change_24h: Optional[float],
    market_cap: Optional[float],
    volume: Optional[float]
) -> int:
    if change_24h is None:
        return 70

    abs_change = abs(change_24h)

    if abs_change >= 5.0:
        return 90

    if abs_change >= 3.0:
        return 85

    if abs_change >= 1.5:
        return 80

    if market_cap is not None and market_cap > 10_000_000_000:
        return 90

    if volume is not None and volume > 500_000_000:
        return 80

    return 70


def calculate_risk(confidence: int) -> str:
    if confidence >= 90:
        return "konservativ"

    if confidence >= 80:
        return "normal"

    return "aggressiv"


def calculate_suggested_amount(action: str, confidence: int) -> Optional[float]:
    if action != "BUY":
        return None

    if confidence >= 90:
        return 5.00

    if confidence >= 80:
        return 3.50

    return 2.00


def build_reason(
    price: Optional[float],
    change_24h: Optional[float],
    volume: Optional[float],
    market_cap: Optional[float]
) -> str:
    price_text = format_eur(price)
    change_text = format_percent(change_24h)
    volume_text = format_eur(volume)
    market_cap_text = format_eur(market_cap)

    return (
        f"Live-Daten: Preis {price_text}, "
        f"24h-Veränderung {change_text}, "
        f"Volumen {volume_text}, "
        f"Market Cap {market_cap_text}."
    )


def safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def format_eur(value: Optional[float]) -> str:
    if value is None:
        return "-"

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} Mrd. €"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f} Mio. €"

    if value >= 1:
        return f"{value:.2f} €"

    return f"{value:.6f} €"


def format_percent(value: Optional[float]) -> str:
    if value is None:
        return "-"

    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f} %"


def action_priority(action: str) -> int:
    if action == "BUY":
        return 0

    if action == "SELL":
        return 1

    if action == "HOLD":
        return 2

    return 3
