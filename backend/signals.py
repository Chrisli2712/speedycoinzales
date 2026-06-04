from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import time
import re
import requests

from .push_manager import push_new_signals


COINPAPRIKA_URL = "https://api.coinpaprika.com/v1/tickers"
GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

MARKET_CACHE_SECONDS = 300
NEWS_CACHE_SECONDS = 600

_MARKET_CACHE_DATA: Optional[List[Dict]] = None
_MARKET_CACHE_TIME: float = 0.0

_NEWS_CACHE_DATA: Optional[List[Dict]] = None
_NEWS_CACHE_TIME: float = 0.0


COINS = [
    {
        "symbol": "BTC",
        "asset": "BTC",
        "name": "Bitcoin",
        "börse": "Coinbase",
        "news_terms": ["bitcoin", "btc"],
    },
    {
        "symbol": "LTC",
        "asset": "LTC",
        "name": "Litecoin",
        "börse": "Coinbase",
        "news_terms": ["litecoin", "ltc"],
    },
    {
        "symbol": "IOTA",
        "asset": "IOTA",
        "name": "IOTA",
        "börse": "Bitunix",
        "news_terms": ["iota"],
    },
    {
        "symbol": "ETH",
        "asset": "ETH",
        "name": "Ethereum",
        "börse": "Coinbase",
        "news_terms": ["ethereum", "ether", "eth"],
    },
    {
        "symbol": "SOL",
        "asset": "SOL",
        "name": "Solana",
        "börse": "Coinbase",
        "news_terms": ["solana", "sol"],
    },
    {
        "symbol": "XRP",
        "asset": "XRP",
        "name": "XRP",
        "börse": "Bitunix",
        "news_terms": ["xrp", "ripple"],
    },
    {
        "symbol": "ADA",
        "asset": "ADA",
        "name": "Cardano",
        "börse": "Bitunix",
        "news_terms": ["cardano", "ada"],
    },
]


NEGATIVE_NEWS_KEYWORDS = [
    "crash",
    "plunge",
    "collapse",
    "selloff",
    "sell-off",
    "dump",
    "falls",
    "fell",
    "drops",
    "dropped",
    "tumbles",
    "slumps",
    "bleed",
    "bleeds",
    "liquidation",
    "liquidations",
    "bankruptcy",
    "insolvency",
    "lawsuit",
    "sues",
    "sued",
    "probe",
    "investigation",
    "fraud",
    "scam",
    "hack",
    "hacked",
    "exploit",
    "breach",
    "outage",
    "ban",
    "banned",
    "delist",
    "delisting",
    "crackdown",
    "regulation",
    "regulatory",
    "sec",
    "cftc",
    "sanctions",
    "war",
    "missile",
    "attack",
    "tariff",
    "rate hike",
    "interest rates",
    "fed warning",
    "recession",
]

EXTREME_NEWS_KEYWORDS = [
    "exchange collapse",
    "bank run",
    "major hack",
    "massive hack",
    "sec lawsuit",
    "trading halted",
    "withdrawals halted",
    "bankruptcy filing",
    "criminal charges",
    "sanctions announced",
    "war escalates",
    "market crash",
    "crypto crash",
    "bitcoin crash",
]

POSITIVE_NEWS_KEYWORDS = [
    "rally",
    "rebounds",
    "rebound",
    "surge",
    "surges",
    "jumps",
    "gains",
    "approval",
    "approved",
    "etf approval",
    "partnership",
    "adoption",
    "inflows",
    "record inflows",
    "launches",
    "integrates",
    "upgrade",
]

CRYPTO_MARKET_TERMS = [
    "crypto",
    "cryptocurrency",
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "solana",
    "sol",
    "cardano",
    "ada",
    "xrp",
    "ripple",
    "litecoin",
    "ltc",
    "iota",
    "stablecoin",
    "exchange",
    "binance",
    "coinbase",
    "etf",
    "token",
    "blockchain",
]

MACRO_MARKET_TERMS = [
    "fed",
    "federal reserve",
    "sec",
    "cftc",
    "blackrock",
    "rates",
    "interest rates",
    "inflation",
    "recession",
    "sanctions",
    "war",
    "tariff",
]

