const API_BASE = (window.SHMLRP_API_BASE || "").replace(/\/+$/, "");
const buildUrl = (path) => (API_BASE ? `${API_BASE}${path}` : path);

const state = {
  latest: null,
  running: false,
};

const apiStatus = document.getElementById("api-status");
const runButton = document.getElementById("run-btn");
const exportButton = document.getElementById("export-btn");
const runForm = document.getElementById("run-form");

const runIdEl = document.getElementById("run-id");
const runStatusEl = document.getElementById("run-status");
const runUpdatedEl = document.getElementById("run-updated");
const runLogEl = document.getElementById("run-log");

const headlineMetrics = document.getElementById("headline-metrics");
const driftBars = document.getElementById("drift-bars");
const rootCauses = document.getElementById("root-causes");
const governance = document.getElementById("governance");
const incidentFeed = document.getElementById("incident-feed");
const artifactGrid = document.getElementById("artifact-grid");
const accuracyChart = document.getElementById("accuracy-chart");
const driftChart = document.getElementById("drift-chart");
const historyTable = document.getElementById("history-table");

const formatNumber = (value, digits = 3) => {
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "number") {
    return value.toFixed(digits);
  }
  return String(value);
};

const setStatus = (text, tone) => {
  apiStatus.textContent = text;
  apiStatus.classList.remove("warn", "alert");
  if (tone) {
    apiStatus.classList.add(tone);
  }
};

const formatTimestamp = (value) => {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) {
    return "-";
  }
  return date.toLocaleString();
};

const resizeCanvas = (canvas) => {
  if (!canvas) {
    return null;
  }
  const ratio = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * ratio;
  canvas.height = rect.height * ratio;
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  return ctx;
};

const drawLineChart = (canvas, seriesList, options = {}) => {
  const ctx = resizeCanvas(canvas);
  if (!ctx) {
    return;
  }
  const width = canvas.getBoundingClientRect().width;
  const height = canvas.getBoundingClientRect().height;
  ctx.clearRect(0, 0, width, height);

  const values = seriesList.flatMap((series) => series.values).filter((value) => value !== null && value !== undefined);
  if (!values.length) {
    ctx.fillStyle = "rgba(255,255,255,0.4)";
    ctx.font = "14px Space Grotesk, sans-serif";
    ctx.fillText("Run pipeline to populate chart", 16, height / 2);
    return;
  }

  const padding = 24;
  const minY = options.minY ?? 0;
  const maxY = options.maxY ?? Math.max(...values, 1);
  const spanY = maxY - minY || 1;
  const gridLines = options.gridLines ?? 4;

  ctx.strokeStyle = "rgba(255,255,255,0.06)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= gridLines; i += 1) {
    const y = padding + ((height - padding * 2) * i) / gridLines;
    ctx.beginPath();
    ctx.moveTo(padding, y);
    ctx.lineTo(width - padding, y);
    ctx.stroke();
  }

  const pointCount = seriesList[0]?.values?.length || 1;
  const stepX = pointCount > 1 ? (width - padding * 2) / (pointCount - 1) : 0;

  seriesList.forEach((series) => {
    ctx.strokeStyle = series.color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    let started = false;
    series.values.forEach((value, index) => {
      if (value === null || value === undefined) {
        started = false;
        return;
      }
      const x = padding + index * stepX;
      const y = padding + (height - padding * 2) * (1 - (value - minY) / spanY);
      if (!started) {
        ctx.moveTo(x, y);
        started = true;
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    ctx.fillStyle = series.color;
    series.values.forEach((value, index) => {
      if (value === null || value === undefined) {
        return;
      }
      const x = padding + index * stepX;
      const y = padding + (height - padding * 2) * (1 - (value - minY) / spanY);
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });
  });
};

const updateHeadline = (report) => {
  headlineMetrics.innerHTML = "";
  const metrics = report?.performance || {};
  const baseline = metrics.baseline || {};
  const candidate = report?.retrain?.candidate_metrics || {};

  const items = [
    { label: "Baseline accuracy", value: formatNumber(baseline.accuracy) },
    { label: "Candidate accuracy", value: formatNumber(candidate.accuracy) },
    { label: "Baseline AUC", value: formatNumber(baseline.auc) },
    { label: "Brier score", value: formatNumber(candidate.brier ?? baseline.brier) },
  ];

  items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "metric-card";
    card.innerHTML = `<span class="metric-label">${item.label}</span><span class="metric-value">${item.value}</span>`;
    headlineMetrics.appendChild(card);
  });
};

