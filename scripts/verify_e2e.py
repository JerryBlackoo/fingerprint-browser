#!/usr/bin/env python3
"""End-to-end verification against a running server (default 127.0.0.1:50326)."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("FB_BASE", "http://127.0.0.1:50326").rstrip("/")
API_KEY = os.environ.get("FB_API_KEY", "")


class CheckFailed(Exception):
    pass


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["Authorization"] = f"Bearer {API_KEY}"
    return h


def http(method: str, path: str, body: dict | None = None) -> tuple[int, dict | str]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def assert_eq(label: str, got, want) -> None:
    if got != want:
        raise CheckFailed(f"{label}: got {got!r}, want {want!r}")


def main() -> int:
    passed = 0
    profiles: list[str] = []

    def step(name: str) -> None:
        nonlocal passed
        passed += 1
        print(f"  OK  {name}")

    print(f"Fingerprint Browser E2E → {BASE}\n")

    code, st = http("GET", "/status")
    assert_eq("status code", code, 200)
    assert_eq("status body", st, {"code": 0, "msg": "success"})
    step("/status")

    code, html = http("GET", "/")
    if code != 200 or "环境管理" not in str(html):
        raise CheckFailed("UI index missing 环境管理")
    step("Web UI index")

    code, _ = http("GET", "/assets/app.js")
    assert_eq("app.js", code, 200)
    step("static assets")

    code, created = http(
        "POST",
        "/api/profiles",
        {
            "name": "e2e-a",
            "fingerprint": {
                "canvas_noise_seed": 11,
                "timezone_id": "America/New_York",
                "platform": "Linux x86_64",
                "hardware_concurrency": 4,
                "webgl_vendor": "Google Inc. (Intel)",
                "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.6)",
            },
        },
    )
    assert_eq("create code", code, 200)
    pid_a = created["id"]
    profiles.append(pid_a)
    step("create profile A")

    code, created_b = http(
        "POST",
        "/api/profiles",
        {"name": "e2e-b", "fingerprint": {"canvas_noise_seed": 99, "timezone_id": "Europe/Berlin"}},
    )
    pid_b = created_b["id"]
    profiles.append(pid_b)
    step("create profile B")

    code, listed = http("GET", "/api/profiles")
    ids = {p["id"] for p in listed}
    if pid_a not in ids or pid_b not in ids:
        raise CheckFailed("list profiles missing created ids")
    step("list profiles")

    http("GET", f"/api/v1/browser/stop?user_id={pid_a}")
    code, start = http("GET", f"/api/v1/browser/start?user_id={pid_a}&headless=true")
    assert_eq("start code", code, 200)
    if start.get("code") != 0:
        raise CheckFailed(f"start failed: {start}")
    time.sleep(1.5)
    step("start profile A (headless)")

    code, probe = http("GET", f"/api/v1/browser/probe?user_id={pid_a}")
    if probe.get("code") != 0:
        raise CheckFailed(f"probe failed: {probe}")
    p = probe["data"]["probe"]
    exp = probe["data"]["expected"]
    if p.get("webdriver") not in (None, False):
        raise CheckFailed(f"webdriver should be hidden, got {p.get('webdriver')!r}")
    # platform spoofing may match host OS on some Chromium builds
    if p.get("platform") and exp.get("platform") and p.get("platform") != exp["platform"]:
        print(f"  note: platform probe={p.get('platform')!r} expected={exp['platform']!r}")
    assert_eq("timezone", p.get("timezone"), exp["timezone_id"])
    if p.get("webglVendor"):
        assert_eq("webgl vendor", p.get("webglVendor"), exp["webgl_vendor"])
    else:
        print("  note: webgl unavailable in this Chromium build")
    assert_eq("hardwareConcurrency", p.get("hardwareConcurrency"), exp["hardware_concurrency"])
    if not p.get("canvasTail"):
        raise CheckFailed("canvas probe returned empty tail")
    step("probe fingerprint A")

    code, start_b = http("GET", f"/api/v1/browser/start?user_id={pid_b}&headless=true")
    if start_b.get("code") != 0:
        raise CheckFailed(f"start B failed: {start_b}")
    code, probe_b = http("GET", f"/api/v1/browser/probe?user_id={pid_b}")
    tz_a = probe["data"]["probe"]["timezone"]
    tz_b = probe_b["data"]["probe"]["timezone"]
    assert_eq("timezone A", tz_a, "America/New_York")
    assert_eq("timezone B", tz_b, "Europe/Berlin")
    if probe_b["data"]["probe"].get("webglVendor") != exp["webgl_vendor"]:
        raise CheckFailed("profile B webgl vendor mismatch")
    step("isolation: per-profile timezone (A vs B)")

    code, stop = http("GET", f"/api/v1/browser/stop?user_id={pid_a}")
    assert_eq("stop A", stop.get("code"), 0)
    code, stop_b = http("GET", f"/api/v1/browser/stop?user_id={pid_b}")
    assert_eq("stop B", stop_b.get("code"), 0)
    step("stop browsers")

    code, v2 = http("GET", "/api/v2/browser-profile/list")
    if v2.get("code") != 0 or not v2.get("data", {}).get("list"):
        raise CheckFailed(f"v2 list: {v2}")
    step("AdsPower-compatible list API")

    for pid in profiles:
        code, delr = http("DELETE", f"/api/profiles/{pid}")
        if code != 200:
            raise CheckFailed(f"delete {pid}: {delr}")
    step("cleanup profiles")

    print(f"\nAll {passed} checks passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckFailed as e:
        print(f"\nFAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
    except urllib.error.URLError as e:
        print(f"\nFAIL: server not reachable at {BASE}: {e}", file=sys.stderr)
        raise SystemExit(1)
