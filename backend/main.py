from fastapi import FastAPI, Query
import json
from backend.signals import generate_signals

app = FastAPI(title="SpeedyCoinZales API")

with open("holdings.json", "r") as f:
    holdings = json.load(f)

@app.get("/signal")
def get_signals(lang: str = Query("de")):
    return generate_signals(holdings, lang)
