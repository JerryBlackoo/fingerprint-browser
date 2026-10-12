"""Resolve timezone / geo / language hints from a public IP (ip-api.com, no key)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

_COUNTRY_LANG: dict[str, list[str]] = {
    "US": ["en-US", "en"],
    "GB": ["en-GB", "en"],
    "DE": ["de-DE", "de"],
    "FR": ["fr-FR", "fr"],
    "JP": ["ja-JP", "ja"],
    "CN": ["zh-CN", "zh"],
}


def lookup_ip(ip: str) -> dict:
    ip = ip.strip()
    if not ip:
        raise ValueError("ip is required")
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,timezone,lat,lon,query"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if data.get("status") != "success":
        raise ValueError(data.get("message") or "lookup failed")
    cc = data.get("countryCode") or "US"
    langs = _COUNTRY_LANG.get(cc, ["en-US", "en"])
    return {
        "ip": data.get("query", ip),
        "country": data.get("country"),
        "country_code": cc,
        "timezone_id": data.get("timezone"),
        "geolocation_lat": data.get("lat"),
        "geolocation_lon": data.get("lon"),
        "languages": langs,
        "locale": langs[0],
    }
