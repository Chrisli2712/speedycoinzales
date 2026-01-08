import requests
import os

# OneSignal API Daten
ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID", "bc6352cb-5fb4-4fbb-9e54-066c7e1f57dc")
ONESIGNAL_REST_KEY = os.getenv("ONESIGNAL_REST_KEY", "hspoh5doauw3f4plelozqtwuu")
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"

def send_push(signals):
    """
    Sendet Push-Benachrichtigungen für BUY/SELL Signale
    """
    for signal in signals:
        if signal["action"] in ["BUY", "SELL"]:
            message = f"{signal['action']} {signal['asset']} auf {signal['börse']} (Risikostufe: {signal['risk']})"
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
                response = requests.post(ONESIGNAL_URL, json=payload, headers=headers)
                if response.status_code == 200:
                    print(f"[Push] {signal['asset']} gesendet")
                else:
                    print(f"[Push Fehler] {response.text}")
            except Exception as e:
                print(f"[Push Exception] {e}")
