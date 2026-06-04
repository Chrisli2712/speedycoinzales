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

        highest_crash_risk = 0

        if signals:
            highest_crash_risk = max(
                int(signal.get("crash_risk_score", 0))
                for signal in signals
            )

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
            "highest_crash_risk_score": highest_crash_risk,
            "market_status": calculate_overall_market_status(highest_crash_risk),
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

        crash_risk_score = calculate_crash_risk(
            change_1h=change_1h,
            change_24h=change_24h,
            change_7d=change_7d,
            volume=volume,
            market_cap=market_cap,
        )

        market_warning = calculate_market_warning(crash_risk_score)

        action = calculate_action(
            change_24h=change_24h,
            change_1h=change_1h,
            change_7d=change_7d,
            crash_risk_score=crash_risk_score,
        )

        confidence = calculate_confidence(
            action=action,
            crash_risk_score=crash_risk_score,
            change_24h=change_24h,
            change_1h=change_1h,
            change_7d=change_7d,
            market_cap=market_cap,
            volume=volume,
        )

        risk = calculate_risk(confidence)
        amount = calculate_suggested_amount(action, confidence, crash_risk_score)

        reason = build_reason(
            action=action,
            price=price,
            change_1h=change_1h,
            change_24h=change_24h,
            change_7d=change_7d,
            volume=volume,
            market_cap=market_cap,
            crash_risk_score=crash_risk_score,
            market_warning=market_warning,
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
                "crash_risk_score": crash_risk_score,
                "market_warning": market_warning,
            }
        )

    sorted_signals = sorted(
        signals,
        key=lambda s: (
            action_priority(s.get("action")),
            -int(s.get("crash_risk_score", 0)),
            -int(s.get("confidence_score", 0)),
        ),
    )

    return sorted_signals


def calculate_crash_risk(
    change_1h: Optional[float],
    change_24h: Optional[float],
    change_7d: Optional[float],
    volume: Optional[float],
    market_cap: Optional[float],
) -> int:
    score = 10

    if change_1h is not None:
        if change_1h <= -2.0:
            score += 25
        elif change_1h <= -1.0:
            score += 15
        elif change_1h <= -0.5:
            score += 8

    if change_24h is not None:
        if change_24h <= -8.0:
            score += 40
        elif change_24h <= -5.0:
            score += 30
        elif change_24h <= -3.0:
            score += 20
        elif change_24h <= -1.5:
            score += 10

        if change_24h >= 3.0:
            score -= 10
        elif change_24h >= 1.0:
            score -= 5

    if change_7d is not None:
        if change_7d <= -25.0:
            score += 30
        elif change_7d <= -15.0:
            score += 20
        elif change_7d <= -8.0:
            score += 12

        if change_7d >= 10.0:
            score -= 8
        elif change_7d >= 3.0:
            score -= 4

    volume_ratio = None

    if volume is not None and market_cap is not None and market_cap > 0:
        volume_ratio = volume / market_cap

    if volume_ratio is not None:
        if volume_ratio >= 0.35:
            score += 20
        elif volume_ratio >= 0.20:
            score += 12
        elif volume_ratio >= 0.10:
            score += 6

    if market_cap is not None:
        if market_cap < 1_000_000_000:
            score += 12
        elif market_cap < 5_000_000_000:
            score += 6

    if score < 0:
        score = 0

    if score > 100:
        score = 100

    return int(score)


def calculate_market_warning(crash_risk_score: int) -> str:
    if crash_risk_score >= 85:
        return "extrem"

    if crash_risk_score >= 70:
        return "hoch"

    if crash_risk_score >= 50:
        return "mittel"

    return "niedrig"


def calculate_overall_market_status(highest_crash_risk_score: int) -> str:
    if highest_crash_risk_score >= 85:
        return "EXTREME WARNUNG"

    if highest_crash_risk_score >= 70:
        return "HOHES RISIKO"

    if highest_crash_risk_score >= 50:
        return "ERHÖHTE VORSICHT"

    return "MARKT RUHIG"


def calculate_action(
    change_24h: Optional[float],
    change_1h: Optional[float],
    change_7d: Optional[float],
    crash_risk_score: int,
) -> str:
    if crash_risk_score >= 75:
        return "SELL"

    if crash_risk_score >= 60 and change_24h is not None and change_24h < 0:
        return "SELL"

    if change_24h is None:
        return "HOLD"

    short_term_positive = change_1h is not None and change_1h >= 0.8
    day_positive = change_24h >= 2.5
    week_not_bad = change_7d is None or change_7d > -8.0
    crash_risk_ok = crash_risk_score < 50

    if day_positive and week_not_bad and crash_risk_ok:
        return "BUY"

    if short_term_positive and change_24h >= 1.0 and week_not_bad and crash_risk_ok:
        return "BUY"

    return "HOLD"


def calculate_confidence(
    action: str,
    crash_risk_score: int,
    change_24h: Optional[float],
    change_1h: Optional[float],
    change_7d: Optional[float],
    market_cap: Optional[float],
    volume: Optional[float],
) -> int:
    if action == "SELL":
        if crash_risk_score >= 85:
            return 95

        if crash_risk_score >= 75:
            return 92

        if crash_risk_score >= 60:
            return 88

        return 80

    if action == "BUY":
        score = 75

        if change_24h is not None:
            if change_24h >= 6.0:
                score += 12
            elif change_24h >= 3.0:
                score += 9
            elif change_24h >= 1.5:
                score += 5

        if change_1h is not None and change_1h >= 0.8:
            score += 5

        if change_7d is not None and change_7d > 0:
            score += 5

        if market_cap is not None and market_cap > 10_000_000_000:
            score += 5

        if volume is not None and volume > 500_000_000:
            score += 5

        if crash_risk_score < 30:
            score += 5

        if score > 95:
            score = 95

        return int(score)

    score = 70

    if market_cap is not None:
        if market_cap > 100_000_000_000:
            score += 15
        elif market_cap > 10_000_000_000:
            score += 10
        elif market_cap > 1_000_000_000:
            score += 5

    if change_24h is not None and abs(change_24h) < 2.0:
        score += 5

    if change_7d is not None and abs(change_7d) < 10.0:
        score += 5

    if volume is not None and volume > 500_000_000:
        score += 5

    if crash_risk_score >= 50:
        score -= 10

    if score > 90:
        score = 90

    if score < 70:
        score = 70

    return int(score)


def calculate_risk(confidence: int) -> str:
    if confidence >= 90:
        return "konservativ"

    if confidence >= 80:
        return "normal"

    return "aggressiv"


def calculate_suggested_amount(
    action: str,
    confidence: int,
    crash_risk_score: int,
) -> Optional[float]:
    if action != "BUY":
        return None

    if crash_risk_score >= 50:
        return None

    if confidence >= 90:
        return 5.00

    if confidence >= 80:
        return 3.50

    return 2.00


def build_reason(
    action: str,
    price: Optional[float],
    change_1h: Optional[float],
    change_24h: Optional[float],
    change_7d: Optional[float],
    volume: Optional[float],
    market_cap: Optional[float],
    crash_risk_score: int,
    market_warning: str,
) -> str:
    if action == "SELL":
        signal_text = "Verkaufs-/Warnsignal wegen erhöhtem Crash-Risiko."
    elif action == "BUY":
        signal_text = "Kaufsignal bei positivem Momentum und niedrigem Crash-Risiko."
    else:
        signal_text = "Halten/Beobachten, kein starkes Kauf- oder Verkaufssignal."

    return (
        f"{signal_text} "
        f"Crash-Risiko {crash_risk_score}/100 ({market_warning}). "
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
