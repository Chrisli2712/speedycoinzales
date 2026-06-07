from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import hashlib
import json
import os
import time
import uuid

import requests


COINPAPRIKA_URL = "https://api.coinpaprika.com/v1/tickers"
COINBASE_BASE_URL = "https://api.coinbase.com"
BITUNIX_BASE_URL = os.getenv("BITUNIX_BASE_URL", "https://openapi.bitunix.com")

PORTFOLIO_CACHE_SECONDS = int(os.getenv("PORTFOLIO_CACHE_SECONDS", "120"))
PORTFOLIO_MIN_VALUE_EUR = float(os.getenv("PORTFOLIO_MIN_VALUE_EUR", "0.01"))

_PORTFOLIO_CACHE_DATA: Optional[Dict] = None
_PORTFOLIO_CACHE_TIME: float = 0.0

_PRICE_CACHE_DATA: Optional[Dict[str, float]] = None
_PRICE_CACHE_TIME: float = 0.0
PRICE_CACHE_SECONDS = 300


def get_portfolio_snapshot() -> Dict:
    global _PORTFOLIO_CACHE_DATA
    global _PORTFOLIO_CACHE_TIME

    now = time.time()

    if (
        _PORTFOLIO_CACHE_DATA is not None
        and now - _PORTFOLIO_CACHE_TIME < PORTFOLIO_CACHE_SECONDS
    ):
        return _PORTFOLIO_CACHE_DATA

    prices_eur = fetch_prices_eur()

    all_holdings: List[Dict] = []
    sources: List[Dict] = []

    coinbase_holdings, coinbase_status = fetch_coinbase_holdings()
    sources.append(coinbase_status)
    all_holdings.extend(coinbase_holdings)

    bitunix_holdings, bitunix_status = fetch_bitunix_spot_holdings()
    sources.append(bitunix_status)
    all_holdings.extend(bitunix_holdings)

    aggregated_holdings = aggregate_holdings(all_holdings)
    enriched_holdings = enrich_holdings_with_prices(aggregated_holdings, prices_eur)

    known_value_eur = 0.0
    unknown_value_assets = []

    for holding in enriched_holdings:
        value_eur = holding.get("value_eur")

        if value_eur is None:
            unknown_value_assets.append(holding.get("asset"))
        else:
            known_value_eur += float(value_eur)

    for holding in enriched_holdings:
        value_eur = holding.get("value_eur")

        if value_eur is None or known_value_eur <= 0:
            holding["portfolio_percent"] = None
        else:
            holding["portfolio_percent"] = round((value_eur / known_value_eur) * 100, 2)

    enriched_holdings = [
        h for h in enriched_holdings
        if h.get("value_eur") is None or h.get("value_eur", 0) >= PORTFOLIO_MIN_VALUE_EUR
    ]

    enriched_holdings = sorted(
        enriched_holdings,
        key=lambda h: (
            h.get("value_eur") is None,
            -(h.get("value_eur") or 0),
            h.get("asset", ""),
        ),
    )

    result = {
        "ok": True,
        "portfolio_live": True,
        "mode": "READ_ONLY",
        "security_note": "Portfolio wird nur gelesen. Es werden keine Trades oder Auszahlungen ausgeführt.",
        "sources": sources,
        "total_value_eur": round(known_value_eur, 2),
        "unknown_value_assets": unknown_value_assets,
        "holdings": enriched_holdings,
        "holding_count": len(enriched_holdings),
        "cache_seconds": PORTFOLIO_CACHE_SECONDS,
        "last_update_utc": datetime.now(timezone.utc).isoformat(),
    }

    _PORTFOLIO_CACHE_DATA = result
    _PORTFOLIO_CACHE_TIME = now

    return result


