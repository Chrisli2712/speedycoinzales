import os
import hashlib
import requests
from typing import List, Dict, Optional, Tuple

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"

_LAST_PUSH_SIGNATURE: Optional[str] = None


def _build_signature(signals: List[Dict]) -> str:
    rows = []

    for s in signals:
        rows.append(
            f"{s.get('asset','')}|"
            f"{s.get('börse','')}|"
            f"{s.get('action','')}|"
            f"{s.get('confidence_score','')}|"
            f"{s.get('suggested_amount_eur','')}"
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


def push_new_signals(signals: List[Dict], lang: str = "de") -> Tuple[bool, str]:
    global _LAST_PUSH_SIGNATURE

    actionable = [
        s for s in signals
        if s.get("action") in ["BUY", "SELL"]
        and int(s.get("confidence_score", 0)) >= 80
    ]

    if not actionable:
        return False, "Keine BUY/SELL Signale"

    current_signature = _build_signature(actionable)

    if _LAST_PUSH_SIGNATURE == current_signature:
        return False, "Keine Änderung seit letztem Push"

    lines = []

    for s in actionable:
        asset = s.get("asset", "?")
        action = s.get("action", "?")
        confidence = s.get("confidence_score", "?")
        amount = s.get("suggested_amount_eur")
        reason = s.get("reason", "")

        if amount is None:
            amount_text = "-"
        else:
            amount_text = f"{amount} €"

        lines.append(
            f"{asset}: {action} ({confidence}%)\n"
            f"Betrag: {amount_text}\n"
            f"Grund: {reason}"
        )

    message = "\n\n".join(lines)

    ok, detail = _send_to_onesignal(
        title="🚨 Neues Trading-Signal",
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
