"""Normalize Cookie JSON (Chrome / AdsPower / EditThisCookie style) for Playwright."""

from __future__ import annotations

import json
import time
from typing import Any


def parse_cookies_json(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    if not raw:
        return []
    data = json.loads(raw)
    if isinstance(data, dict) and "cookies" in data:
        data = data["cookies"]
    if not isinstance(data, list):
        raise ValueError("Cookie JSON must be an array")
    return [normalize_cookie(c) for c in data if isinstance(c, dict)]


def normalize_cookie(c: dict[str, Any]) -> dict[str, Any]:
    name = c.get("name")
    value = c.get("value", "")
    domain = c.get("domain")
    if not name or not domain:
        raise ValueError(f"invalid cookie entry: {c!r}")
    out: dict[str, Any] = {
        "name": str(name),
        "value": str(value),
        "domain": str(domain),
        "path": c.get("path") or "/",
    }
    exp = c.get("expirationDate") or c.get("expires")
    if exp is not None:
        if isinstance(exp, (int, float)) and exp > 0:
            if exp > 1e12:
                exp = exp / 1000
            if exp < time.time():
                out["expires"] = int(time.time()) + 86400
            else:
                out["expires"] = int(exp)
    for key in ("httpOnly", "secure"):
        if key in c:
            out[key] = bool(c[key])
    ss = c.get("sameSite")
    if ss in ("Strict", "Lax", "None"):
        out["sameSite"] = ss
    elif isinstance(ss, str) and ss.lower() in ("strict", "lax", "none"):
        out["sameSite"] = ss.capitalize() if ss.lower() != "none" else "None"
    return out
