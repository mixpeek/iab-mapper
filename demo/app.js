const state = {
  rows: [],
  mapped: [],
  threshold: 0.7,
  unmatchedOnly: false,
  search: "",
};

const els = {
  dz: document.getElementById("dropzone"),
  file: document.getElementById("fileInput"),
  mapBtn: document.getElementById("mapBtn"),
  conf: document.getElementById("confidence"),
  confVal: document.getElementById("confVal"),
  search: document.getElementById("search"),
  unmatched: document.getElementById("unmatchedOnly"),
  tbody: document.getElementById("resultsBody"),
  exportCsv: document.getElementById("exportCsv"),
  exportJson: document.getElementById("exportJson"),
  summary: document.getElementById("summary"),
  fileStatus: document.getElementById("fileStatus"),
  useEmbeddings: document.getElementById("useEmbeddings"),
  embCut: document.getElementById("embCut"),
  useLLM: document.getElementById("useLLM"),
  llmModel: document.getElementById("llmModel"),
  llmHost: document.getElementById("llmHost"),
  methods: document.getElementById("methods"),
  clearBtn: document.getElementById("clearBtn"),
  themeToggle: document.getElementById("themeToggle"),
  themeIcon: document.getElementById("themeIcon"),
  themeLabel: document.getElementById("themeLabel"),
};

function fmtPct(n) {
  return (Math.round(n * 1000) / 10).toFixed(1) + "%";
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsText(file);
  });
}

function parseCSV(text) {
  const lines = text.split(/\r?\n/).filter(Boolean);
  if (lines.length === 0) return [];
  const header = lines[0].split(",").map((s) => s.trim());
  const idx = (name) => header.indexOf(name);
  if (idx("label") === -1) throw new Error("CSV must include a 'label' column");
  const out = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(",");
    const rec = {
      code: idx("code") !== -1 ? (cols[idx("code")] || "").trim() : undefined,
      label: (cols[idx("label")] || "").trim(),
      channel: idx("channel") !== -1 ? (cols[idx("channel")] || "").trim() : undefined,
      type: idx("type") !== -1 ? (cols[idx("type")] || "").trim() : undefined,
      format: idx("format") !== -1 ? (cols[idx("format")] || "").trim() : undefined,
      language: idx("language") !== -1 ? (cols[idx("language")] || "").trim() : undefined,
      source: idx("source") !== -1 ? (cols[idx("source")] || "").trim() : undefined,
      environment: idx("environment") !== -1 ? (cols[idx("environment")] || "").trim() : undefined,
    };
    if (!rec.label) continue;
    out.push(rec);
  }
  return out;
}

function validateRows(rows) {
  if (!Array.isArray(rows)) throw new Error("Input must be an array");
  for (const r of rows) {
    if (!r || typeof r !== "object") throw new Error("Row must be an object");
    if (!("label" in r) || !String(r.label || "").trim()) throw new Error("Each row must have a non-empty 'label'");
  }
}

function setSummary(total, mapped, threshold, unmatched) {
  els.summary.textContent = `Mapped ${total} rows • ${fmtPct(mapped / Math.max(total, 1))} ≥ threshold • ${unmatched} unmatched → Request Audit`;
}

