from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

from app import browser, store
from app.ip_lookup import lookup_ip
from app.models import FingerprintConfig, ProfileCreate, ProfileUpdate
from app.platform_presets import PRESETS
from app.profile_geo import apply_ip_hints, resolve_ip_for_profile

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
API_KEY = os.environ.get("FB_API_KEY", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await browser.shutdown_all()


app = FastAPI(title="Fingerprint Browser", lifespan=lifespan)


def _check_auth(authorization: str | None) -> None:
    if not API_KEY:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


@app.get("/status")
@app.get("/api/v1/status")
def status() -> dict:
    return {"code": 0, "msg": "success"}


@app.get("/api/v1/user/list")
def list_users_compat(authorization: str | None = None) -> dict:
    _check_auth(authorization)
    profiles = store.list_profiles()
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "list": [
                {
                    "user_id": p.id,
                    "name": p.name,
                    "group_name": p.group,
                    "remark": p.remark,
                }
                for p in profiles
            ]
        },
    }


@app.get("/api/v2/browser-profile/list")
def list_profiles_v2(authorization: str | None = None) -> dict:
    return list_users_compat(authorization)


@app.post("/api/v2/browser-profile/create")
def create_profile_v2(body: ProfileCreate, authorization: str | None = None) -> dict:
    _check_auth(authorization)
    p = store.create_profile(body)
    return {"code": 0, "msg": "success", "data": {"profile_id": p.id}}


@app.get("/api/v1/browser/start")
async def browser_start(
    user_id: str = Query(..., description="Profile id"),
    authorization: str | None = None,
    headless: bool = False,
) -> dict:
    _check_auth(authorization)
    profile = store.get_profile(user_id)
    if not profile:
        return {"code": -1, "msg": "profile not found"}
    data = await browser.start_profile(profile, headless=headless)
    return {"code": 0, "msg": "success", "data": data}


@app.get("/api/v1/browser/stop")
async def browser_stop(
    user_id: str = Query(...),
    authorization: str | None = None,
) -> dict:
    _check_auth(authorization)
    ok = await browser.stop_profile(user_id)
    if not ok:
        return {"code": -1, "msg": "profile not running"}
    return {"code": 0, "msg": "success"}


@app.get("/api/v1/browser/probe")
async def browser_probe(
    user_id: str = Query(...),
    authorization: str | None = None,
) -> dict:
    _check_auth(authorization)
    profile = store.get_profile(user_id)
    if not profile:
        return {"code": -1, "msg": "profile not found"}
    data = await browser.probe_profile(user_id)
    if data is None:
        return {"code": -1, "msg": "profile not running"}
    return {"code": 0, "msg": "success", "data": {"probe": data, "expected": profile.fingerprint.model_dump()}}


@app.get("/api/profiles")
def api_list_profiles() -> list[dict]:
    return [p.model_dump() for p in store.list_profiles()]


@app.get("/api/profiles/{profile_id}")
def api_get_profile(profile_id: str) -> dict:
    p = store.get_profile(profile_id)
    if not p:
        raise HTTPException(404, "profile not found")
    return p.model_dump()


@app.post("/api/profiles")
def api_create_profile(body: ProfileCreate) -> dict:
    p = store.create_profile(body)
    return p.model_dump()


@app.patch("/api/profiles/{profile_id}")
def api_update_profile(profile_id: str, body: ProfileUpdate) -> dict:
    p = store.update_profile(profile_id, body)
    if not p:
        raise HTTPException(404, "profile not found")
    return p.model_dump()


@app.delete("/api/profiles/{profile_id}")
def api_delete_profile(profile_id: str) -> dict:
    if not store.delete_profile(profile_id):
        raise HTTPException(404, "profile not found")
    return {"ok": True}


class GeoLookupBody(BaseModel):
    ip: str


@app.get("/api/platform-presets")
def platform_presets() -> dict:
    return PRESETS


@app.post("/api/geo/lookup")
def geo_lookup(body: GeoLookupBody) -> dict:
    try:
        return {"code": 0, "data": lookup_ip(body.ip)}
    except ValueError as exc:
        return {"code": -1, "msg": str(exc)}


@app.post("/api/profiles/{profile_id}/apply-ip")
def apply_ip_to_profile(profile_id: str, body: GeoLookupBody | None = None) -> dict:
    p = store.get_profile(profile_id)
    if not p:
        raise HTTPException(404, "profile not found")
    ip = body.ip if body and body.ip else ""
    try:
        resolved = resolve_ip_for_profile(p, ip_override=ip)
        fp = apply_ip_hints(p.fingerprint, resolved)
    except ValueError as exc:
        return {"code": -1, "msg": str(exc)}
    updated = store.update_profile(profile_id, ProfileUpdate(fingerprint=fp))
    return {"code": 0, "data": updated.model_dump() if updated else {}}


@app.post("/api/geo/validate-cookies")
def validate_cookies(body: dict) -> dict:
    from app.cookies_util import parse_cookies_json

    raw = body.get("cookies_json", "")
    try:
        items = parse_cookies_json(raw)
        return {"code": 0, "count": len(items)}
    except (ValueError, json.JSONDecodeError) as exc:
        return {"code": -1, "msg": str(exc)}


if WEB_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")
