const rows = document.getElementById("rows");
const dlg = document.getElementById("dlg");
const form = document.getElementById("form");
const dlgTitle = document.getElementById("dlgTitle");
const btnSave = document.getElementById("btnSave");

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.querySelector(`[data-panel="${btn.dataset.tab}"]`).classList.add("active");
  });
});

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function splitList(s) {
  return String(s || "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

function formToBody() {
  const fd = new FormData(form);
  const lat = fd.get("geolocation_lat");
  const lon = fd.get("geolocation_lon");
  const accUser = fd.get("acc_username") || "";
  const accPass = fd.get("acc_password") || "";
  const platform = fd.get("account_platform") || "";
  const accounts =
    accUser || accPass
      ? [
          {
            platform: platform || "custom",
            username: accUser,
            password: accPass,
            login_url: fd.get("acc_login_url") || "",
          },
        ]
      : [];

  return {
    name: fd.get("name"),
    group: fd.get("group") || "default",
    remark: fd.get("remark") || "",
    startup_url: fd.get("startup_url") || "",
    account_platform: platform,
    platform_accounts: accounts,
    cookies_json: fd.get("cookies_json") || "",
    cookie_merge: fd.get("cookie_merge") === "on",
    proxy: {
      mode: fd.get("proxy_mode"),
      host: fd.get("proxy_host") || "",
      port: Number(fd.get("proxy_port") || 0),
      username: fd.get("proxy_username") || "",
      password: fd.get("proxy_password") || "",
    },
    fingerprint: {
      user_agent: fd.get("user_agent"),
      platform: fd.get("platform"),
      timezone_mode: fd.get("timezone_mode"),
      timezone_id: fd.get("timezone_id"),
      language_mode: fd.get("language_mode"),
      locale: fd.get("locale"),
      languages: splitList(fd.get("languages")),
      geolocation_mode: fd.get("geolocation_mode"),
      geolocation_lat: lat === "" || lat === null ? null : Number(lat),
      geolocation_lon: lon === "" || lon === null ? null : Number(lon),
      ip_lookup_hint: fd.get("ip_lookup_hint") || "",
      viewport_width: Number(fd.get("viewport_width") || 1920),
      viewport_height: Number(fd.get("viewport_height") || 1080),
      device_scale_factor: Number(fd.get("device_scale_factor") || 1),
      webrtc_policy: fd.get("webrtc_policy"),
      canvas_mode: fd.get("canvas_mode"),
      canvas_noise_seed: Number(fd.get("canvas_noise_seed") || 42),
      audio_mode: fd.get("audio_mode"),
      client_rects_mode: fd.get("client_rects_mode"),
      fonts_mode: fd.get("fonts_mode"),
      fonts_list: splitList(fd.get("fonts_list")),
      webgl_vendor: fd.get("webgl_vendor"),
      webgl_renderer: fd.get("webgl_renderer"),
      webgpu_mode: fd.get("webgpu_mode"),
      hardware_concurrency: Number(fd.get("hardware_concurrency") || 8),
      device_memory: Number(fd.get("device_memory") || 8),
    },
  };
}

function fillForm(p) {
  form.profile_id.value = p.id;
  form.name.value = p.name;
  form.group.value = p.group;
  form.remark.value = p.remark || "";
  form.startup_url.value = p.startup_url || "";
  form.account_platform.value = p.account_platform || "";
  const acc = (p.platform_accounts && p.platform_accounts[0]) || {};
  form.acc_username.value = acc.username || "";
  form.acc_password.value = acc.password || "";
  form.acc_login_url.value = acc.login_url || "";
  form.cookies_json.value = p.cookies_json || "";
  form.cookie_merge.checked = p.cookie_merge !== false;
  form.platform.value = p.fingerprint.platform;
  form.user_agent.value = p.fingerprint.user_agent;
  form.proxy_mode.value = p.proxy.mode;
  form.proxy_host.value = p.proxy.host || "";
  form.proxy_port.value = p.proxy.port || "";
  form.proxy_username.value = p.proxy.username || "";
  form.proxy_password.value = p.proxy.password || "";
  const f = p.fingerprint;
  form.timezone_mode.value = f.timezone_mode || "manual";
  form.timezone_id.value = f.timezone_id;
  form.language_mode.value = f.language_mode || "manual";
  form.locale.value = f.locale;
  form.languages.value = (f.languages || []).join(",");
  form.geolocation_mode.value = f.geolocation_mode || "manual";
  form.geolocation_lat.value = f.geolocation_lat ?? "";
  form.geolocation_lon.value = f.geolocation_lon ?? "";
  form.ip_lookup_hint.value = f.ip_lookup_hint || "";
  form.viewport_width.value = f.viewport_width;
  form.viewport_height.value = f.viewport_height;
  form.device_scale_factor.value = f.device_scale_factor;
  form.webrtc_policy.value = f.webrtc_policy;
  form.canvas_mode.value = f.canvas_mode || "noise";
  form.canvas_noise_seed.value = f.canvas_noise_seed;
  form.audio_mode.value = f.audio_mode || "real";
  form.client_rects_mode.value = f.client_rects_mode || "noise";
  form.fonts_mode.value = f.fonts_mode || "default";
  form.fonts_list.value = (f.fonts_list || []).join(",");
  form.webgl_vendor.value = f.webgl_vendor;
  form.webgl_renderer.value = f.webgl_renderer;
  form.webgpu_mode.value = f.webgpu_mode || "based_on_webgl";
  form.hardware_concurrency.value = f.hardware_concurrency;
  form.device_memory.value = f.device_memory;
}

function openNew() {
  form.reset();
  form.profile_id.value = "";
  form.group.value = "default";
  form.cookie_merge.checked = true;
  dlgTitle.textContent = "新建环境";
  btnSave.textContent = "创建";
  dlg.showModal();
}

async function openEdit(id) {
  const res = await fetch(`/api/profiles/${id}`);
  if (!res.ok) return alert("读取环境失败");
  fillForm(await res.json());
  dlgTitle.textContent = "编辑环境";
  btnSave.textContent = "保存";
  dlg.showModal();
}

async function load() {
  const res = await fetch("/api/profiles");
  const list = await res.json();
  rows.innerHTML = list
    .map(
      (p) => `
    <tr>
      <td>${escapeHtml(p.name)}</td>
      <td><code>${p.id}</code></td>
      <td>${escapeHtml(p.group)}</td>
      <td>${p.proxy.mode === "none" ? "—" : `${p.proxy.mode}://${p.proxy.host}:${p.proxy.port}`}</td>
      <td class="actions">
        <button type="button" data-edit="${p.id}">编辑</button>
        <button type="button" data-open="${p.id}">打开</button>
        <button type="button" data-stop="${p.id}">关闭</button>
      </td>
    </tr>`
    )
    .join("");
}

rows.addEventListener("click", async (e) => {
  const edit = e.target.closest("[data-edit]");
  const open = e.target.closest("[data-open]");
  const stop = e.target.closest("[data-stop]");
  if (edit) return openEdit(edit.getAttribute("data-edit"));
  if (open) {
    const id = open.getAttribute("data-open");
    const r = await fetch(`/api/v1/browser/start?user_id=${encodeURIComponent(id)}`);
    const j = await r.json();
    alert(j.code === 0 ? "已启动浏览器窗口" : j.msg || JSON.stringify(j));
  }
  if (stop) {
    const id = stop.getAttribute("data-stop");
    const r = await fetch(`/api/v1/browser/stop?user_id=${encodeURIComponent(id)}`);
    const j = await r.json();
    alert(j.msg || JSON.stringify(j));
  }
});

document.getElementById("btnRefresh").onclick = load;
document.getElementById("btnNew").onclick = openNew;
document.getElementById("btnCancel").onclick = () => dlg.close();

document.getElementById("btnValidateCookies").onclick = async () => {
  const cookies_json = form.cookies_json.value;
  const r = await fetch("/api/geo/validate-cookies", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cookies_json }),
  });
  const j = await r.json();
  alert(j.code === 0 ? `Cookie 有效，共 ${j.count} 条` : j.msg || JSON.stringify(j));
};

document.getElementById("btnApplyIp").onclick = async () => {
  const ip =
    form.ip_lookup_hint.value.trim() ||
    form.proxy_host.value.trim();
  if (!ip) {
    alert("请填写 IP 查询地址或代理 Host（纯 IP）");
    return;
  }
  const pid = form.profile_id.value;
  if (pid) {
    const r = await fetch(`/api/profiles/${pid}/apply-ip`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ip }),
    });
    const j = await r.json();
    if (j.code !== 0) return alert(j.msg || JSON.stringify(j));
    fillForm(j.data);
    alert("已写入 profile 并填充时区/语言/经纬度");
    return;
  }
  const r = await fetch("/api/geo/lookup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ip }),
  });
  const j = await r.json();
  if (j.code !== 0) return alert(j.msg || JSON.stringify(j));
  const d = j.data;
  form.ip_lookup_hint.value = d.ip;
  if (form.timezone_mode.value === "based_on_ip") form.timezone_id.value = d.timezone_id;
  if (form.language_mode.value === "based_on_ip") {
    form.languages.value = d.languages.join(",");
    form.locale.value = d.locale;
  }
  if (form.geolocation_mode.value === "based_on_ip") {
    form.geolocation_lat.value = d.geolocation_lat;
    form.geolocation_lon.value = d.geolocation_lon;
  }
  alert(`已根据 ${d.ip}（${d.country}）填充表单，保存后生效`);
};

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = formToBody();
  const id = form.profile_id.value;
  const url = id ? `/api/profiles/${id}` : "/api/profiles";
  const method = id ? "PATCH" : "POST";
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    alert(await res.text());
    return;
  }
  dlg.close();
  load();
});

load();
