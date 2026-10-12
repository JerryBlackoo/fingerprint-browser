from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from playwright.async_api import BrowserContext, Playwright, async_playwright

from app.cookies_util import parse_cookies_json
from app.fingerprint import build_init_script
from app.models import Profile, ProxyConfig
from app.platform_presets import default_startup_url
from app.profile_geo import apply_ip_hints, resolve_ip_for_profile
from app.store import profile_data_dir


@dataclass
class RunningBrowser:
    profile_id: str
    playwright: Playwright
    context: BrowserContext


_lock = asyncio.Lock()
_running: dict[str, RunningBrowser] = {}


def _proxy_for_playwright(proxy: ProxyConfig) -> dict[str, str] | None:
    if proxy.mode == "none" or not proxy.host or not proxy.port:
        return None
    scheme = "socks5" if proxy.mode == "socks5" else "http"
    server = f"{scheme}://{proxy.host}:{proxy.port}"
    out: dict[str, str] = {"server": server}
    if proxy.username:
        out["username"] = proxy.username
        out["password"] = proxy.password
    return out


def _profile_for_launch(profile: Profile) -> Profile:
    fp = profile.fingerprint
    needs_ip = (
        fp.timezone_mode == "based_on_ip"
        or fp.language_mode == "based_on_ip"
        or fp.geolocation_mode == "based_on_ip"
    )
    if needs_ip:
        try:
            ip = resolve_ip_for_profile(profile)
            fp = apply_ip_hints(fp, ip)
        except ValueError:
            pass
    if fp.geolocation_mode == "off":
        fp = fp.model_copy(update={"geolocation_lat": None, "geolocation_lon": None})
    startup = default_startup_url(profile.account_platform, profile.startup_url)
    return profile.model_copy(update={"fingerprint": fp, "startup_url": startup})


async def start_profile(profile: Profile, *, headless: bool = False) -> dict[str, Any]:
    async with _lock:
        if profile.id in _running:
            rb = _running[profile.id]
            return _session_info(rb)

        profile = _profile_for_launch(profile)
        pw = await async_playwright().start()
        fp = profile.fingerprint
        launch_args = ["--disable-blink-features=AutomationControlled"]
        if fp.webgpu_mode == "disabled":
            launch_args.append("--disable-features=WebGPU")
        if fp.webrtc_policy == "disable":
            launch_args.append("--force-webrtc-ip-handling-policy=disable_all")
        elif fp.webrtc_policy == "disable_non_proxied_udp":
            launch_args.append("--force-webrtc-ip-handling-policy=default_public_interface_only")

        geo = None
        if fp.geolocation_lat is not None and fp.geolocation_lon is not None:
            geo = {"latitude": fp.geolocation_lat, "longitude": fp.geolocation_lon}

        context = await pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_data_dir(profile.id)),
            headless=headless,
            channel=None,
            args=launch_args,
            user_agent=fp.user_agent,
            locale=fp.locale,
            timezone_id=fp.timezone_id,
            viewport={"width": fp.viewport_width, "height": fp.viewport_height},
            device_scale_factor=fp.device_scale_factor,
            proxy=_proxy_for_playwright(profile.proxy),
            geolocation=geo,
            permissions=["geolocation"] if geo else None,
        )
        await context.add_init_script(build_init_script(fp))
        cookie_note = ""
        if profile.cookies_json.strip():
            try:
                cookies = parse_cookies_json(profile.cookies_json)
                if cookies:
                    if not profile.cookie_merge:
                        await context.clear_cookies()
                    await context.add_cookies(cookies)
                    cookie_note = f"loaded {len(cookies)} cookies"
            except ValueError as exc:
                cookie_note = f"cookie error: {exc}"

        page = context.pages[0] if context.pages else await context.new_page()
        start_url = (profile.startup_url or "").strip() or "about:blank"
        await page.goto(start_url, wait_until="domcontentloaded")

        rb = RunningBrowser(profile_id=profile.id, playwright=pw, context=context)
        _running[profile.id] = rb
        info = _session_info(rb)
        if cookie_note:
            info["cookies"] = cookie_note
        return info


def _session_info(rb: RunningBrowser) -> dict[str, Any]:
    return {
        "profile_id": rb.profile_id,
        "running": True,
        "note": "Playwright persistent context; connect via same API or extend with CDP port.",
    }


async def stop_profile(profile_id: str) -> bool:
    async with _lock:
        rb = _running.pop(profile_id, None)
        if not rb:
            return False
        await rb.context.close()
        await rb.playwright.stop()
        return True


async def is_running(profile_id: str) -> bool:
    return profile_id in _running


_PROBE_JS = """
() => {
  const canvas = document.createElement('canvas');
  canvas.width = 200;
  canvas.height = 50;
  const ctx = canvas.getContext('2d');
  ctx.textBaseline = 'top';
  ctx.font = '14px Arial';
  ctx.fillText('fp-browser-probe', 2, 2);
  const canvasTail = canvas.toDataURL().slice(-32);
  const glCanvas = document.createElement('canvas');
  const gl = glCanvas.getContext('webgl');
  const VENDOR = 0x9245;
  const RENDERER = 0x9246;
  return {
    webdriver: navigator.webdriver,
    platform: navigator.platform,
    hardwareConcurrency: navigator.hardwareConcurrency,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    userAgent: navigator.userAgent,
    canvasTail,
    webglVendor: gl ? gl.getParameter(VENDOR) : null,
    webglRenderer: gl ? gl.getParameter(RENDERER) : null,
  };
}
"""


async def probe_profile(profile_id: str) -> dict[str, Any] | None:
    async with _lock:
        rb = _running.get(profile_id)
        if not rb:
            return None
        page = rb.context.pages[0] if rb.context.pages else await rb.context.new_page()
        return await page.evaluate(_PROBE_JS)


async def shutdown_all() -> None:
    async with _lock:
        ids = list(_running.keys())
    for pid in ids:
        await stop_profile(pid)