def fetch_coinbase_holdings() -> Tuple[List[Dict], Dict]:
    api_key = os.getenv("COINBASE_API_KEY", "").strip()
    api_secret = os.getenv("COINBASE_API_SECRET", "").strip().replace("\\n", "\n")

    if not api_key or not api_secret:
        return [], {
            "source": "Coinbase",
            "configured": False,
            "ok": False,
            "detail": "COINBASE_API_KEY oder COINBASE_API_SECRET fehlt.",
        }

    try:
        from coinbase.jwt_generator import build_rest_jwt, format_jwt_uri
    except Exception as e:
        return [], {
            "source": "Coinbase",
            "configured": True,
            "ok": False,
            "detail": f"coinbase-advanced-py fehlt oder kann nicht geladen werden: {str(e)}",
        }

    holdings: List[Dict] = []
    path = "/api/v3/brokerage/accounts"
    cursor = None

    try:
        while True:
            params = {"limit": 250}

            if cursor:
                params["cursor"] = cursor

            jwt_uri = format_jwt_uri("GET", path)
            jwt_token = build_rest_jwt(jwt_uri, api_key, api_secret)

            response = requests.get(
                COINBASE_BASE_URL + path,
                params=params,
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/json",
                    "User-Agent": "SpeedyCoinZales/1.0",
                },
                timeout=15,
            )

            if response.status_code >= 300:
                return holdings, {
                    "source": "Coinbase",
                    "configured": True,
                    "ok": False,
                    "detail": f"Coinbase HTTP {response.status_code}: {response.text}",
                }

            data = response.json()
            accounts = data.get("accounts", [])

            if not isinstance(accounts, list):
                accounts = []

            for account in accounts:
                asset = str(account.get("currency", "")).upper().strip()

                if not asset:
                    continue

                available_balance = account.get("available_balance", {})
                hold_balance = account.get("hold", {})

                available = safe_float(available_balance.get("value")) or 0.0
                locked = safe_float(hold_balance.get("value")) or 0.0
                amount = available + locked

                if amount <= 0:
                    continue

                holdings.append(
                    {
                        "source": "Coinbase",
                        "asset": asset,
                        "amount": round(amount, 12),
                        "available": round(available, 12),
                        "locked": round(locked, 12),
                        "raw_name": account.get("name"),
                    }
                )

            if data.get("has_next") and data.get("cursor"):
                cursor = data.get("cursor")
            else:
                break

        return holdings, {
            "source": "Coinbase",
            "configured": True,
            "ok": True,
            "detail": f"{len(holdings)} Coinbase-Bestände geladen.",
        }

    except Exception as e:
        return holdings, {
            "source": "Coinbase",
            "configured": True,
            "ok": False,
            "detail": f"Coinbase Fehler: {str(e)}",
        }


def fetch_bitunix_spot_holdings() -> Tuple[List[Dict], Dict]:
    api_key = os.getenv("BITUNIX_API_KEY", "").strip()
    secret_key = os.getenv("BITUNIX_SECRET_KEY", "").strip()

    if not api_key or not secret_key:
        return [], {
            "source": "Bitunix Spot",
            "configured": False,
            "ok": False,
            "detail": "BITUNIX_API_KEY oder BITUNIX_SECRET_KEY fehlt.",
        }

    path = "/api/spot/v1/user/account"

    try:
        headers = build_bitunix_headers(
            api_key=api_key,
            secret_key=secret_key,
            query_params={},
            body=None,
        )

        response = requests.get(
            BITUNIX_BASE_URL + path,
            headers=headers,
            timeout=15,
        )

        if response.status_code >= 300:
            return [], {
                "source": "Bitunix Spot",
                "configured": True,
                "ok": False,
                "detail": f"Bitunix HTTP {response.status_code}: {response.text}",
            }

        data = response.json()

        success = data.get("success")
        code = str(data.get("code", ""))

        if success is False or code not in ["0", ""]:
            return [], {
                "source": "Bitunix Spot",
                "configured": True,
                "ok": False,
                "detail": f"Bitunix API Fehler: {data}",
            }

        rows = data.get("data", [])

        if not isinstance(rows, list):
            rows = []

        holdings: List[Dict] = []

        for row in rows:
            asset = str(row.get("coin", "")).upper().strip()

            if not asset:
                continue

            available = safe_float(row.get("balance")) or 0.0
            locked = safe_float(row.get("balanceLocked")) or 0.0
            amount = available + locked

            if amount <= 0:
                continue

            holdings.append(
                {
                    "source": "Bitunix Spot",
                    "asset": asset,
                    "amount": round(amount, 12),
                    "available": round(available, 12),
                    "locked": round(locked, 12),
                    "raw_name": asset,
                }
            )

        return holdings, {
            "source": "Bitunix Spot",
            "configured": True,
            "ok": True,
            "detail": f"{len(holdings)} Bitunix-Spot-Bestände geladen.",
        }

    except Exception as e:
        return [], {
            "source": "Bitunix Spot",
            "configured": True,
            "ok": False,
            "detail": f"Bitunix Fehler: {str(e)}",
        }