function renderTable() {
  const t = state.threshold;
  const search = state.search.toLowerCase();
  const filtered = state.mapped.filter((r) => {
    const isUnmatched = !r.code_3x;
    if (state.unmatchedOnly && !isUnmatched) return false;
    if (r.confidence !== undefined && r.confidence < t && !isUnmatched) return false;
    if (!search) return true;
    const hay = `${r.code_2x || ""} ${r.label_2x || ""} ${r.code_3x || ""} ${r.label_3x || ""} ${r.method || ""}`.toLowerCase();
    return hay.includes(search);
  });

  els.tbody.innerHTML = "";
  for (const r of filtered) {
    const tr = document.createElement("tr");
    const cells = [
      r.code_2x || "",
      r.label_2x || "",
      r.code_3x || "",
      r.label_3x || "",
      r.confidence !== undefined ? r.confidence.toFixed(3) : "",
      r.method || "",
      r.notes || "",
      r.llm_reranked ? "Yes" : "No", // Display "Yes" or "No" for LLM re-ranked
    ];
    const methodDescriptions = {
      exact_code: "Direct code correspondence from curated seed/overrides",
      label_match: "Normalized label/path match",
      synonym: "Matched via alias dictionary",
      fuzzy: "String similarity retrieval",
      semantic: "Embedding similarity or LLM rerank",
      rapidfuzz: "Fuzzy match via RapidFuzz",
      bm25: "BM25 text retrieval",
      tfidf: "TF‑IDF cosine similarity",
      embed: "Semantic embedding similarity",
      override: "Forced mapping via overrides",
    };
    for (let i = 0; i < cells.length; i++) {
      const c = cells[i];
      const td = document.createElement("td");
      td.textContent = c;
      if (i === 5 && r.method) {
        td.title = methodDescriptions[r.method] || "";
      }
      tr.appendChild(td);
    }
    els.tbody.appendChild(tr);
  }

  const total = state.mapped.length;
  const matched = state.mapped.filter((r) => r.code_3x && r.confidence >= t).length;
  const unmatched = state.mapped.filter((r) => !r.code_3x || r.confidence < t).length;
  setSummary(total, matched, t, unmatched);

  const hasData = total > 0;
  els.exportCsv.disabled = !hasData;
  els.exportJson.disabled = !hasData;
  els.clearBtn.disabled = !hasData; // Enable/disable Clear button
}

async function onFiles(files) {
  const file = files[0];
  if (!file) return;
  if (!/\.(csv|json)$/i.test(file.name)) {
    alert("Please upload a .csv or .json file");
    return;
  }
  try {
    const text = await readFileAsText(file);
    let rows;
    if (/\.csv$/i.test(file.name)) {
      rows = parseCSV(text);
    } else {
      rows = JSON.parse(text);
    }
    validateRows(rows);
    state.rows = rows;
    els.mapBtn.disabled = rows.length === 0;
    els.fileStatus.textContent = `${file.name} • ${rows.length} rows ready`;
  } catch (e) {
    console.error(e);
    alert(`Invalid file: ${e.message || e}`);
    els.fileStatus.textContent = "";
  }
}

