const RUN_META = {
  dfr: { key: "dfr", match: "dfr-rapid-launch", label: "dfr-rapid-launch" },
  multi: { key: "multi", match: "multi-drone-inspection", label: "multi-drone-inspection" },
  waiver: { key: "waiver", match: "bvlos-waiver-block", label: "bvlos-waiver-block" },
};

let demoData = null;
let currentRun = null;
let activeTab = "summary";

function findRun(match) {
  if (!demoData?.runs) return null;
  return demoData.runs.find((r) => {
    const id = r.summary?.mission_id || r.doctor?.mission_id || "";
    const dir = r.receipt_dir || "";
    return id.includes(match) || dir.includes(match);
  });
}

function statusBadge(status) {
  return status || "caution";
}

function renderChecks(container, checks, limit = 4) {
  if (!container) return;
  container.innerHTML = `
    <div class="check-row head"><span>check</span><span>sev</span><span>result</span></div>
  `;
  (checks || []).slice(0, limit).forEach((c) => {
    const row = document.createElement("div");
    row.className = "check-row";
    row.innerHTML = `
      <span>${c.signal}</span>
      <span class="sev ${c.status}">${c.status}</span>
      <span>${c.message}</span>
    `;
    container.appendChild(row);
  });
}

function renderMetrics(container, summary, doctor) {
  if (!container) return;
  container.innerHTML = `
    <article><span>drones</span><strong>${summary?.drone_count ?? "—"}</strong></article>
    <article><span>waiver</span><strong>${(summary?.waiver_profile || "—").replace("part91-", "").replace("-bvlos", "ft")}</strong></article>
    <article><span>launch</span><strong>${doctor?.launch_recommendation ?? "—"}</strong></article>
  `;
}

function renderDoctorList(container, checks) {
  if (!container) return;
  container.innerHTML = "";
  (checks || []).forEach((c) => {
    const item = document.createElement("div");
    item.className = "doctor-item";
    item.innerHTML = `<span class="sev ${c.status}">${c.status}</span> <strong>${c.signal}</strong> — ${c.message}`;
    container.appendChild(item);
  });
}

function receiptPayload(run, tab) {
  if (tab === "doctor") return run.doctor;
  if (tab === "full") return run;
  return run.summary;
}

function applyRun(key) {
  const meta = RUN_META[key];
  const run = findRun(meta.match);
  if (!run) return false;

  currentRun = run;
  const doctor = run.doctor || {};
  const summary = run.summary || {};
  const badge = statusBadge(doctor.overall_status);

  const sets = [
    ["hero-label", meta.label],
    ["hero-badge", null, badge],
    ["hero-command", `mission-preflight doctor ${meta.label} —json`],
    ["demo-label", meta.label],
    ["demo-status", null, badge],
    ["demo-command", `mission-preflight doctor ${meta.label} —json`],
    ["launch-line", `<strong>Launch recommendation:</strong> ${doctor.launch_recommendation || "—"}`],
  ];

  sets.forEach(([id, text, cls]) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (text != null && id !== "hero-badge" && id !== "demo-status") {
      el.innerHTML = text;
    }
    if (cls) {
      el.className = id.includes("badge") || id.includes("status") ? `badge ${cls}` : el.className;
      if (id.includes("status")) el.className = `badge ${cls}`;
    }
  });

  document.getElementById("hero-badge").className = `badge ${badge}`;
  document.getElementById("demo-status").className = `badge ${badge}`;

  renderMetrics(document.getElementById("hero-metrics"), summary, doctor);
  renderMetrics(document.getElementById("demo-metrics"), summary, doctor);
  renderChecks(document.getElementById("hero-checks"), doctor.checks);
  renderChecks(document.getElementById("demo-checks"), doctor.checks);
  renderDoctorList(document.getElementById("doctor-list"), doctor.checks);

  const preview = document.getElementById("receipt-preview");
  if (preview) {
    preview.textContent = JSON.stringify(receiptPayload(run, activeTab), null, 2);
  }
  return true;
}

async function loadDemoData() {
  const res = await fetch("./data/demo.json");
  if (!res.ok) throw new Error(`Failed to load demo data (${res.status})`);
  demoData = await res.json();
  Object.values(RUN_META).forEach((meta) => {
    const run = findRun(meta.match);
    if (run) RUN_META[meta.key] = { ...meta, run };
  });
}

function wireTabs() {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeTab = btn.dataset.tab;
      if (currentRun) {
        document.getElementById("receipt-preview").textContent = JSON.stringify(
          receiptPayload(currentRun, activeTab),
          null,
          2
        );
      }
    });
  });
}

function wireDownload() {
  const link = document.getElementById("download-receipt");
  if (!link) return;
  link.addEventListener("click", (e) => {
    e.preventDefault();
    if (!currentRun?.doctor) return;
    const blob = new Blob([JSON.stringify(currentRun.doctor, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentRun.summary?.mission_id || "doctor"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });
}

async function init() {
  wireTabs();
  wireDownload();

  const runBtn = document.getElementById("run-demo");
  const runSelect = document.getElementById("run-select");
  const err = document.getElementById("demo-error");

  runBtn?.addEventListener("click", () => {
    if (!applyRun(runSelect.value)) {
      err.hidden = false;
      err.textContent = "Could not load scenario — demo.json missing run.";
    } else {
      err.hidden = true;
    }
  });

  try {
    await loadDemoData();
    applyRun("dfr");
  } catch (e) {
    if (err) {
      err.hidden = false;
      err.textContent = String(e.message || e);
    }
  }
}

document.addEventListener("DOMContentLoaded", init);