def build_bitunix_headers(
    api_key: str,
    secret_key: str,
    query_params: Dict,
    body: Optional[Dict],
) -> Dict:
    nonce = uuid.uuid4().hex
    timestamp = str(int(time.time() * 1000))

    query_string = build_bitunix_query_string(query_params)

    if body is None:
        body_string = ""
    else:
        body_string = json.dumps(body, separators=(",", ":"), ensure_ascii=False)

    digest_input = nonce + timestamp + api_key + query_string + body_string
    digest = sha256_hex(digest_input)
    sign = sha256_hex(digest + secret_key)

    return {
        "api-key": api_key,
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "SpeedyCoinZales/1.0",
    }


def build_bitunix_query_string(query_params: Dict) -> str:
    if not query_params:
        return ""

    parts = []

    for key in sorted(query_params.keys()):
        value = query_params[key]
        parts.append(f"{key}{value}")

    return "".join(parts)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch_prices_eur() -> Dict[str, float]:
    global _PRICE_CACHE_DATA
    global _PRICE_CACHE_TIME

    now = time.time()

    if _PRICE_CACHE_DATA is not None and now - _PRICE_CACHE_TIME < PRICE_CACHE_SECONDS:
        return _PRICE_CACHE_DATA

    prices: Dict[str, float] = {
        "EUR": 1.0,
    }

    try:
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
            _PRICE_CACHE_DATA = prices
            _PRICE_CACHE_TIME = now
            return prices

        data = response.json()

        if not isinstance(data, list):
            _PRICE_CACHE_DATA = prices
            _PRICE_CACHE_TIME = now
            return prices

        best_rank_by_symbol: Dict[str, int] = {}

        for item in data:
            symbol = str(item.get("symbol", "")).upper().strip()

            if not symbol:
                continue

            quotes = item.get("quotes", {})
            eur = quotes.get("EUR", {})
            price = safe_float(eur.get("price"))

            if price is None or price <= 0:
                continue

            rank = safe_int(item.get("rank"), 999999)

            if symbol not in prices or rank < best_rank_by_symbol.get(symbol, 999999):
                prices[symbol] = price
                best_rank_by_symbol[symbol] = rank

    except Exception:
        pass

    _PRICE_CACHE_DATA = prices
    _PRICE_CACHE_TIME = now

    return prices


def aggregate_holdings(holdings: List[Dict]) -> List[Dict]:
    by_asset: Dict[str, Dict] = {}

    for holding in holdings:
        asset = str(holding.get("asset", "")).upper().strip()

        if not asset:
            continue

        if asset not in by_asset:
            by_asset[asset] = {
                "asset": asset,
                "amount": 0.0,
                "available": 0.0,
                "locked": 0.0,
                "sources": [],
            }

        by_asset[asset]["amount"] += safe_float(holding.get("amount")) or 0.0
        by_asset[asset]["available"] += safe_float(holding.get("available")) or 0.0
        by_asset[asset]["locked"] += safe_float(holding.get("locked")) or 0.0

        by_asset[asset]["sources"].append(
            {
                "source": holding.get("source"),
                "amount": holding.get("amount"),
                "available": holding.get("available"),
                "locked": holding.get("locked"),
            }
        )

    result = []

    for item in by_asset.values():
        result.append(
            {
                "asset": item["asset"],
                "amount": round(item["amount"], 12),
                "available": round(item["available"], 12),
                "locked": round(item["locked"], 12),
                "sources": item["sources"],
            }
        )

    return result


def enrich_holdings_with_prices(
    holdings: List[Dict],
    prices_eur: Dict[str, float],
) -> List[Dict]:
    enriched = []

    for holding in holdings:
        asset = holding.get("asset")
        amount = safe_float(holding.get("amount")) or 0.0
        price_eur = prices_eur.get(asset)

        if price_eur is None:
            value_eur = None
        else:
            value_eur = round(amount * price_eur, 2)

        enriched.append(
            {
                **holding,
                "price_eur": round(price_eur, 8) if price_eur is not None else None,
                "value_eur": value_eur,
            }
        )

    return enriched


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
