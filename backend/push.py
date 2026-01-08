import requests
import os

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")

def send_push(title: str, message: str):
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        return

    url = "https://onesignal.com/api/v1/notifications"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {ONESIGNAL_API_KEY}"
    }

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {"de": title},
        "contents": {"de": message}
    }

    requests.post(url, json=payload, headers=headers)
