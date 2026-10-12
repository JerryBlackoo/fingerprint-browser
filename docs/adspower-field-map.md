# AdsPower 字段 ↔ 本产品（已支持）

| AdsPower | 本产品 UI |
|----------|-----------|
| 基础：名称 / 备注 / UA / OS | **基础** |
| 标签页 URL | **基础** → 启动 URL；或 **账号** 平台预设 |
| 代理 | **代理** |
| Cookie / 合并 | **账号** → Cookie JSON + 合并勾选 |
| 账号平台 | **账号** → 平台 + 账号密码（本地存储） |
| WebRTC / 时区 / 语言 / 地理 | **指纹**（含「基于 IP」） |
| 分辨率 / Canvas / Audio / ClientRects | **指纹** |
| 字体 / WebGL / WebGPU | **指纹** |
| CPU / 内存 | **高级** |

## 基于 IP

1. **代理** 填纯 IP 的 host，或在 **指纹** 填「IP 查询」  
2. 时区/语言/地理 选 **基于 IP**  
3. 点 **根据 IP 填充**（已保存环境会写回 profile）  
4. 启动浏览器时也会按 IP 再算一次

## Cookie 格式

```json
[
  {
    "name": "SID",
    "value": "xxx",
    "domain": ".google.com",
    "path": "/",
    "secure": true,
    "httpOnly": true
  }
]
```

支持 `expirationDate`（Chrome 扩展导出字段名）。

## API

- `POST /api/geo/lookup` `{"ip":"8.8.8.8"}`
- `POST /api/profiles/{id}/apply-ip` `{"ip":"..."}`  
- `POST /api/geo/validate-cookies` `{"cookies_json":"[...]"}`
