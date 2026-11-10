"use strict";
(function () {
  const TOKEN = document.querySelector('meta[name="sentinel-token"]').content;
  const $ = (id) => document.getElementById(id);
  const STATUSES = ["LEAK", "ERROR", "INCONCLUSIVE", "BLOCKED", "SKIPPED"];
  const LABEL = { LEAK: "Leak", ERROR: "Error", INCONCLUSIVE: "Inconclusive", BLOCKED: "Blocked",
                  SKIPPED: "Skipped" };
  const VERDICT = { PASS: "PASS — everything that ran was blocked",
                    FAIL: "FAIL — at least one attack got through",
                    INCOMPLETE: "INCOMPLETE — some checks proved nothing",
                    EMPTY: "Nothing ran" };
  // form field id -> key in a config's settings (see settings_of() in server.py)
  const TARGET_FIELDS = ["host", "port", "scheme", "base_path", "frontend_host", "frontend_port", "api_path"];
  const FLOW_FIELDS = { fs_login: "login", fs_register: "register", fs_upload: "upload",
                        fs_resource: "resource", fs_username_field: "username_field",
                        fs_password_field: "password_field", fs_upload_field: "upload_field",
                        fs_token_json_path: "token_json_path", fs_auth_header: "auth_header" };
  let defaults = null, filter = "ALL", flowFilter = null, lastRun = null, timer = null;

  // ---- tiny DOM helper: text is always set as text, never parsed as HTML ----
  function el(tag, attrs, ...kids) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "class") n.className = v; else if (k === "text") n.textContent = v;
      else n.setAttribute(k, v);
    }
    for (const k of kids) if (k != null) n.append(k);
    return n;
  }

  async function api(path, body) {
    const opt = { headers: { "X-Sentinel-Token": TOKEN }, cache: "no-store" };
    if (body !== undefined) {
      opt.method = "POST";
      opt.headers["Content-Type"] = "application/json";
      opt.body = JSON.stringify(body);
    }
    const r = await fetch(path, opt);
    let data = {};
    try { data = await r.json(); } catch (e) { /* non-JSON error */ }
    if (!r.ok) throw new Error(data.error || ("HTTP " + r.status));
    return data;
  }

  // ---- form -----------------------------------------------------------------
  const checked = (sel) => [...document.querySelectorAll(sel + " input:checked")].map((c) => c.value);
  const val = (id) => $(id).value.trim();

  function form() {
    return {
      mode: $("mode").value, config: $("config").value,
      host: val("host"), port: val("port"), scheme: $("scheme").value, base_path: val("base_path"),
      frontend_host: val("frontend_host"), frontend_port: val("frontend_port"),
      api_path: val("api_path"), via_frontend: $("via_frontend").checked,
      flows: checked("#flows"), suites: checked("#suites"),
      overrides: {
        endpoints: { login: val("fs_login"), register: val("fs_register"),
                     upload: val("fs_upload"), resource: val("fs_resource") },
        fields: { username: val("fs_username_field"), password: val("fs_password_field"),
                  upload_file: val("fs_upload_field") },
        token_json_path: val("fs_token_json_path"), auth_header: val("fs_auth_header"),
        users: { user: { username: val("fs_user"), password: $("fs_pass").value, id: val("fs_uid") },
                 admin: { username: val("fs_admin_user"), password: $("fs_admin_pass").value } },
        media_upload: $("fs_media_upload").checked,
      },
    };
  }

  function preview() {
    const f = form();
    const fe = f.frontend_port ? "http://" + (f.frontend_host || f.host || "…") + ":" + f.frontend_port : "";
    const viaFe = f.via_frontend && fe;
    $("urlPreview").textContent = viaFe ? fe + f.api_path + "  (through the front end)"
      : f.scheme + "://" + (f.host || "…") + ":" + (f.port || "…") + f.base_path;
    $("fePreview").textContent = fe;
    $("fePreviewWrap").hidden = !fe;
    $("via_frontend").disabled = !f.frontend_port;
    if (!f.frontend_port) $("via_frontend").checked = false;
    $("apiPathField").hidden = !$("via_frontend").checked;
  }

  function applyConfig() {
    const t = defaults.config_targets[$("config").value] || {};
    if (t.error) { $("formError").textContent = t.error; return; }
    $("formError").textContent = "";
    for (const id of TARGET_FIELDS) $(id).value = t[id] === undefined || t[id] === null ? "" : t[id];
    $("scheme").value = t.scheme || "http";
    for (const [id, key] of Object.entries(FLOW_FIELDS)) $(id).value = t[key] || "";
    $("fs_user").value = t.user.username; $("fs_pass").value = t.user.password;
    $("fs_uid").value = t.user.id; $("fs_admin_user").value = t.admin.username;
    $("fs_admin_pass").value = t.admin.password;
    $("fs_media_upload").checked = !!t.media_upload;
    $("via_frontend").checked = false;
    preview();
  }

  function modeChanged() {
    const http = $("mode").value === "http";
    $("httpFields").hidden = !http; $("settings").hidden = !http;
    $("refHint").hidden = http; $("check").hidden = !http;
    $("preflight").replaceChildren();
  }

  function checklist(box, items, prefix) {
    box.replaceChildren(...items.map((s) => {
      const key = s.key || s.name, id = prefix + key;
      return el("label", { class: "suite", for: id },
        el("input", { type: "checkbox", id, value: key, checked: "" }),
        el("span", {}, el("b", { text: (s.label || s.name) + " (" + s.count + ")" }),
           el("small", { text: s.info })));
    }));
  }

  function fillConfigs(selected) {
    const cfg = $("config");
    cfg.replaceChildren(el("option", { value: "", text: "(built-in defaults)" }),
      ...defaults.configs.map((c) => el("option", { value: c, text: c })));
    cfg.value = selected;
  }

  function buildForm() {
    fillConfigs(defaults.config);
    checklist($("flows"), defaults.flows, "flow-");
    checklist($("suites"), defaults.suites, "suite-");
    applyConfig();
    modeChanged();
  }

  // ---- rendering --------------------------------------------------------------
  function renderFilters(counts, total) {
    const items = [["ALL", "All", total]].concat(STATUSES.map((s) => [s, LABEL[s], counts[s] || 0]));
    $("filters").replaceChildren(...items.map(([key, label, n]) => {
      const b = el("button", { type: "button", class: "chip", role: "tab",
                               "aria-selected": String(filter === key), text: label + " " + n });
      b.addEventListener("click", () => { filter = key; render(lastRun); });
      return b;
    }));
  }

  function renderFlows(run) {
    const flows = run.by_flow || [];
    $("flowPanel").hidden = !flows.length;
    $("byFlow").replaceChildren(...flows.map((f) => {
      const c = f.counts, ran = f.ran;
      const state = c.LEAK || c.ERROR ? "LEAK" : c.INCONCLUSIVE ? "INCONCLUSIVE" : ran ? "BLOCKED" : "SKIPPED";
      const bar = el("div", { class: "fbar" });
      for (const s of ["BLOCKED", "LEAK", "INCONCLUSIVE", "ERROR", "SKIPPED"]) {
        if (c[s]) { const seg = el("span", { class: "seg " + s }); seg.style.flexGrow = String(c[s]); bar.append(seg); }
      }
      const parts = [c.BLOCKED + " blocked"];
      if (c.LEAK) parts.push(c.LEAK + " leak" + (c.LEAK > 1 ? "s" : ""));
      if (c.INCONCLUSIVE) parts.push(c.INCONCLUSIVE + " inconclusive");
      if (c.ERROR) parts.push(c.ERROR + " error" + (c.ERROR > 1 ? "s" : ""));
      if (c.SKIPPED) parts.push(c.SKIPPED + " skipped");
      const card = el("button", { type: "button", class: "fcard " + state,
                                  "aria-pressed": String(flowFilter === f.flow) },
        el("span", { class: "fname", text: f.label }),
        el("span", { class: "fscore", text: ran ? c.BLOCKED + "/" + ran : "–" }),
        bar, el("span", { class: "fdetail", text: parts.join(" · ") }));
      card.addEventListener("click", () => {
        flowFilter = flowFilter === f.flow ? null : f.flow; render(lastRun);
      });
      return card;
    }));
  }

  function renderRows(findings) {
    const order = Object.fromEntries(STATUSES.map((s, i) => [s, i]));
    const rows = findings.map((f, i) => [f, i])
      .filter(([f]) => (filter === "ALL" || f.status === filter) && (!flowFilter || f.flow === flowFilter))
      .sort((a, b) => (order[a[0].status] - order[b[0].status]) || (a[1] - b[1]));
    $("results").tBodies[0].replaceChildren(...rows.map(([f]) => {
      const what = el("td", {}, el("div", { text: f.desc }));
      if (f.detail) what.append(el("div", { class: "detail", text: f.detail }));
      if (f.fix) what.append(el("div", { class: "fix" }, el("b", { text: "Fix: " }), f.fix));
      return el("tr", {},
        el("td", {}, el("span", { class: "badge " + f.status, text: LABEL[f.status] })),
        el("td", { class: "id" }, f.id, el("small", { text: f.flow_label || f.suite || f.category })),
        what);
    }));
    $("empty").hidden = rows.length > 0;
    $("empty").textContent = findings.length ? "No checks match this filter."
                                              : "Results appear here as each check finishes.";
  }

  function render(run) {
    lastRun = run;
    const running = !!run && run.status === "running";
    $("start").hidden = running; $("stop").hidden = !running; $("check").disabled = running;
    const pill = $("pill");
    const state = run ? run.status : "idle";
    pill.className = "pill " + state;
    pill.textContent = { idle: "Idle", running: "Running…", done: "Finished", stopped: "Stopped",
                         error: "Runner error" }[state] || state;
    if (!run) { renderFilters({}, 0); renderRows([]); return; }

    const s = run.summary, c = s.counts;
    for (const k of Object.keys(LABEL)) $("n" + k).textContent = c[k] || 0;
    $("score").textContent = s.ran ? s.score : "–";
    const v = $("verdict");
    if (running) { v.className = "verdict none"; v.textContent = "Running — score so far"; }
    else { v.className = "verdict " + s.verdict; v.textContent = VERDICT[s.verdict] || s.verdict; }
    const bits = [run.target + (run.via_frontend ? " (via the front end)" : "")];
    if (run.frontend && !run.via_frontend) bits.push("front end " + run.frontend);
    bits.push(run.flows.length + " flow(s)", "coverage " + s.coverage + "%", run.elapsed + "s");
    if (run.requests) bits.push(run.requests + " requests");
    $("meta").textContent = bits.join(" · ");

    const pct = run.total ? Math.round(100 * run.done / run.total) : 0;
    $("bar").style.width = pct + "%";
    $("progress").setAttribute("aria-valuenow", String(pct));
    let text = run.done + " / " + run.total + " checks";
    if (running && run.current) text += " — now: " + run.current.id + " " + run.current.desc;
    if (run.status === "stopped") text += " — stopped before the end";
    if (run.status === "error") text += " — the runner failed: " + run.error;
    if (run.status === "done") text += " — finished " + new Date(run.finished).toLocaleTimeString();
    $("progressText").textContent = text;
    $("notes").replaceChildren(...(run.notes || []).map((n) => el("li", { text: n })));

    renderFlows(run);
    renderFilters(c, run.findings.length);
    renderRows(run.findings);
    $("download").hidden = running;
  }

  function renderHistory(history) {
    const box = $("history");
    if (!history.length) { box.replaceChildren(el("li", { class: "hint", text: "None yet." })); return; }
    box.replaceChildren(...history.map((h) => el("li", {},
      el("span", { class: "hs", text: String(h.score) }),
      el("span", { class: "badge " + ({ PASS: "BLOCKED", FAIL: "LEAK" }[h.verdict] || "INCONCLUSIVE"),
                   text: h.verdict }),
      el("span", { text: h.counts.BLOCKED + " blocked · " + h.counts.LEAK + " leaks · " +
                         h.counts.INCONCLUSIVE + " inconclusive · coverage " + h.coverage + "%" }),
      el("span", { class: "ht", text: h.target + " · " + new Date(h.when).toLocaleString() }))));
  }

  // ---- polling ----------------------------------------------------------------
  async function poll() {
    clearTimeout(timer);
    let delay = 3000;
    try {
      const st = await api("/api/state");
      render(st.run); renderHistory(st.history);
      if (st.run && st.run.status === "running") delay = 600;
    } catch (e) {
      $("progressText").textContent = "Lost contact with the harness: " + e.message;
    }
    timer = setTimeout(poll, delay);
  }

  // ---- actions ----------------------------------------------------------------
  $("start").addEventListener("click", async () => {
    $("formError").textContent = ""; $("preflight").replaceChildren();
    const f = form();
    if (!f.flows.length) { $("formError").textContent = "Pick at least one flow."; return; }
    if (!f.suites.length) { $("formError").textContent = "Pick at least one suite (Advanced)."; return; }
    try { await api("/api/run", f); filter = "ALL"; flowFilter = null; poll(); }
    catch (e) { $("formError").textContent = e.message; }
  });

  $("stop").addEventListener("click", async () => {
    try { await api("/api/stop", {}); } catch (e) { $("formError").textContent = e.message; }
  });

  $("check").addEventListener("click", async () => {
    const box = $("preflight");
    $("formError").textContent = "";
    box.replaceChildren(el("li", { class: "note", text: "Trying each flow once…" }));
    try {
      const r = await api("/api/preflight", form());
      box.replaceChildren(...r.steps.map((s) => el("li", { class: s.state },
        el("b", { text: s.label + ": " }), s.text)));
      if (r.steps.some((s) => s.state === "fail" && s.key !== "backend" && s.key !== "frontend")) {
        $("settings").open = true;
      }
    } catch (e) { box.replaceChildren(el("li", { class: "fail", text: e.message })); }
  });

  $("save").addEventListener("click", async () => {
    const msg = $("saveMsg");
    msg.textContent = "";
    try {
      const r = await api("/api/save", Object.assign(form(), { name: val("saveName") }));
      defaults = await api("/api/defaults");
      fillConfigs(r.config);
      applyConfig();
      msg.textContent = "Saved as " + r.config + " and selected.";
    } catch (e) { msg.textContent = "Not saved: " + e.message; }
  });

  $("download").addEventListener("click", async (ev) => {
    ev.preventDefault();
    try {
      const r = await fetch("/api/report", { headers: { "X-Sentinel-Token": TOKEN } });
      if (!r.ok) throw new Error("no report yet");
      const url = URL.createObjectURL(await r.blob());
      const a = el("a", { href: url, download: "sentinel-report-" + (lastRun ? lastRun.id : "run") + ".json" });
      document.body.append(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    } catch (e) { $("formError").textContent = e.message; }
  });

  $("toggleFlows").addEventListener("click", () => {
    const boxes = [...document.querySelectorAll("#flows input")];
    const all = boxes.every((b) => b.checked);
    boxes.forEach((b) => { b.checked = !all; });
  });
  $("mode").addEventListener("change", modeChanged);
  $("config").addEventListener("change", applyConfig);
  for (const id of TARGET_FIELDS.concat(["scheme"])) $(id).addEventListener("input", preview);
  $("via_frontend").addEventListener("change", preview);

  (async function init() {
    try { defaults = await api("/api/defaults"); buildForm(); }
    catch (e) { $("formError").textContent = "Could not load settings: " + e.message; }
    poll();
  })();
})();
