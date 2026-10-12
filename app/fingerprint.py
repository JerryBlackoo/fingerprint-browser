"""In-page fingerprint hooks (JS layer). Kernel-level patches are out of scope."""

from __future__ import annotations

import json

from app.models import FingerprintConfig


def build_init_script(cfg: FingerprintConfig) -> str:
    langs = ", ".join(repr(x) for x in cfg.languages)
    seed = int(cfg.canvas_noise_seed)
    canvas_block = ""
    if cfg.canvas_mode == "noise":
        canvas_block = f"""
  const noise = (data, s) => {{
    for (let i = 0; i < data.length; i += 4) {{
      data[i] ^= (s * 2654435761 + i) & 3;
      data[i + 1] ^= (s + i * 7) & 3;
    }}
  }};
  const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
  HTMLCanvasElement.prototype.toDataURL = function(...args) {{
    const ctx = this.getContext('2d');
    if (ctx) {{
      try {{
        const img = ctx.getImageData(0, 0, this.width, this.height);
        noise(img.data, {seed});
        ctx.putImageData(img, 0, 0);
      }} catch (_) {{}}
    }}
    return origToDataURL.apply(this, args);
  }};"""

    audio_block = ""
    if cfg.audio_mode == "noise":
        audio_block = f"""
  const _seed = {seed};
  const origGetChannelData = AudioBuffer.prototype.getChannelData;
  AudioBuffer.prototype.getChannelData = function(ch) {{
    const data = origGetChannelData.call(this, ch);
    for (let i = 0; i < data.length; i += 97) {{
      data[i] += ((_seed + i) % 7) * 1e-7;
    }}
    return data;
  }};"""

    rects_block = ""
    if cfg.client_rects_mode == "noise":
        rects_block = f"""
  const _j = ({seed} % 97) * 0.0001;
  const _nudge = (r) => {{
    if (!r) return r;
    return DOMRect.fromRect({{
      x: r.x + _j, y: r.y + _j, width: r.width, height: r.height
    }});
  }};
  const _origGbcr = Element.prototype.getBoundingClientRect;
  Element.prototype.getBoundingClientRect = function() {{
    return _nudge(_origGbcr.call(this));
  }};"""

    fonts_block = ""
    if cfg.fonts_mode == "custom" and cfg.fonts_list:
        allowed = json.dumps(cfg.fonts_list)
        fonts_block = f"""
  const _allowed = new Set({allowed});
  if (document.fonts && document.fonts.check) {{
    const _origCheck = document.fonts.check.bind(document.fonts);
    document.fonts.check = (font, text) => {{
      const fam = String(font).replace(/^[0-9.]+px\\s+/i, '');
      const name = fam.replace(/['"]/g, '').split(',')[0].trim();
      if (name && !_allowed.has(name)) return false;
      return _origCheck(font, text);
    }};
  }}"""

    webgpu_block = ""
    if cfg.webgpu_mode == "disabled":
        webgpu_block = """
  try {
    Object.defineProperty(navigator, 'gpu', { get: () => undefined, configurable: true });
  } catch (_) {}"""

    return f"""
(() => {{
  const patch = (obj, key, val) => {{
    try {{
      Object.defineProperty(obj, key, {{ get: () => val, configurable: true }});
    }} catch (_) {{}}
  }};

  patch(navigator, 'webdriver', false);
  patch(navigator, 'platform', {cfg.platform!r});
  patch(navigator, 'hardwareConcurrency', {cfg.hardware_concurrency});
  patch(navigator, 'deviceMemory', {cfg.device_memory});
  patch(navigator, 'languages', [{langs}]);
  patch(navigator, 'language', {cfg.languages[0]!r});

  const origGetParameter = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = function(param) {{
    const UNMASKED_VENDOR_WEBGL = 0x9245;
    const UNMASKED_RENDERER_WEBGL = 0x9246;
    if (param === UNMASKED_VENDOR_WEBGL) return {cfg.webgl_vendor!r};
    if (param === UNMASKED_RENDERER_WEBGL) return {cfg.webgl_renderer!r};
    return origGetParameter.call(this, param);
  }};
  {canvas_block}
  {audio_block}
  {rects_block}
  {fonts_block}
  {webgpu_block}
}})();
"""
