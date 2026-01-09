import os
import requests

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"

def push_new_signals(signals):
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        print("OneSignal Keys fehlen")
        return
    headers = {
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {"en": "Neue Signale verfügbar!"},
        "contents": {"en": f"{len(signals)} neue Signale generiert."}
    }
    response = requests.post(ONESIGNAL_URL, json=payload, headers=headers)
    print("Push Response:", response.json())
