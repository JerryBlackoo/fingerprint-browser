from __future__ import annotations

from pydantic import BaseModel, Field


class ProxyConfig(BaseModel):
    mode: str = Field(default="none", description="none | http | socks5")
    host: str = ""
    port: int = 0
    username: str = ""
    password: str = ""


class PlatformAccount(BaseModel):
    platform: str = Field(default="custom", description="google | facebook | amazon | custom")
    username: str = ""
    password: str = ""
    login_url: str = ""


class FingerprintConfig(BaseModel):
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    platform: str = "Win32"
    languages: list[str] = Field(default_factory=lambda: ["en-US", "en"])
    timezone_id: str = "America/New_York"
    locale: str = "en-US"
    timezone_mode: str = Field(default="manual", description="manual | based_on_ip")
    language_mode: str = Field(default="manual", description="manual | based_on_ip")
    geolocation_mode: str = Field(default="manual", description="manual | based_on_ip | off")
    viewport_width: int = 1920
    viewport_height: int = 1080
    device_scale_factor: float = 1.0
    hardware_concurrency: int = 8
    device_memory: float = 8.0
    webgl_vendor: str = "Google Inc. (Intel)"
    webgl_renderer: str = "ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.6)"
    canvas_mode: str = Field(default="noise", description="real | noise")
    canvas_noise_seed: int = 42
    audio_mode: str = Field(default="real", description="real | noise")
    client_rects_mode: str = Field(default="noise", description="real | noise")
    fonts_mode: str = Field(default="default", description="default | custom")
    fonts_list: list[str] = Field(
        default_factory=lambda: [
            "Arial",
            "Helvetica",
            "Times New Roman",
            "Courier New",
            "Verdana",
            "Georgia",
        ]
    )
    webgpu_mode: str = Field(default="based_on_webgl", description="based_on_webgl | real | disabled")
    webrtc_policy: str = Field(
        default="disable_non_proxied_udp",
        description="default | disable | disable_non_proxied_udp",
    )
    geolocation_lat: float | None = None
    geolocation_lon: float | None = None
    ip_lookup_hint: str = Field(default="", description="IP used for last based_on_ip fill")


class Profile(BaseModel):
    id: str
    name: str
    group: str = "default"
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    fingerprint: FingerprintConfig = Field(default_factory=FingerprintConfig)
    remark: str = ""
    startup_url: str = ""
    account_platform: str = Field(default="", description="Preset: google, facebook, etc.")
    platform_accounts: list[PlatformAccount] = Field(default_factory=list)
    cookies_json: str = Field(default="", description="Raw JSON array of cookies")
    cookie_merge: bool = Field(default=True, description="Merge on start vs replace context cookies")


class ProfileCreate(BaseModel):
    name: str
    group: str = "default"
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    fingerprint: FingerprintConfig = Field(default_factory=FingerprintConfig)
    remark: str = ""
    startup_url: str = ""
    account_platform: str = ""
    platform_accounts: list[PlatformAccount] = Field(default_factory=list)
    cookies_json: str = ""
    cookie_merge: bool = True


class ProfileUpdate(BaseModel):
    name: str | None = None
    group: str | None = None
    proxy: ProxyConfig | None = None
    fingerprint: FingerprintConfig | None = None
    remark: str | None = None
    startup_url: str | None = None
    account_platform: str | None = None
    platform_accounts: list[PlatformAccount] | None = None
    cookies_json: str | None = None
    cookie_merge: bool | None = None
