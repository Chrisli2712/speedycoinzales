import requests
import os

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID", "bc6352cb-5fb4-4fbb-9e54-066c7e1f57dc")
ONESIGNAL_REST_KEY = os.getenv("ONESIGNAL_REST_KEY", "hspoh5doauw3f4plelozqtwuu")

def push_new_signals(signals, lang="de"):
    if not signals:
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {ONESIGNAL_API_KEY}"
    }

    for signal in signals:
        title = f"Neues Asset: {signal['asset']}" if lang=="de" else f"New Asset: {signal['asset']}"
        content = f"Aktion: {signal['action']}, empfohlen: {signal['suggested_amount_eur']} €" \
                  if signal["suggested_amount_eur"] else f"Aktion: {signal['action']}"

        data = {
            "app_id": ONESIGNAL_APP_ID,
            "included_segments": ["All"],
            "headings": {"en": title, "de": title},
            "contents": {"en": content, "de": content}
        }

        response = requests.post("https://onesignal.com/api/v1/notifications", headers=headers, json=data)
        print(response.status_code, response.text)
