from fastapi import FastAPI, Query
import json
from .signals import generate_signals

app = FastAPI(title="SpeedyCoinZales API")

# Holdings & alle Assets laden
with open("holdings.json", "r") as f:
    holdings = json.load(f)

with open("assets.json", "r") as f:
    all_assets = json.load(f)

@app.get("/signal")
def get_signals(lang: str = Query("de")):
    return generate_signals(holdings, all_assets, lang)