INFLUENCER_GROUPS = {
    "Trump": ["donald trump", "trump"],
    "Musk": ["elon musk", "musk"],
    "Putin": ["vladimir putin", "putin"],
    "Fed": ["federal reserve", "fed"],
    "SEC": ["sec"],
    "BlackRock": ["blackrock"],
    "Binance": ["binance"],
    "Coinbase": ["coinbase"],
    "Saylor": ["michael saylor", "saylor", "microstrategy"],
}


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
        news_articles, news_error = fetch_news_articles_safe()

        all_signals = build_live_signals(
            market_data=market_data,
            news_articles=news_articles,
        )

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
        highest_news_risk = 0
        highest_combined_risk = 0

        if signals:
            highest_crash_risk = max(
                int(signal.get("crash_risk_score", 0))
                for signal in signals
            )
            highest_news_risk = max(
                int(signal.get("news_risk_score", 0))
                for signal in signals
            )
            highest_combined_risk = max(
                int(signal.get("combined_risk_score", 0))
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
            "datenquelle_news": "GDELT News",
            "live": True,
            "news_live": news_error is None,
            "news_error": news_error,
            "market_cache_seconds": MARKET_CACHE_SECONDS,
            "news_cache_seconds": NEWS_CACHE_SECONDS,
            "highest_crash_risk_score": highest_crash_risk,
            "highest_news_risk_score": highest_news_risk,
            "highest_combined_risk_score": highest_combined_risk,
            "market_status": calculate_overall_market_status(highest_combined_risk),
            "news_articles_checked": len(news_articles),
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
            "datenquelle_news": "GDELT News",
            "live": False,
            "news_live": False,
            "error": f"Live-Daten konnten nicht geladen werden: {str(e)}",
            "push": {
                "ok": False,
                "detail": "Kein Push, weil Live-Daten nicht geladen wurden",
            },
        }


def fetch_live_market_data() -> List[Dict]:
    global _MARKET_CACHE_DATA
    global _MARKET_CACHE_TIME

    now = time.time()

    if _MARKET_CACHE_DATA is not None and now - _MARKET_CACHE_TIME < MARKET_CACHE_SECONDS:
        return _MARKET_CACHE_DATA

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
        if _MARKET_CACHE_DATA is not None:
            return _MARKET_CACHE_DATA

        raise Exception(f"CoinPaprika HTTP {response.status_code}: {response.text}")

    data = response.json()

    if not isinstance(data, list):
        raise Exception("Unerwartete CoinPaprika-Antwort")

    _MARKET_CACHE_DATA = data
    _MARKET_CACHE_TIME = now

    return data


def fetch_news_articles_safe() -> Tuple[List[Dict], Optional[str]]:
    try:
        return fetch_news_articles(), None
    except Exception as e:
        if _NEWS_CACHE_DATA is not None:
            return _NEWS_CACHE_DATA, f"News-Fehler, Cache genutzt: {str(e)}"

        return [], f"News konnten nicht geladen werden: {str(e)}"


def fetch_news_articles() -> List[Dict]:
    global _NEWS_CACHE_DATA
    global _NEWS_CACHE_TIME

    now = time.time()

    if _NEWS_CACHE_DATA is not None and now - _NEWS_CACHE_TIME < NEWS_CACHE_SECONDS:
        return _NEWS_CACHE_DATA

    query = (
        '(crypto OR cryptocurrency OR bitcoin OR ethereum OR solana OR cardano OR xrp '
        'OR litecoin OR iota OR binance OR coinbase OR sec OR etf OR fed OR blackrock '
        'OR trump OR musk OR putin OR sanctions OR war OR hack OR lawsuit OR regulation)'
    )

    response = requests.get(
        GDELT_DOC_URL,
        params={
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": 75,
            "timespan": "12h",
            "sort": "HybridRel",
        },
        timeout=15,
        headers={
            "Accept": "application/json",
            "User-Agent": "SpeedyCoinZales/1.0",
        },
    )

    if response.status_code != 200:
        if _NEWS_CACHE_DATA is not None:
            return _NEWS_CACHE_DATA

        raise Exception(f"GDELT HTTP {response.status_code}: {response.text}")

    data = response.json()
    articles = data.get("articles", [])

    if not isinstance(articles, list):
        articles = []

    cleaned_articles: List[Dict] = []

    for article in articles:
        title = str(article.get("title", "")).strip()
        url = str(article.get("url", "")).strip()
        domain = str(article.get("domain", "")).strip()
        seendate = str(article.get("seendate", "")).strip()

        if not title:
            continue

        cleaned_articles.append(
            {
                "title": title,
                "url": url,
                "domain": domain,
                "seendate": seendate,
            }
        )

    _NEWS_CACHE_DATA = cleaned_articles
    _NEWS_CACHE_TIME = now

    return cleaned_articles


