from fastapi import FastAPI, Query
from backend.signals import generate_signals
import json

app = FastAPI(title="SpeedyCoinZales API")

with open("holdings.json", "r") as f:
    holdings = json.load(f)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/signal")
def get_signals(lang: str = Query("de")):
    return generate_signals(holdings, lang)
