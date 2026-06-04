from fastapi import FastAPI, Query, HTTPException
from .signals import generate_signals
from .push_manager import send_test_push
import os

app = FastAPI(title="SpeedyCoinZales API")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")


@app.get("/")
def root():
    return {
        "status": "ok",
        "app": "SpeedyCoinZales",
        "version": "1.0"
    }


@app.get("/signal")
def get_signals(
    lang: str = Query("de"),
    mode: str = Query("konservativ")
):
    allowed_modes = ["konservativ", "normal", "aggressiv"]

    if mode not in allowed_modes:
        raise HTTPException(
            status_code=400,
            detail="Ungültiger Modus. Erlaubt: konservativ, normal, aggressiv"
        )

    return generate_signals(
        lang=lang,
        mode=mode
    )


@app.get("/test-push")
def test_push(token: str = Query("")):
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    ok, detail = send_test_push("Test Push: SpeedyCoinZales ist live ✅")

    return {
        "ok": ok,
        "detail": detail
    }
