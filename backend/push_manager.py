import requests
import os

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID", "DEINE_APP_ID")
ONESIGNAL_REST_KEY = os.getenv("ONESIGNAL_REST_KEY", "DEIN_REST_API_KEY")
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"

def send_push(signals):
    for signal in signals:
        if signal["action"] in ["BUY", "SELL"]:
            message = f"{signal['action']} {signal['asset']} auf {signal['börse']} (Preis: {signal['current_price_eur']} EUR)"
            payload = {
                "app_id": ONESIGNAL_APP_ID,
                "included_segments": ["All"],
                "headings": {"en": "SpeedyCoinZales Signal", "de": "SpeedyCoinZales Signal"},
                "contents": {"en": message, "de": message}
            }
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Basic {ONESIGNAL_REST_KEY}"
            }
            try:
                requests.post(ONESIGNAL_URL, json=payload, headers=headers)
            except Exception as e:
                print(f"[Push Error] {e}")
