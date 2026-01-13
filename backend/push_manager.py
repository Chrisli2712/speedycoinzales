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


def push_new_signals(signals: List[Dict], lang: str = "de") -> bool:
    """
    Push nur bei BUY/SELL und nur wenn sich etwas geändert hat.
    """
    global _LAST_PUSH_SIGNATURE

    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        print("⚠️ OneSignal nicht konfiguriert – Push übersprungen")
        return False

    actionable = [s for s in signals if s.get("action") in ("BUY", "SELL")]
    if not actionable:
        return False

    sig = _signature(actionable)
    if _LAST_PUSH_SIGNATURE == sig:
        print("ℹ️ Keine Änderung – kein Push")
        return False

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
        "included_segments": ["All"],
        "headings": {"de": "📊 Trading-Signal Update", "en": "📊 Trading Signal Update"},
        "contents": {"de": message, "en": message},
    }

    headers = {
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
        "Content-Type": "application/json; charset=utf-8",
    }

    try:
        r = requests.post(ONESIGNAL_URL, json=payload, headers=headers, timeout=10)
        if r.status_code >= 300:
            print("❌ OneSignal Fehler:", r.status_code, r.text)
            return False

        _LAST_PUSH_SIGNATURE = sig
        print("✅ Push gesendet")
        return True

    except Exception as e:
        print("❌ Push Exception:", str(e))
        return False


def send_test_push(message: str = "Test Push von SpeedyCoinZales") -> Tuple[bool, str]:
    """
    Test Push mit Debug-Text zurück.
    """
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        return False, "ENV fehlt: ONESIGNAL_APP_ID oder ONESIGNAL_API_KEY"

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {"de": "✅ Test Push", "en": "✅ Test Push"},
        "contents": {"de": message, "en": message},
    }

    headers = {
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
        "Content-Type": "application/json; charset=utf-8",
    }

    try:
        r = requests.post(ONESIGNAL_URL, json=payload, headers=headers, timeout=10)
        if r.status_code >= 300:
            return False, f"OneSignal HTTP {r.status_code}: {r.text}"
        return True, f"OneSignal OK: {r.text}"
    except Exception as e:
        return False, f"Exception: {str(e)}"
