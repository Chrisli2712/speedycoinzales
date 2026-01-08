import json
import os
from push import send_push

LAST_SIGNALS_FILE = "last_signals.json"

def load_last_signals():
    if os.path.exists(LAST_SIGNALS_FILE):
        with open(LAST_SIGNALS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_last_signals(signals):
    with open(LAST_SIGNALS_FILE, "w") as f:
        json.dump(signals, f)

def push_new_signals(signals):
    """
    Prüft, welche Signale neu sind oder sich geändert haben,
    und verschickt nur dafür Push-Benachrichtigungen.
    """
    last_signals = load_last_signals()
    updated_signals = {}

    for signal in signals:
        asset = signal["asset"]
        # Prüfen, ob Signal neu oder anders ist
        if asset not in last_signals or last_signals[asset] != signal["action"]:
            # Nur bei BUY/SELL & Confidence >= 90
            if signal["confidence_score"] >= 90 and signal["action"] in ["BUY", "SELL"]:
                send_push(
                    f"{signal['action']} Signal 🚨",
                    f"{asset} auf {signal['börse']} – Confidence {signal['confidence_score']}%"
                )
        updated_signals[asset] = signal["action"]

    # Speichern für den nächsten Vergleich
    save_last_signals(updated_signals)