const updateDrift = (report) => {
  driftBars.innerHTML = "";
  const scores = report?.drift?.feature_scores || {};
  const entries = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  const maxValue = entries.length ? Math.max(...entries.map((entry) => entry[1])) : 1;

  entries.forEach(([feature, value]) => {
    const row = document.createElement("div");
    row.className = "bar-item";
    const percent = Math.max(0.05, value / maxValue);
    row.innerHTML = `
      <div>${feature}</div>
      <div class="bar" style="transform: scaleX(${percent})"></div>
      <div>${formatNumber(value, 3)}</div>
    `;
    driftBars.appendChild(row);
  });
};

const updateRootCause = (report) => {
  rootCauses.innerHTML = "";
  const features = report?.root_cause?.top_features || [];
  if (!features.length) {
    rootCauses.innerHTML = "<li>Run pipeline to compute root-cause signals.</li>";
    return;
  }
  features.forEach((feature) => {
    const li = document.createElement("li");
    li.textContent = feature;
    rootCauses.appendChild(li);
  });
};

const updateGovernance = (report) => {
  governance.innerHTML = "";
  const retrain = report?.retrain || {};
  const canary = retrain.canary || {};
  const baseline = report?.performance?.baseline || {};
  const baselineCurrent = report?.performance?.baseline_on_current || {};
  const candidate = retrain.candidate_metrics || {};

  const cards = [
    {
      title: "Baseline",
      subtitle: `Accuracy: ${formatNumber(baseline.accuracy)}`,
    },
    {
      title: "Baseline on current",
      subtitle: `Accuracy: ${formatNumber(baselineCurrent.accuracy)}`,
    },
    {
      title: "Candidate",
      subtitle: `Accuracy: ${formatNumber(candidate.accuracy)}`,
    },
    {
      title: "Canary",
      subtitle: canary.reason || "Pending",
      badge: canary.approved ? "Approved" : "Review",
      tone: canary.approved ? null : "warn",
    },
  ];

  cards.forEach((card) => {
    const container = document.createElement("div");
    container.className = "governance-card";
    container.innerHTML = `
      <div class="metric-label">${card.title}</div>
      <div class="metric-value">${card.subtitle}</div>
    `;
    if (card.badge) {
      const badge = document.createElement("div");
      badge.className = `badge ${card.tone || ""}`.trim();
      badge.textContent = card.badge;
      container.appendChild(badge);
    }
    governance.appendChild(container);
  });
};

const updateIncidents = (report) => {
  incidentFeed.innerHTML = "";
  const items = [];
  if (report?.drift?.is_drifted) {
    items.push({
      title: "Data drift detected",
      body: `Drifted features: ${report.drift.drifted_features?.join(", ") || ""}`,
      tone: "warn",
    });
  }
  if (report?.quality?.issues?.length) {
    items.push({
      title: "Quality gate failed",
      body: report.quality.issues.join(" | "),
      tone: "alert",
    });
  }
  if (report?.retrain?.needed) {
    items.push({
      title: "Auto retrain triggered",
      body: report.retrain.promoted ? "Candidate promoted" : "Candidate held",
      tone: report.retrain.promoted ? null : "warn",
    });
  }

  if (!items.length) {
    items.push({
      title: "No incidents",
      body: "Run pipeline to generate reliability events.",
    });
  }

  items.forEach((item) => {
    const li = document.createElement("li");
    li.className = "incident-item";
    const badge = item.tone ? `<div class="badge ${item.tone}">${item.tone.toUpperCase()}</div>` : "";
    li.innerHTML = `
      <div class="metric-label">${item.title}</div>
      <div class="metric-value">${item.body}</div>
      ${badge}
    `;
    incidentFeed.appendChild(li);
  });
};

const updateArtifacts = (report) => {
  artifactGrid.innerHTML = "";
  const artifacts = report?.artifacts || {};
  const entries = [
    { label: "Baseline model", value: artifacts.baseline_model },
    { label: "Candidate model", value: artifacts.candidate_model },
    { label: "Baseline data", value: report?.data?.baseline_path },
    { label: "Current data", value: report?.data?.current_path },
  ];

  entries.forEach((entry) => {
    const card = document.createElement("div");
    card.className = "artifact";
    card.innerHTML = `<strong>${entry.label}</strong><div>${entry.value || "-"}</div>`;
    artifactGrid.appendChild(card);
  });
};

