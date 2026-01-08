import os
import requests

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")


def push_new_signals(signals):
    # Falls OneSignal (noch) nicht konfiguriert ist → App soll TROTZDEM laufen
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        print("OneSignal ENV vars missing – skipping push")
        return

    for s in signals:
        if s.get("action") != "BUY":
            continue

        payload = {
            "app_id": ONESIGNAL_APP_ID,
            "included_segments": ["All"],
            "headings": {"en": f"BUY Signal: {s['asset']}"},
            "contents": {"en": s["reason"]},
        }

        headers = {
            "Authorization": f"Basic {ONESIGNAL_API_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            "https://onesignal.com/api/v1/notifications",
            json=payload,
            headers=headers,
            timeout=10,
        )

        print("OneSignal status:", response.status_code)
