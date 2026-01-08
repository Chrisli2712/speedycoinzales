import requests
import os

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID", "bc6352cb-5fb4-4fbb-9e54-066c7e1f57dc")
ONESIGNAL_REST_KEY = os.getenv("ONESIGNAL_REST_KEY", "hspoh5doauw3f4plelozqtwuu")

def push_new_signals(signals):
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        return

    for s in signals:
        if s["action"] != "BUY":
            continue

        payload = {
            "app_id": ONESIGNAL_APP_ID,
            "included_segments": ["All"],
            "headings": {"en": f"BUY Signal: {s['asset']}"},
            "contents": {"en": s["reason"]}
        }

        headers = {
            "Authorization": f"Basic {ONESIGNAL_API_KEY}",
            "Content-Type": "application/json"
        }

        requests.post(
            "https://onesignal.com/api/v1/notifications",
            json=payload,
            headers=headers
        )
