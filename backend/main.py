from fastapi import FastAPI, Query, HTTPException
from .signals import generate_signals
from .push_manager import send_test_push
import os

app = FastAPI(title="SpeedyCoinZales API")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")  # optional


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/signal")
def get_signals(lang: str = Query("de")):
    # Hinweis: Signale sind nur Info, keine Anlageberatung.
    return generate_signals(lang=lang)


@app.get("/test-push")
def test_push(token: str = Query("")):
    """
    Optionaler Endpoint: sendet Test-Push.
    Wenn ADMIN_TOKEN gesetzt ist, muss token passen.
    """
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    ok = send_test_push("Test Push: SpeedyCoinZales ist live ✅")
    return {"ok": ok}
