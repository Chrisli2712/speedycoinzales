from fastapi import FastAPI, Query
from backend.signals import generate_signals

app = FastAPI(title="SpeedyCoinZales API")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/signal")
def get_signals(lang: str = Query("de")):
    return generate_signals(lang=lang)
