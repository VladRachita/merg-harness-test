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
  let defaults = null, filter = "ALL", lastRun = null, timer = null, userEdited = false;

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
  function form() {
    const suites = [...document.querySelectorAll("#suites input:checked")].map((c) => c.value);
    return { mode: $("mode").value, config: $("config").value, host: $("host").value.trim(),
             port: $("port").value.trim(), scheme: $("scheme").value,
             base_path: $("base_path").value.trim(), suites };
  }

  function preview() {
    const f = form();
    $("urlPreview").textContent = f.scheme + "://" + (f.host || "…") + ":" + (f.port || "…") + f.base_path;
  }

  function applyConfigTarget() {
    const t = defaults.config_targets[$("config").value] || {};
    if (t.error) { $("formError").textContent = t.error; return; }
    $("formError").textContent = "";
    $("host").value = t.host || ""; $("port").value = t.port || "";
    $("scheme").value = t.scheme || "http"; $("base_path").value = t.base_path || "";
    userEdited = false;
    preview();
  }

  function modeChanged() {
    const http = $("mode").value === "http";
    $("httpFields").hidden = !http; $("refHint").hidden = http; $("check").hidden = !http;
    $("preflight").replaceChildren();
  }

  function buildForm() {
    const cfg = $("config");
    cfg.append(el("option", { value: "", text: "(built-in defaults)" }));
    for (const c of defaults.configs) cfg.append(el("option", { value: c, text: c }));
    cfg.value = defaults.config;
    const box = $("suites");
    for (const s of defaults.suites) {
      const id = "suite-" + s.name;
      box.append(el("label", { class: "suite", for: id },
        el("input", { type: "checkbox", id, value: s.name, checked: "" }),
        el("span", {}, el("b", { text: s.name + " (" + s.count + ")" }), el("small", { text: s.info }))));
    }
    applyConfigTarget();
    modeChanged();
  }

  // ---- rendering --------------------------------------------------------------
  function renderFilters(counts, total) {
    const box = $("filters");
    const items = [["ALL", "All", total]].concat(STATUSES.map((s) => [s, LABEL[s], counts[s] || 0]));
    box.replaceChildren(...items.map(([key, label, n]) => {
      const b = el("button", { type: "button", class: "chip", role: "tab",
                               "aria-selected": String(filter === key), text: label + " " + n });
      b.addEventListener("click", () => { filter = key; render(lastRun); });
      return b;
    }));
  }

  function renderRows(findings) {
    const order = Object.fromEntries(STATUSES.map((s, i) => [s, i]));
    const rows = findings.map((f, i) => [f, i])
      .filter(([f]) => filter === "ALL" || f.status === filter)
      .sort((a, b) => (order[a[0].status] - order[b[0].status]) || (a[1] - b[1]));
    const body = $("results").tBodies[0];
    body.replaceChildren(...rows.map(([f]) => {
      const what = el("td", {}, el("div", { text: f.desc }));
      if (f.detail) what.append(el("div", { class: "detail", text: f.detail }));
      if (f.fix) what.append(el("div", { class: "fix" }, el("b", { text: "Fix: " }), f.fix));
      return el("tr", {},
        el("td", {}, el("span", { class: "badge " + f.status, text: LABEL[f.status] })),
        el("td", { class: "id" }, f.id, el("small", { text: f.suite || f.category })),
        what);
    }));
    $("empty").hidden = rows.length > 0;
    $("empty").textContent = findings.length ? "No checks with this result."
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
    $("meta").textContent = run.target + " · " + run.suites.length + " suite(s) · coverage " +
      s.coverage + "% · " + run.elapsed + "s" + (run.requests ? " · " + run.requests + " requests" : "");

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

    renderFilters(c, run.findings.length);
    renderRows(run.findings);
    const dl = $("download");
    dl.hidden = running;
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
    if (!f.suites.length) { $("formError").textContent = "Pick at least one suite."; return; }
    try { await api("/api/run", f); filter = "ALL"; poll(); }
    catch (e) { $("formError").textContent = e.message; }
  });

  $("stop").addEventListener("click", async () => {
    try { await api("/api/stop", {}); } catch (e) { $("formError").textContent = e.message; }
  });

  $("check").addEventListener("click", async () => {
    const box = $("preflight");
    $("formError").textContent = "";
    box.replaceChildren(el("li", { class: "note", text: "Checking…" }));
    try {
      const r = await api("/api/preflight", form());
      box.replaceChildren(...r.lines.map(([kind, text]) => el("li", { class: kind, text })));
    } catch (e) { box.replaceChildren(el("li", { class: "fail", text: e.message })); }
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

  $("toggleSuites").addEventListener("click", () => {
    const boxes = [...document.querySelectorAll("#suites input")];
    const all = boxes.every((b) => b.checked);
    boxes.forEach((b) => { b.checked = !all; });
  });
  $("mode").addEventListener("change", modeChanged);
  $("config").addEventListener("change", applyConfigTarget);
  for (const id of ["host", "port", "scheme", "base_path"]) {
    $(id).addEventListener("input", () => { userEdited = true; preview(); });
  }

  (async function init() {
    try { defaults = await api("/api/defaults"); buildForm(); }
    catch (e) { $("formError").textContent = "Could not load settings: " + e.message; }
    poll();
  })();
})();
