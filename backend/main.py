from fastapi import FastAPI, Query
import json
from .signals import generate_signals

app = FastAPI(title="SpeedyCoinZales API")

# --- Holdings laden ---
with open("holdings.json", "r") as f:
    holdings = json.load(f)

@app.get("/signal")
def get_signals(lang: str = Query("de")):
    """
    Liefert Markt-Signale
    lang: "de" oder "en"
    """
    return generate_signals(holdings, lang)
