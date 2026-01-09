import os
import requests

# OneSignal Zugangsdaten aus Render Environment
ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")

ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"


def push_new_signals(signals: list):
    """
    Sendet Push-Nachrichten über OneSignal.
    Wenn keine Keys gesetzt sind → leise abbrechen (kein Crash).
    """

    # Sicherheit: App darf niemals crashen
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        print("⚠️ OneSignal nicht konfiguriert – Push übersprungen")
        return

    if not signals:
        return

    # Text für Push zusammenbauen
    message_lines = []
    for s in signals:
        action = s.get("action", "")
        asset = s.get("asset", "")
        score = s.get("confidence_score", "")
        message_lines.append(f"{asset}: {action} ({score}%)")

    message = "\n".join(message_lines)

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Subscribed Users"],
        "headings": {"en": "📊 Trading-Signale", "de": "📊 Trading-Signale"},
        "contents": {"en": message, "de": message},
    }

    headers = {
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            ONESIGNAL_URL,
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code >= 300:
            print("❌ OneSignal Fehler:", response.text)
        else:
            print("✅ Push gesendet")

    except Exception as e:
        print("❌ Push Exception:", str(e))