const updateHistory = (records) => {
  if (!historyTable) {
    return;
  }
  const tbody = historyTable.querySelector("tbody");
  tbody.innerHTML = "";

  if (!records.length) {
    const row = document.createElement("tr");
    row.innerHTML = `<td colspan="5">No runs yet. Trigger a pipeline run.</td>`;
    tbody.appendChild(row);
    return;
  }

  records.forEach((record) => {
    const drift = record.metrics?.drift?.global_score;
    const baselineAcc = record.metrics?.baseline?.accuracy;
    const candidateAcc = record.metrics?.candidate?.accuracy;
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${record.run_id || "-"}</td>
      <td>${formatTimestamp(record.timestamp)}</td>
      <td>${formatNumber(drift)}</td>
      <td>${formatNumber(baselineAcc)}</td>
      <td>${formatNumber(candidateAcc)}</td>
    `;
    tbody.appendChild(row);
  });
};

const updateCharts = (records) => {
  if (!records.length) {
    drawLineChart(accuracyChart, []);
    drawLineChart(driftChart, []);
    return;
  }
  const baseline = records.map((record) => record.metrics?.baseline?.accuracy ?? null);
  const candidate = records.map((record) => record.metrics?.candidate?.accuracy ?? null);
  const drift = records.map((record) => record.metrics?.drift?.global_score ?? null);

  drawLineChart(
    accuracyChart,
    [
      { label: "Baseline", color: "#2dd4bf", values: baseline },
      { label: "Candidate", color: "#f6c453", values: candidate },
    ],
    { minY: 0, maxY: 1 }
  );
  const driftMax = Math.max(...drift.filter((value) => value !== null && value !== undefined), 0.2);
  drawLineChart(
    driftChart,
    [{ label: "Drift", color: "#ff6b6b", values: drift }],
    { minY: 0, maxY: Math.min(1, driftMax + 0.1) }
  );
};

const updateMeta = (report) => {
  if (!report) {
    runIdEl.textContent = "No runs yet";
    runStatusEl.textContent = "Idle";
    runUpdatedEl.textContent = "-";
    runLogEl.textContent = "Awaiting next run...";
    return;
  }
  runIdEl.textContent = report.run_id || "-";
  runStatusEl.textContent = report.status || "-";
  runUpdatedEl.textContent = report.timestamps?.ended_at || "-";
  runLogEl.textContent = JSON.stringify(
    {
      drifted_features: report.drift?.drifted_features,
      canary: report.retrain?.canary?.reason,
      promoted: report.retrain?.promoted,
    },
    null,
    2
  );
};

const updateUI = (report) => {
  state.latest = report;
  updateMeta(report);
  updateHeadline(report);
  updateDrift(report);
  updateRootCause(report);
  updateGovernance(report);
  updateIncidents(report);
  updateArtifacts(report);
};

const fetchLatest = async () => {
  try {
    const response = await fetch(buildUrl("/latest"));
    if (!response.ok) {
      setStatus("API: error", "alert");
      return;
    }
    const data = await response.json();
    setStatus("API: online");
    if (Object.keys(data || {}).length) {
      updateUI(data);
    }
  } catch (err) {
    setStatus("API: offline", "alert");
  }
};

const fetchHistory = async () => {
  try {
    const response = await fetch(buildUrl("/metrics/recent?limit=20"));
    if (!response.ok) {
      return;
    }
    const records = await response.json();
    updateHistory(records);
    updateCharts(records);
  } catch (err) {
    updateHistory([]);
    updateCharts([]);
  }
};

const runPipeline = async (payload) => {
  runButton.disabled = true;
  runButton.textContent = "Running...";
  runStatusEl.textContent = "Running";
  runLogEl.textContent = "Pipeline in progress...";
  try {
    const response = await fetch(buildUrl("/run"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    updateUI(data);
    fetchHistory();
  } catch (err) {
    runLogEl.textContent = "Run failed. Check server logs.";
  } finally {
    runButton.disabled = false;
    runButton.textContent = "Run Pipeline";
  }
};

runForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const formData = new FormData(runForm);
  const payload = {
    drift_probability: Number(formData.get("drift_probability")),
    sample_size: Number(formData.get("sample_size")),
    seed: Number(formData.get("seed")),
  };
  runPipeline(payload);
});

runButton.addEventListener("click", () => {
  runForm.requestSubmit();
});

exportButton.addEventListener("click", () => {
  if (!state.latest) {
    runLogEl.textContent = "No report to export yet.";
    return;
  }
  const blob = new Blob([JSON.stringify(state.latest, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${state.latest.run_id || "report"}.json`;
  link.click();
  URL.revokeObjectURL(url);
});

fetchLatest();
fetchHistory();