async function mapNow() {
  els.mapBtn.disabled = true;
  els.mapBtn.classList.add("loading"); // Add loading class
  try {
    const body = {
      version_from: "2.x",
      version_to: "3.0",
      rows: state.rows,
      options: {
        confidence_min: state.threshold,
        fuzzy_method: "hybrid",
        methods: Array.from(els.methods?.querySelectorAll('input[name="methods"]:checked') || []).map(i => i.value),
        use_embeddings: !!els.useEmbeddings.checked,
        emb_model: "tfidf",
        emb_cut: els.embCut ? parseFloat(els.embCut.value || "0.80") : 0.8,
        use_llm: !!(els.useLLM && els.useLLM.checked),
        llm_model: els.llmModel ? els.llmModel.value : undefined,
        llm_host: els.llmHost ? els.llmHost.value : undefined,
      },
    };
    const res = await fetch(`/api/map`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const data = await res.json();
    state.mapped = data.rows || [];
    renderTable();
  } catch (e) {
    console.error(e);
    alert(`Map failed: ${e.message || e}`);
  } finally {
    els.mapBtn.disabled = false;
    els.mapBtn.classList.remove("loading"); // Remove loading class
    els.clearBtn.disabled = state.rows.length === 0; // Enable Clear after mapping/error
  }
}

function clearTable() {
  state.rows = [];
  state.mapped = [];
  state.search = "";
  if (els.file) els.file.value = ""; // Clear selected file
  els.fileStatus.textContent = "";
  els.mapBtn.disabled = true;
  els.exportCsv.disabled = true;
  els.exportJson.disabled = true;
  els.clearBtn.disabled = true; // Disable Clear button
  els.tbody.innerHTML = "";
  setSummary(0, 0, state.threshold, 0); // Reset summary
}

function toCSV(rows) {
  const cols = ["code_2x","label_2x","code_3x","label_3x","confidence","method","notes"];
  const lines = [cols.join(",")];
  for (const r of rows) {
    lines.push(cols.map((k) => {
      const v = r[k] == null ? "" : String(r[k]);
      if (v.includes(",") || v.includes("\n") || v.includes('"')) {
        return '"' + v.replaceAll('"', '""') + '"';
      }
      return v;
    }).join(","));
  }
  return lines.join("\n");
}

function download(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

els.dz.addEventListener("click", () => els.file.click());
els.dz.addEventListener("dragover", (e) => { e.preventDefault(); });
els.dz.addEventListener("drop", (e) => { e.preventDefault(); onFiles(e.dataTransfer.files); });
els.file.addEventListener("change", (e) => onFiles(e.target.files));

els.mapBtn.addEventListener("click", mapNow);

els.conf.addEventListener("input", (e) => {
  state.threshold = parseFloat(e.target.value);
  els.confVal.textContent = state.threshold.toFixed(2);
  renderTable();
});

els.search.addEventListener("input", (e) => {
  state.search = e.target.value || "";
  renderTable();
});

els.unmatched.addEventListener("change", (e) => {
  state.unmatchedOnly = !!e.target.checked;
  renderTable();
});

els.clearBtn.addEventListener("click", clearTable); // Event listener for Clear button

els.exportCsv.addEventListener("click", () => {
  const csv = toCSV(state.mapped);
  download("mapped.csv", csv, "text/csv;charset=utf-8");
});

els.exportJson.addEventListener("click", () => {
  download("mapped.json", JSON.stringify(state.mapped, null, 2), "application/json;charset=utf-8");
});

// Tooltip titles for method explanations
// No longer needed, using custom JS tooltips

const TOOLTIP_DELAY = 100; // ms

let tooltipTimeout; // to manage delayed display

function showTooltip(element, text) {
  const tooltip = document.createElement("div");
  tooltip.className = "custom-tooltip";
  tooltip.textContent = text;
  document.body.appendChild(tooltip);

  const rect = element.getBoundingClientRect();
  tooltip.style.left = `${rect.left + rect.width / 2}px`;
  tooltip.style.top = `${rect.top - 10}px`; // 10px above the element
  tooltip.style.transform = `translate(-50%, -100%)`; // Center and position above
}

function hideTooltip() {
  const existingTooltip = document.querySelector(".custom-tooltip");
  if (existingTooltip) {
    existingTooltip.remove();
  }
}

document.addEventListener("mouseover", (event) => {
  const target = event.target.closest("[data-tooltip]");
  if (target) {
    clearTimeout(tooltipTimeout);
    tooltipTimeout = setTimeout(() => {
      showTooltip(target, target.getAttribute("data-tooltip"));
    }, TOOLTIP_DELAY);
  } else {
    clearTimeout(tooltipTimeout);
    hideTooltip();
  }
});

document.addEventListener("mouseout", (event) => {
  const target = event.target.closest("[data-tooltip]");
  if (target) {
    clearTimeout(tooltipTimeout);
    hideTooltip();
  }
});

// Prevent native title from showing alongside custom tooltip
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-tooltip]").forEach(el => {
    if (el.hasAttribute("title")) {
      el.setAttribute("data-original-title", el.getAttribute("title"));
      el.removeAttribute("title");
    }
  });
  // Initialize theme from localStorage or system preference
  try {
    const saved = localStorage.getItem("iab_theme");
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    setTheme(theme);
  } catch (_) {
    setTheme('dark');
  }
});

function setTheme(theme) {
  const root = document.documentElement;
  if (theme === 'light') {
    root.setAttribute('data-theme', 'light');
    if (els.themeIcon) els.themeIcon.className = 'fa-regular fa-sun';
    if (els.themeLabel) els.themeLabel.textContent = 'Light';
    if (els.themeToggle) els.themeToggle.setAttribute('aria-checked', 'true');
  } else {
    root.removeAttribute('data-theme');
    if (els.themeIcon) els.themeIcon.className = 'fa-regular fa-moon';
    if (els.themeLabel) els.themeLabel.textContent = 'Dark';
    if (els.themeToggle) els.themeToggle.setAttribute('aria-checked', 'false');
  }
}

if (els.themeToggle) {
  els.themeToggle.addEventListener('click', () => {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const next = isLight ? 'dark' : 'light';
    setTheme(next);
    try { localStorage.setItem('iab_theme', next); } catch(_) {}
  });
}