def build_live_signals(
    market_data: List[Dict],
    news_articles: List[Dict],
) -> List[Dict]:
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

        (
            news_risk_score,
            news_warning,
            news_summary,
            news_hits,
            influencer_mentions,
            coin_news_risk_score,
            global_news_risk_score,
            influencer_risk_score,
        ) = calculate_news_risk(
            coin=coin,
            news_articles=news_articles,
        )

        combined_risk_score = calculate_combined_risk(
            crash_risk_score=crash_risk_score,
            news_risk_score=news_risk_score,
        )

        market_warning = calculate_market_warning(crash_risk_score)
        combined_warning = calculate_market_warning(combined_risk_score)

        action = calculate_action(
            change_24h=change_24h,
            change_1h=change_1h,
            change_7d=change_7d,
            crash_risk_score=crash_risk_score,
            news_risk_score=news_risk_score,
            combined_risk_score=combined_risk_score,
        )

        confidence = calculate_confidence(
            action=action,
            crash_risk_score=crash_risk_score,
            news_risk_score=news_risk_score,
            combined_risk_score=combined_risk_score,
            change_24h=change_24h,
            change_1h=change_1h,
            change_7d=change_7d,
            market_cap=market_cap,
            volume=volume,
        )

        risk = calculate_risk(confidence)
        amount = calculate_suggested_amount(action, confidence, combined_risk_score)

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
            news_risk_score=news_risk_score,
            news_warning=news_warning,
            combined_risk_score=combined_risk_score,
            combined_warning=combined_warning,
            news_summary=news_summary,
            influencer_mentions=influencer_mentions,
            coin_news_risk_score=coin_news_risk_score,
            global_news_risk_score=global_news_risk_score,
            influencer_risk_score=influencer_risk_score,
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
                "coin_news_risk_score": coin_news_risk_score,
                "global_news_risk_score": global_news_risk_score,
                "influencer_risk_score": influencer_risk_score,
                "news_risk_score": news_risk_score,
                "news_warning": news_warning,
                "news_hits": news_hits,
                "news_summary": news_summary,
                "influencer_mentions": influencer_mentions,
                "combined_risk_score": combined_risk_score,
                "combined_warning": combined_warning,
            }
        )

    sorted_signals = sorted(
        signals,
        key=lambda s: (
            action_priority(s.get("action")),
            -int(s.get("combined_risk_score", 0)),
            -int(s.get("crash_risk_score", 0)),
            -int(s.get("news_risk_score", 0)),
            -int(s.get("confidence_score", 0)),
        ),
    )

    return sorted_signals


