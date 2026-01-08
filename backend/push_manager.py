def push_new_signals(signals):
    """
    Dummy Push-Manager.
    Später echte Push-Integration möglich (OneSignal, Pushover etc.)
    """
    for signal in signals:
        if signal["action"] in ["BUY", "SELL"]:
            print(f"[PUSH] {signal['action']} {signal['asset']} auf {signal['börse']}")
