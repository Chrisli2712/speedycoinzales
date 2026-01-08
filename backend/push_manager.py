import requests
import os

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID", "bc6352cb-5fb4-4fbb-9e54-066c7e1f57dc")
ONESIGNAL_REST_KEY = os.getenv("ONESIGNAL_REST_KEY", "hspoh5doauw3f4plelozqtwuu")
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"

def push_new_signals(signals, lang="de"):
    if not ONESIGNAL_APP_ID or not ONESIGNAL_REST_KEY:
        print("OneSignal Keys fehlen!")
        return

    for s in signals:
        message = f"{s['action']} Signal für {s['asset']} an {s['börse']}. Grund: {s['reason']}"
        payload = {
            "app_id": ONESIGNAL_APP_ID,
            "included_segments": ["All"],
            "headings": {"en": "Trading Signal", "de": "Handelssignal"},
            "contents": {"en": message, "de": message}
        }
        headers = {
            "Authorization": f"Basic {ONESIGNAL_REST_KEY}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(ONESIGNAL_URL, json=payload, headers=headers)
            if response.status_code == 200:
                print(f"Push erfolgreich: {s['asset']}")
            else:
                print(f"Push fehlgeschlagen: {response.text}")
        except Exception as e:
            print(f"Push Error: {e}")