def calculate_news_risk(
    coin: Dict,
    news_articles: List[Dict],
) -> Tuple[int, str, List[str], int, List[str], int, int, int]:
    coin_news_score = 0
    global_news_score = 0
    influencer_score = 0

    matched_headlines: List[str] = []
    influencer_mentions: List[str] = []
    news_hits = 0

    coin_terms = [term.lower() for term in coin.get("news_terms", [])]
    asset = str(coin.get("asset", "")).upper()

    for article in news_articles:
        title = str(article.get("title", "")).strip()
        title_lower = title.lower()

        coin_specific = text_has_any_term(title_lower, coin_terms)
        crypto_market_relevant = text_has_any_term(title_lower, CRYPTO_MARKET_TERMS)
        macro_relevant = text_has_any_term(title_lower, MACRO_MARKET_TERMS)

        if not coin_specific and not crypto_market_relevant and not macro_relevant:
            continue

        base_risk = calculate_article_risk(title_lower)
        article_influencers = detect_influencers(title_lower)

        # Politische / Makro-News zählen nur stark, wenn sie auch Markt-/Krypto-Bezug haben.
        if macro_relevant and not crypto_market_relevant and not coin_specific:
            if base_risk < 25:
                continue
            base_risk = int(base_risk * 0.35)

        if coin_specific:
            article_score = 12 + base_risk

            if article_influencers:
                article_score += 6

            coin_news_score += article_score
            news_hits += 1

            if len(matched_headlines) < 3:
                matched_headlines.append(f"Coin-News: {title}")

        elif crypto_market_relevant:
            article_score = 4 + int(base_risk * 0.65)

            if article_influencers:
                article_score += 4

            global_news_score += article_score
            news_hits += 1

            if len(matched_headlines) < 3:
                matched_headlines.append(f"Markt-News: {title}")

        for influencer in article_influencers:
            if influencer not in influencer_mentions:
                influencer_mentions.append(influencer)

            if coin_specific:
                influencer_score += 10
            elif crypto_market_relevant:
                influencer_score += 6
            else:
                influencer_score += 3

    coin_news_score = clamp_score(coin_news_score)
    global_news_score = clamp_score(global_news_score)
    influencer_score = clamp_score(influencer_score)

    effective_global_news_score = apply_global_news_weight(
        asset=asset,
        coin_news_score=coin_news_score,
        global_news_score=global_news_score,
    )

    news_risk_score = int(
        coin_news_score * 0.70
        + effective_global_news_score * 0.35
        + influencer_score * 0.20
    )

    # Wenn es keine coin-spezifischen Treffer gibt, darf allgemeine Markt-News
    # Altcoins nicht automatisch auf "extrem" ziehen.
    if coin_news_score == 0:
        if asset in ["BTC", "ETH"]:
            news_risk_score = min(news_risk_score, 75)
        else:
            news_risk_score = min(news_risk_score, 60)

    news_risk_score = clamp_score(news_risk_score)
    warning = calculate_news_warning(news_risk_score)

    if not matched_headlines:
        matched_headlines = ["Keine kritischen News-Treffer im aktuellen Zeitfenster."]

    return (
        news_risk_score,
        warning,
        matched_headlines,
        news_hits,
        influencer_mentions,
        coin_news_score,
        global_news_score,
        influencer_score,
    )


def calculate_article_risk(title_lower: str) -> int:
    score = 0

    for keyword in EXTREME_NEWS_KEYWORDS:
        if text_has_term(title_lower, keyword):
            score += 25

    for keyword in NEGATIVE_NEWS_KEYWORDS:
        if text_has_term(title_lower, keyword):
            score += 10

    for keyword in POSITIVE_NEWS_KEYWORDS:
        if text_has_term(title_lower, keyword):
            score -= 6

    if score < 0:
        score = 0

    if score > 70:
        score = 70

    return int(score)


def apply_global_news_weight(
    asset: str,
    coin_news_score: int,
    global_news_score: int,
) -> int:
    if asset in ["BTC", "ETH"]:
        weighted = int(global_news_score * 0.85)
    elif asset in ["SOL", "XRP"]:
        weighted = int(global_news_score * 0.60)
    else:
        weighted = int(global_news_score * 0.45)

    # Ohne coin-spezifische News wird globale News-Wirkung begrenzt.
    if coin_news_score == 0:
        if asset in ["BTC", "ETH"]:
            weighted = min(weighted, 65)
        else:
            weighted = min(weighted, 45)

    return clamp_score(weighted)


def detect_influencers(title_lower: str) -> List[str]:
    found: List[str] = []

    for label, aliases in INFLUENCER_GROUPS.items():
        for alias in aliases:
            if text_has_term(title_lower, alias):
                if label not in found:
                    found.append(label)
                break

    return found


def text_has_any_term(text: str, terms: List[str]) -> bool:
    for term in terms:
        if text_has_term(text, term):
            return True

    return False


def text_has_term(text: str, term: str) -> bool:
    term = term.lower().strip()

    if not term:
        return False

    if " " in term:
        return term in text

    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def calculate_news_warning(news_risk_score: int) -> str:
    if news_risk_score >= 85:
        return "extrem"

    if news_risk_score >= 70:
        return "hoch"

    if news_risk_score >= 45:
        return "mittel"

    return "niedrig"


def calculate_combined_risk(
    crash_risk_score: int,
    news_risk_score: int,
) -> int:
    combined = int((crash_risk_score * 0.70) + (news_risk_score * 0.30))

    if crash_risk_score >= 70 and news_risk_score >= 70:
        combined += 12
    elif crash_risk_score >= 50 and news_risk_score >= 70:
        combined += 8
    elif crash_risk_score >= 70 and news_risk_score >= 45:
        combined += 6

    return clamp_score(combined)


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

    return clamp_score(score)


def calculate_market_warning(risk_score: int) -> str:
    if risk_score >= 85:
        return "extrem"

    if risk_score >= 70:
        return "hoch"

    if risk_score >= 50:
        return "mittel"

    return "niedrig"


