from fastapi import FastAPI, Query
import json
from .signals import generate_signals

app = FastAPI(title="SpeedyCoinZales API")

# Holdings laden
with open("holdings.json", "r") as f:
    holdings = json.load(f)

# Alle Assets (Crypto + Aktien) hier definieren
all_assets = {
    "crypto": ["BTC", "LTC", "IOTA", "SOL", "ETH", "DOT"],
    "stocks": ["AAPL", "TSLA", "NVDA", "SONY", "7203.T"]  # Japan-Aktien Beispiel
}

@app.get("/signal")
def get_signals(lang: str = Query("de")):
    """
    Rückgabe aller Signale.
    Parameter:
        lang: 'de' für Deutsch, 'en' für Englisch
    """
    return generate_signals(holdings, all_assets, lang)
