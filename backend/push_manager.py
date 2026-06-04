import os
import hashlib
import requests
from typing import List, Dict, Optional, Tuple


ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"

_LAST_PUSH_SIGNATURE: Optional[str] = None


def _risk_bucket(value) -> int:
    try:
        number = int(value)
    except Exception:
        number = 0

    if number < 0:
        number = 0

    if number > 100:
        number = 100

    # Damit nicht bei jeder kleinen Änderung ein neuer Push kommt.
    # Beispiel: 81 und 84 bleiben beide im 80er-Bereich.
    return int(number / 10) * 10


def _build_signature(signals: List[Dict]) -> str:
    rows = []

    for s in signals:
        rows.append(
            f"{s.get('asset', '')}|"
            f"{s.get('action', '')}|"
            f"{s.get('recommendation_short', '')}|"
            f"{s.get('priority_level', '')}|"
            f"{_risk_bucket(s.get('combined_risk_score', 0))}|"
            f"{_risk_bucket(s.get('crash_risk_score', 0))}|"
            f"{_risk_bucket(s.get('news_risk_score', 0))}|"
            f"{s.get('combined_warning', '')}|"
            f"{s.get('market_warning', '')}|"
            f"{s.get('news_warning', '')}"
        )

    rows.sort()
    raw = "\n".join(rows).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _send_to_onesignal(title: str, message: str) -> Tuple[bool, str]:
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        return False, "ENV fehlt: ONESIGNAL_APP_ID oder ONESIGNAL_API_KEY"

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {
            "de": title,
            "en": title
        },
        "contents": {
            "de": message,
            "en": message
        }
    }

    headers = {
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }

    try:
        response = requests.post(
            ONESIGNAL_URL,
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code >= 300:
            return False, f"OneSignal HTTP {response.status_code}: {response.text}"

        try:
            data = response.json()
            if isinstance(data, dict) and data.get("errors"):
                return False, f"OneSignal errors: {data.get('errors')}"
        except Exception:
            pass

        return True, f"OneSignal OK: {response.text}"

    except Exception as e:
        return False, f"Exception: {str(e)}"


def _safe_text(value, fallback: str = "-") -> str:
    if value is None:
        return fallback

    text = str(value).strip()

    if not text:
        return fallback

    return text


def _format_percent(value) -> str:
    try:
        number = float(value)
        sign = "+" if number > 0 else ""
        return f"{sign}{number:.2f} %"
    except Exception:
        return "-"


def _format_score(value) -> str:
    try:
        number = int(value)
        return f"{number}/100"
    except Exception:
        return "-/100"


def _format_amount(value) -> str:
    try:
        if value is None:
            return "-"

        number = float(value)
        return f"{number:.2f} €"
    except Exception:
        return "-"


def _priority_sort_value(signal: Dict) -> int:
    try:
        return int(signal.get("priority_level", 9))
    except Exception:
        return 9


def _build_push_title(signals: List[Dict]) -> str:
    has_sell = any(s.get("action") == "SELL" for s in signals)
    has_buy = any(s.get("action") == "BUY" for s in signals)

    highest_combined = 0

    for s in signals:
        try:
            highest_combined = max(highest_combined, int(s.get("combined_risk_score", 0)))
        except Exception:
            pass

    if has_sell and highest_combined >= 85:
        return "🚨 SpeedyCoinZales: EXTREME WARNUNG"

    if has_sell:
        return "⚠️ SpeedyCoinZales: Verkaufssignal"

    if has_buy:
        return "🟢 SpeedyCoinZales: Kaufchance"

    return "📊 SpeedyCoinZales Signal"


def _build_push_message(signals: List[Dict]) -> str:
    sorted_signals = sorted(
        signals,
        key=lambda s: (
            _priority_sort_value(s),
            -int(s.get("combined_risk_score", 0) or 0),
            -int(s.get("crash_risk_score", 0) or 0),
            -int(s.get("confidence_score", 0) or 0)
        )
    )

    # Push kurz halten: maximal 3 wichtigste Signale.
    top_signals = sorted_signals[:3]

    lines = []

    for s in top_signals:
        asset = _safe_text(s.get("asset"))
        action = _safe_text(s.get("action"))
        badge = _safe_text(s.get("recommendation_badge"), "")
        short = _safe_text(s.get("recommendation_short"), action)
        priority = _safe_text(s.get("priority_text"), "-")

        confidence = _format_score(s.get("confidence_score"))
        combined = _format_score(s.get("combined_risk_score"))
        crash = _format_score(s.get("crash_risk_score"))
        news = _format_score(s.get("news_risk_score"))

        change_24h = _format_percent(s.get("change_24h_percent"))
        change_7d = _format_percent(s.get("change_7d_percent"))

        amount = _format_amount(s.get("suggested_amount_eur"))

        block = (
            f"{badge}\n"
            f"{asset}: {short}\n"
            f"Priorität: {priority}\n"
            f"Confidence: {confidence}\n"
            f"Gesamt-Risiko: {combined}\n"
            f"Crash: {crash} | News: {news}\n"
            f"24h: {change_24h} | 7d: {change_7d}"
        )

        if s.get("action") == "BUY":
            block += f"\nBetrag: {amount}"

        lines.append(block)

    if len(sorted_signals) > 3:
        lines.append(f"+ {len(sorted_signals) - 3} weitere Signale in der App")

    return "\n\n".join(lines)


def push_new_signals(signals: List[Dict], lang: str = "de") -> Tuple[bool, str]:
    global _LAST_PUSH_SIGNATURE

    actionable = [
        s for s in signals
        if s.get("action") in ["BUY", "SELL"]
        and int(s.get("confidence_score", 0)) >= 90
    ]

    if not actionable:
        return False, "Keine BUY/SELL Signale"

    current_signature = _build_signature(actionable)

    if _LAST_PUSH_SIGNATURE == current_signature:
        return False, "Keine Änderung seit letztem Push"

    title = _build_push_title(actionable)
    message = _build_push_message(actionable)

    ok, detail = _send_to_onesignal(
        title=title,
        message=message
    )

    if ok:
        _LAST_PUSH_SIGNATURE = current_signature

    return ok, detail


def send_test_push(message: str = "Test Push von SpeedyCoinZales") -> Tuple[bool, str]:
    return _send_to_onesignal(
        title="✅ SpeedyCoinZales Test",
        message=message
    )