def calculate_overall_market_status(highest_risk_score: int) -> str:
    if highest_risk_score >= 85:
        return "EXTREME WARNUNG"

    if highest_risk_score >= 70:
        return "HOHES RISIKO"

    if highest_risk_score >= 50:
        return "ERHÖHTE VORSICHT"

    return "MARKT RUHIG"


def calculate_action(
    change_24h: Optional[float],
    change_1h: Optional[float],
    change_7d: Optional[float],
    crash_risk_score: int,
    news_risk_score: int,
    combined_risk_score: int,
) -> str:
    if combined_risk_score >= 82:
        return "SELL"

    if crash_risk_score >= 78:
        return "SELL"

    if news_risk_score >= 85 and change_24h is not None and change_24h <= 1.0:
        return "SELL"

    if combined_risk_score >= 68 and change_24h is not None and change_24h < 0:
        return "SELL"

    if change_24h is None:
        return "HOLD"

    short_term_positive = change_1h is not None and change_1h >= 0.8
    day_positive = change_24h >= 2.5
    week_not_bad = change_7d is None or change_7d > -8.0
    risk_ok = combined_risk_score < 50

    if day_positive and week_not_bad and risk_ok:
        return "BUY"

    if short_term_positive and change_24h >= 1.0 and week_not_bad and risk_ok:
        return "BUY"

    return "HOLD"


def calculate_confidence(
    action: str,
    crash_risk_score: int,
    news_risk_score: int,
    combined_risk_score: int,
    change_24h: Optional[float],
    change_1h: Optional[float],
    change_7d: Optional[float],
    market_cap: Optional[float],
    volume: Optional[float],
) -> int:
    if action == "SELL":
        if combined_risk_score >= 90:
            return 95

        if combined_risk_score >= 82:
            return 92

        if combined_risk_score >= 68:
            return 88

        if crash_risk_score >= 78 or news_risk_score >= 85:
            return 90

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

        if combined_risk_score < 30:
            score += 5

        if news_risk_score >= 45:
            score -= 10

        if score > 95:
            score = 95

        if score < 70:
            score = 70

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

    if combined_risk_score >= 50:
        score -= 10

    if news_risk_score >= 70:
        score -= 5

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
    combined_risk_score: int,
) -> Optional[float]:
    if action != "BUY":
        return None

    if combined_risk_score >= 50:
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
    news_risk_score: int,
    news_warning: str,
    combined_risk_score: int,
    combined_warning: str,
    news_summary: List[str],
    influencer_mentions: List[str],
    coin_news_risk_score: int,
    global_news_risk_score: int,
    influencer_risk_score: int,
) -> str:
    if action == "SELL":
        signal_text = "Verkaufs-/Warnsignal wegen erhöhtem Gesamt-Risiko."
    elif action == "BUY":
        signal_text = "Kaufsignal bei positivem Momentum und niedrigem Gesamt-Risiko."
    else:
        signal_text = "Halten/Beobachten, kein starkes Kauf- oder Verkaufssignal."

    if influencer_mentions:
        influencer_text = " Einflussfaktoren: " + ", ".join(influencer_mentions[:5]) + "."
    else:
        influencer_text = " Keine starken Personen-/Institutionen-Treffer."

    news_text = " ".join(news_summary[:2])

    return (
        f"{signal_text} "
        f"Gesamt-Risiko {combined_risk_score}/100 ({combined_warning}). "
        f"Crash-Risiko {crash_risk_score}/100 ({market_warning}). "
        f"News-Risiko {news_risk_score}/100 ({news_warning}). "
        f"Coin-News {coin_news_risk_score}/100, "
        f"Markt-News {global_news_risk_score}/100, "
        f"Personen/Institutionen {influencer_risk_score}/100."
        f"{influencer_text} "
        f"News: {news_text} "
        f"Live-Daten: Preis {format_eur(price)}, "
        f"1h {format_percent(change_1h)}, "
        f"24h {format_percent(change_24h)}, "
        f"7d {format_percent(change_7d)}, "
        f"Volumen {format_eur(volume)}, "
        f"Market Cap {format_eur(market_cap)}."
    )


def clamp_score(value: int) -> int:
    if value < 0:
        return 0

    if value > 100:
        return 100

    return int(value)


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
    if action == "SELL":
        return 0

    if action == "BUY":
        return 1

    if action == "HOLD":
        return 2

    return 3
