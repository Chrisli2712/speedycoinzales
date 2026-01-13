import os
import hashlib
import requests
from typing import List, Dict, Optional

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"

# Render läuft bei dir mit WEB_CONCURRENCY=1 → In-Memory Dedup ist ok
_LAST_PUSH_SIGNATURE: Optional[str] = None


def _signature(actionable_signals: List[Dict]) -> str:
    """
    Erzeugt eine stabile Signatur (Hash) aus BUY/SELL Signalen,
    damit wir nur pushen, wenn sich etwas geändert hat.
    """
    # Nur die wichtigsten Felder, sortiert, damit Reihenfolge egal ist
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
    Sendet Push über OneSignal:
    - Nur BUY/SELL
    - Nur wenn sich gegenüber dem letzten Push etwas geändert hat
    - Bricht sauber ab, wenn Keys fehlen
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
        print("ℹ️ Push nicht gesendet (keine Änderung)")
        return False

    # Nachrichtentext
    lines = []
    for s in actionable:
        asset = s.get("asset", "?")
        action = s.get("action", "?")
        score = s.get("confidence_score", "?")
        reason = s.get("reason", "")
        lines.append(f"{asset}: {action} ({score}%) – {reason}")

    message = "\n".join(lines)

    title_de = "📊 Trading-Signal Update"
    title_en = "📊 Trading Signal Update"

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        # für erste Tests am zuverlässigsten:
        "included_segments": ["All"],
        "headings": {"de": title_de, "en": title_en},
        "contents": {"de": message, "en": message},
    }

    headers = {
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
        "Content-Type": "application/json",
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


def send_test_push(message: str = "Test Push von SpeedyCoinZales") -> bool:
    """
    Manuelle Test-Push Nachricht (für /test-push Endpoint).
    """
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        print("⚠️ OneSignal nicht konfiguriert – Testpush übersprungen")
        return False

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {"de": "✅ Test Push", "en": "✅ Test Push"},
        "contents": {"de": message, "en": message},
    }

    headers = {
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(ONESIGNAL_URL, json=payload, headers=headers, timeout=10)
        if r.status_code >= 300:
            print("❌ OneSignal Fehler:", r.status_code, r.text)
            return False
        print("✅ Test Push gesendet")
        return True
    except Exception as e:
        print("❌ Test Push Exception:", str(e))
        return False
