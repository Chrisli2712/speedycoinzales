import os
import requests

ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID")
ONESIGNAL_API_KEY = os.getenv("ONESIGNAL_API_KEY")

def push_new_signals(signals):
    if not ONESIGNAL_APP_ID or not ONESIGNAL_API_KEY:
        print("⚠️ OneSignal ENV vars missing – push skipped")
        return

    buy_signals = [s for s in signals if s["action"] in ["BUY", "SELL"]]

    if not buy_signals:
        return

    message = "\n".join(
        f"{s['asset']}: {s['action']} ({s['confidence_score']}%)"
        for s in buy_signals
    )

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {"en": "Trading Signal Update"},
        "contents": {"en": message},
    }

    headers = {
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
        "Content-Type": "application/json",
    }

    requests.post(
        "https://onesignal.com/api/v1/notifications",
        json=payload,
        headers=headers,
        timeout=10,
    )
