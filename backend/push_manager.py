import os
import requests
from typing import Tuple

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"


def send_test_push(message: str = "Test Push von SpeedyCoinZales") -> Tuple[bool, str]:
    """
    Sendet einen Test-Push und gibt (ok, detail) zurück.
    """

    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        return False, "ENV fehlt: ONESIGNAL_APP_ID oder ONESIGNAL_API_KEY ist nicht gesetzt"

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

        # OneSignal gibt bei Fehlern oft hilfreichen Text zurück
        if r.status_code >= 300:
            return False, f"OneSignal HTTP {r.status_code}: {r.text}"

        return True, f"OneSignal OK: {r.text}"

    except Exception as e:
        return False, f"Exception: {str(e)}"
