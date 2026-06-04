from typing import Dict, List, Optional
from datetime import datetime, timezone
import time
import requests

from .push_manager import push_new_signals


COINPAPRIKA_URL = "https://api.coinpaprika.com/v1/tickers"

CACHE_SECONDS = 300

_CACHE_DATA: Optional[List[Dict]] = None
_CACHE_TIME: float = 0.0


COINS = [
    {
        "symbol": "BTC",
        "asset": "BTC",
        "börse": "Coinbase",
    },
    {
        "symbol": "LTC",
        "asset": "LTC",
        "börse": "Coinbase",
    },
    {
        "symbol": "IOTA",
        "asset": "IOTA",
        "börse": "Bitunix",
    },
    {
        "symbol": "ETH",
        "asset": "ETH",
        "börse": "Coinbase",
    },
    {
        "symbol": "SOL",
        "asset": "SOL",
        "börse": "Coinbase",
    },
    {
        "symbol": "XRP",
        "asset": "XRP",
        "börse": "Bitunix",
    },
    {
        "symbol": "ADA",
        "asset": "ADA",
        "börse": "Bitunix",
    },
]


def generate_signals(lang: str = "de", mode: str = "konservativ") -> Dict:
    mode_settings = {
        "konservativ": {
            "label": "Konservativ",
            "min_confidence": 90,
        },
        "normal": {
            "label": "Normal",
            "min_confidence": 80,
        },
        "aggressiv": {
            "label": "Aggressiv",
            "min_confidence": 70,
        },
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
            "datenquelle": "CoinPaprika Live-Marktdaten",
            "live": True,
            "cache_seconds": CACHE_SECONDS,
            "letzte_aktualisierung_utc": datetime.now(timezone.utc).isoformat(),
            "push": {
                "ok": push_ok,
                "detail": push_detail,
            },
        }

    except Exception as e:
        return {
            "signale": [],
            "sprache": lang,
            "mode": mode,
            "modus": current_mode["label"],
            "min_confidence": min_confidence,
            "anzahl_signale": 0,
            "datenquelle": "CoinPaprika Live-Marktdaten",
            "live": False,
            "error": f"Live-Daten konnten nicht geladen werden: {str(e)}",
            "push": {
                "ok": False,
                "detail": "Kein Push, weil Live-Daten nicht geladen wurden",
            },
        }


def fetch_live_market_data() -> List[Dict]:
    global _CACHE_DATA
    global _CACHE_TIME

    now = time.time()

    if _CACHE_DATA is not None and now - _CACHE_TIME < CACHE_SECONDS:
        return _CACHE_DATA

    response = requests.get(
        COINPAPRIKA_URL,
        params={"quotes": "EUR"},
        timeout=15,
        headers={
            "Accept": "application/json",
            "User-Agent": "SpeedyCoinZales/1.0",
        },
    )

    if response.status_code != 200:
        if _CACHE_DATA is not None:
            return _CACHE_DATA

        raise Exception(f"CoinPaprika HTTP {response.status_code}: {response.text}")

    data = response.json()

    if not isinstance(data, list):
        raise Exception("Unerwartete CoinPaprika-Antwort")

    _CACHE_DATA = data
    _CACHE_TIME = now

    return data


def build_live_signals(market_data: List[Dict]) -> List[Dict]:
    wanted_symbols = {coin["symbol"]: coin for coin in COINS}

    best_by_symbol: Dict[str, Dict] = {}

    for item in market_data:
        symbol = str(item.get("symbol", "")).upper()

        if symbol not in wanted_symbols:
            continue

        rank = item.get("rank")

        if symbol not in best_by_symbol:
            best_by_symbol[symbol] = item
            continue

        old_rank = best_by_symbol[symbol].get("rank")

        if safe_int(rank, 999999) < safe_int(old_rank, 999999):
            best_by_symbol[symbol] = item

    signals: List[Dict] = []

    for coin in COINS:
        symbol = coin["symbol"]
        item = best_by_symbol.get(symbol)

        if item is None:
            continue

        quotes = item.get("quotes", {})
        eur = quotes.get("EUR") or quotes.get("USD") or {}

        price = safe_float(eur.get("price"))
        change_24h = safe_float(eur.get("percent_change_24h"))
        change_1h = safe_float(eur.get("percent_change_1h"))
        change_7d = safe_float(eur.get("percent_change_7d"))
        volume = safe_float(eur.get("volume_24h"))
        market_cap = safe_float(eur.get("market_cap"))

        action = calculate_action(change_24h, change_1h, change_7d)
        confidence = calculate_confidence(change_24h, change_1h, change_7d, market_cap, volume)
        risk = calculate_risk(confidence)
        amount = calculate_suggested_amount(action, confidence)

        reason = build_reason(
            price=price,
            change_1h=change_1h,
            change_24h=change_24h,
            change_7d=change_7d,
            volume=volume,
            market_cap=market_cap,
        )

        signals.append(
            {
                "asset": coin["asset"],
                "börse": coin["börse"],
                "action": action,
                "confidence_score": confidence,
                "risk": risk,
                "suggested_amount_eur": amount,
                "reason": reason,
                "live_price_eur": round(price, 6) if price is not None else None,
                "change_1h_percent": round(change_1h, 2) if change_1h is not None else None,
                "change_24h_percent": round(change_24h, 2) if change_24h is not None else None,
                "change_7d_percent": round(change_7d, 2) if change_7d is not None else None,
            }
        )

    sorted_signals = sorted(
        signals,
        key=lambda s: (
            action_priority(s.get("action")),
            -int(s.get("confidence_score", 0)),
        ),
    )

    return sorted_signals


def calculate_action(
    change_24h: Optional[float],
    change_1h: Optional[float],
    change_7d: Optional[float],
) -> str:
    if change_24h is None:
        return "HOLD"

    short_term_strong = change_1h is not None and change_1h >= 0.8
    day_positive = change_24h >= 2.5
    week_not_bad = change_7d is None or change_7d > -8.0

    if day_positive and week_not_bad:
        return "BUY"

    if short_term_strong and change_24h >= 1.0 and week_not_bad:
        return "BUY"

    if change_24h <= -4.0:
        return "SELL"

    return "HOLD"


def calculate_confidence(
    change_24h: Optional[float],
    change_1h: Optional[float],
    change_7d: Optional[float],
    market_cap: Optional[float],
    volume: Optional[float],
) -> int:
    score = 70

    if change_24h is not None:
        abs_change = abs(change_24h)

        if abs_change >= 5.0:
            score += 15
        elif abs_change >= 3.0:
            score += 10
        elif abs_change >= 1.5:
            score += 5

    if change_1h is not None and abs(change_1h) >= 0.8:
        score += 5

    if change_7d is not None and change_7d > 0:
        score += 5

    if market_cap is not None and market_cap > 10_000_000_000:
        score += 10

    if volume is not None and volume > 500_000_000:
        score += 5

    if score > 95:
        score = 95

    if score < 70:
        score = 70

    return int(score)


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
    change_1h: Optional[float],
    change_24h: Optional[float],
    change_7d: Optional[float],
    volume: Optional[float],
    market_cap: Optional[float],
) -> str:
    return (
        f"Live-Daten: Preis {format_eur(price)}, "
        f"1h {format_percent(change_1h)}, "
        f"24h {format_percent(change_24h)}, "
        f"7d {format_percent(change_7d)}, "
        f"Volumen {format_eur(volume)}, "
        f"Market Cap {format_eur(market_cap)}."
    )


def safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def safe_int(value, default: int) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


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
