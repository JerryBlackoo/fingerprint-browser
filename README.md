# Fingerprint Browser（开源多环境）

在理解本机 [AdsPower](../adspower-fingerprint-learning/README.md) 架构的基础上，实现的**同类能力**产品：

- 多 Profile 隔离（独立 `user-data-dir`）
- 每环境代理（HTTP / SOCKS5）
- 可配置 UA、时区、语言、视口、WebGL 字符串、Canvas 噪声（**页面 JS 层**）
- Web UI「环境管理」+ **AdsPower 风格 Local API** 子集（`/status`、`/api/v1/browser/start` 等）

## 与 AdsPower 的差异（必读）

| 能力 | AdsPower | 本项目 |
|------|----------|--------|
| 内核 | 定制 SunBrowser（Blink/C++ patch） | 官方 Playwright Chromium |
| 指纹强度 | 商业级、持续对抗检测 | 教学/自动化够用，**弱于**商业内核 |
| 实现来源 | 闭源 | 开源，不复制其二进制 |

不会、也不能通过逆向其 `SunBrowser` 做 1:1 克隆；若需更强指纹，可后续接入 [Camoufox](https://github.com/daijro/camoufox) 等开源内核。

## 安装与运行

```bash
cd /home/jerry/Projects/fingerprint-browser
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 可选：与 AdsPower 一样用 Bearer 保护 API
# export FB_API_KEY=your_secret

uvicorn app.main:app --host 127.0.0.1 --port 50326
```

浏览器打开：**http://127.0.0.1:50326/**

数据目录：`~/.local/share/fingerprint-browser/`

## API 示例

```bash
curl -s http://127.0.0.1:50326/status

curl -s -X POST http://127.0.0.1:50326/api/profiles \
  -H 'Content-Type: application/json' \
  -d '{"name":"US-1","proxy":{"mode":"socks5","host":"127.0.0.1","port":7890}}'

curl -s 'http://127.0.0.1:50326/api/v1/browser/start?user_id=PROFILE_ID'
```

## 测试

服务启动后：

```bash
python scripts/verify_e2e.py
# 可选：FB_BASE=http://127.0.0.1:50326 FB_API_KEY=...
```

通过即表示：API、Web UI、headless 启停、指纹 probe（webdriver/platform/timezone/webgl/canvas）均正常。

## 架构

```text
Web UI (web/)  →  FastAPI (app/main.py)  →  Playwright persistent context
                      ↓
              profiles.json + user_data/<id>/
```
