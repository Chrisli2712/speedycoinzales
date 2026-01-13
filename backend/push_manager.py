import os
import hashlib
import requests
from typing import List, Dict, Optional, Tuple

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"

_LAST_PUSH_SIGNATURE: Optional[str] = None


def _signature(actionable_signals: List[Dict]) -> str:
    rows = []
    for s in actionable_signals:
        rows.append(
            f"{s.get('asset','')}|{s.get('börse','')}|{s.get('action','')}|{s.get('confidence_score','')}"
        )
    rows.sort()
    payload = "\n".join(rows).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _post_onesignal(payload: Dict) -> Tuple[bool, str]:
    """
    Sendet an OneSignal und bewertet Erfolg korrekt:
    - HTTP >= 300 => ok False
    - HTTP 200 aber JSON enthält 'errors' => ok False
    """
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        return False, "ENV fehlt: ONESIGNAL_APP_ID oder ONESIGNAL_API_KEY"

    headers = {
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
        "Content-Type": "application/json; charset=utf-8",
    }

    try:
        r = requests.post(ONESIGNAL_URL, json=payload, headers=headers, timeout=10)
        text = r.text

        if r.status_code >= 300:
            return False, f"OneSignal HTTP {r.status_code}: {text}"

        # OneSignal kann HTTP 200 liefern, aber errors im JSON haben
        try:
            data = r.json()
        except Exception:
            # Wenn kein JSON, trotzdem als ok werten
            return True, f"OneSignal OK (non-JSON): {text}"

        if isinstance(data, dict) and data.get("errors"):
            return False, f"OneSignal errors: {data.get('errors')}"

        return True, f"OneSignal OK: {text}"

    except Exception as e:
        return False, f"Exception: {str(e)}"


def push_new_signals(signals: List[Dict], lang: str = "de") -> Tuple[bool, str]:
    """
    Push nur bei BUY/SELL und nur wenn sich etwas geändert hat.
    Gibt (ok, detail) zurück.
    """
    global _LAST_PUSH_SIGNATURE

    actionable = [s for s in signals if s.get("action") in ("BUY", "SELL")]
    if not actionable:
        return False, "No actionable signals (no BUY/SELL)"

    sig = _signature(actionable)
    if _LAST_PUSH_SIGNATURE == sig:
        return False, "No change since last push"

    lines = []
    for s in actionable:
        asset = s.get("asset", "?")
        action = s.get("action", "?")
        score = s.get("confidence_score", "?")
        reason = s.get("reason", "")
        lines.append(f"{asset}: {action} ({score}%) – {reason}")

    message = "\n".join(lines)

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        # Für Produktion später eher: ["Subscribed Users"]
        "included_segments": ["All"],
        "headings": {"de": "📊 Trading-Signal Update", "en": "📊 Trading Signal Update"},
        "contents": {"de": message, "en": message},
    }

    ok, detail = _post_onesignal(payload)
    if ok:
        _LAST_PUSH_SIGNATURE = sig
    return ok, detail


def send_test_push(message: str = "Test Push von SpeedyCoinZales") -> Tuple[bool, str]:
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {"de": "✅ Test Push", "en": "✅ Test Push"},
        "contents": {"de": message, "en": message},
    }
    return _post_onesignal(payload)
