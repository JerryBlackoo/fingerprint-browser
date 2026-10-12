from __future__ import annotations

PRESETS: dict[str, dict[str, str]] = {
    "": {"label": "无", "login_url": ""},
    "google": {
        "label": "Google",
        "login_url": "https://accounts.google.com/",
    },
    "facebook": {
        "label": "Facebook",
        "login_url": "https://www.facebook.com/",
    },
    "amazon": {
        "label": "Amazon",
        "login_url": "https://www.amazon.com/ap/signin",
    },
    "twitter": {
        "label": "X (Twitter)",
        "login_url": "https://x.com/i/flow/login",
    },
    "custom": {"label": "自定义", "login_url": ""},
}


def default_startup_url(platform: str, current: str) -> str:
    if current.strip():
        return current
    return PRESETS.get(platform, {}).get("login_url", "")
