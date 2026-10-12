from __future__ import annotations

import re

from app.ip_lookup import lookup_ip
from app.models import FingerprintConfig, Profile


_IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def resolve_ip_for_profile(profile: Profile, ip_override: str = "") -> str:
    if ip_override.strip():
        return ip_override.strip()
    host = profile.proxy.host.strip()
    if _IP_RE.match(host):
        return host
    hint = profile.fingerprint.ip_lookup_hint.strip()
    if _IP_RE.match(hint):
        return hint
    raise ValueError("请填写 IP 查询地址，或代理 host 使用纯 IP，或在指纹页填写 IP 提示")


def apply_ip_hints(fp: FingerprintConfig, ip: str) -> FingerprintConfig:
    data = lookup_ip(ip)
    updates = fp.model_dump()
    updates["ip_lookup_hint"] = data["ip"]
    if fp.timezone_mode == "based_on_ip" and data.get("timezone_id"):
        updates["timezone_id"] = data["timezone_id"]
    if fp.language_mode == "based_on_ip":
        updates["languages"] = data["languages"]
        updates["locale"] = data["locale"]
    if fp.geolocation_mode == "based_on_ip":
        updates["geolocation_lat"] = data["geolocation_lat"]
        updates["geolocation_lon"] = data["geolocation_lon"]
    elif fp.geolocation_mode == "off":
        updates["geolocation_lat"] = None
        updates["geolocation_lon"] = None
    return FingerprintConfig.model_validate(updates)
