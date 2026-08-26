// Tideway - Interactive Dashboard & Real-Time Console Controller

let ws = null;
let reconnectTimer = null;
let currentScanModeDeep = false;
let currentExecutionMode = "clean";
let currentPreviewFiles = [];
let autoScrollEnabled = true;
let confirmResolveCallback = null;

let categoryColors = {
  "Images": "#38bdf8",
  "Videos": "#a855f7",
  "Audio": "#f59e0b",
  "Documents": "#34d399",
  "Projects_And_Creative": "#f97316",
  "Code_And_Web": "#ec4899",
  "Data_And_Databases": "#6366f1",
  "Archives": "#94a3b8",
  "Executables_And_Installers": "#f43f5e",
  "Fonts": "#14b8a6",
  "Misc": "#64748b"
};

let distributionChartInstance = null;
let storageChartInstance = null;
let categoriesData = {};

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  connectWebSocket();
  loadDrives();
  loadStatus();
  loadHistory();
  loadWatchers();
  loadCategories();

  // Check URL hash for direct tab navigation (e.g. #tab-preview, #tab-history)
  if (window.location.hash) {
    const rawHash = window.location.hash.replace("#tab-", "").replace("#", "");
    const validTabs = ["dashboard", "preview", "history", "watcher", "rules"];
    if (validTabs.includes(rawHash)) {
      switchTab(rawHash);
    }
  }

  window.addEventListener("hashchange", () => {
    if (window.location.hash) {
      const rawHash = window.location.hash.replace("#tab-", "").replace("#", "");
      const validTabs = ["dashboard", "preview", "history", "watcher", "rules"];
      if (validTabs.includes(rawHash)) {
        switchTab(rawHash);
      }
    }
  });

  const targetInput = document.getElementById("target-dir-input");
  if (targetInput) {
    targetInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        startOrganize();
      }
    });
  }
});

// ==========================================
// 1. WEBSOCKET REAL-TIME STREAMING
// ==========================================
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  updateWsStatus("connecting", "Connecting...");

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    updateWsStatus("connected", "Connected");
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleRealtimeEvent(data);
    } catch (e) {
      console.error("Error parsing WebSocket message:", e);
    }
  };

  ws.onclose = () => {
    updateWsStatus("disconnected", "Reconnecting...");
    if (!reconnectTimer) {
      reconnectTimer = setTimeout(connectWebSocket, 3000);
    }
  };

  ws.onerror = () => {
    updateWsStatus("disconnected", "Connection Error");
    ws.close();
  };
}

function updateWsStatus(status, text) {
  const indicator = document.getElementById("ws-indicator");
  const label = document.getElementById("ws-status-text");
  if (!indicator || !label) return;

  label.innerText = text;
  if (status === "connected") {
    indicator.className = "w-2 h-2 rounded-full bg-emerald-400";
  } else if (status === "connecting") {
    indicator.className = "w-2 h-2 rounded-full bg-amber-400 animate-pulse";
  } else {
    indicator.className = "w-2 h-2 rounded-full bg-rose-500 animate-pulse";
  }
}

function handleRealtimeEvent(data) {
  const statusBadge = document.getElementById("interactive-status-badge");
  const footerStatus = document.getElementById("terminal-footer-status");

  switch (data.type) {
    case "start":
      showLiveProgress(true, data.mode);
      if (statusBadge) {
        statusBadge.className = "px-3 py-1 text-xs rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono font-medium animate-pulse";
        statusBadge.innerText = `STATUS: ${data.mode.toUpperCase()}`;
      }
      if (footerStatus) {
        footerStatus.innerText = `Running ${data.mode} on ${data.target}...`;
      }
      appendTerminalLog(`=== ${data.mode.toUpperCase()} STARTED ===`, "text-indigo-400 font-bold");
      appendTerminalLog(`Target: ${data.target} (Deep: ${data.deep})`, "text-slate-400");
      break;

    case "log":
      appendTerminalLog(data.text, data.color || "text-slate-300");
      break;

    case "file_preview":
      updateChartsFromLiveCounts(data.counts, data.sizes);
      break;

    case "file_moving":
      setLiveCurrentFile(`Moving: ${data.file.name}`);
      break;

    case "file_moved":
      setLiveProcessedCount(data.total_processed);
      updateChartsFromLiveCounts(data.counts, data.sizes);
      break;

    case "folder_removed":
      // Handled via log event
      break;

    case "complete":
      showLiveProgress(false);
      if (statusBadge) {
        statusBadge.className = "px-3 py-1 text-xs rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono font-medium";
        statusBadge.innerText = "STATUS: READY";
      }
      if (footerStatus) {
        footerStatus.innerText = `Completed. ${data.summary.total_files} files processed (${data.summary.total_bytes_formatted}).`;
      }
      appendTerminalLog(`=== ${data.summary.mode.toUpperCase()} FINISHED ===\n`, "text-emerald-400 font-bold");
      showToast("Completed", `${data.summary.total_files} files processed successfully.`, "success");
      loadStatus();
      loadHistory();
      break;

    case "watchdog_organized":
      appendTerminalLog(`[WATCHDOG AUTO-SORT] ${data.file.name} -> ${data.file.dest_path}`, "text-cyan-400 font-semibold");
      showToast("Auto-Organized File", `${data.file.name} sorted into ${data.file.category}`, "info");
      loadStatus();
      loadHistory();
      break;

    case "watchdog_status_changed":
      loadWatchers();
      break;

    case "undo_complete":
      appendTerminalLog(`[UNDO] Run ${data.run_id} reverted (${data.result.restored} files restored).`, "text-amber-300 font-semibold");
      showToast("Run Restored", `${data.result.restored} files moved back to original locations.`, "info");
      loadHistory();
      break;

    case "error":
      appendTerminalLog(`[ERROR] ${data.error}`, "text-rose-400 font-bold");
      showToast("Error", data.error, "error");
      break;
  }
}

// ==========================================
// 2. TERMINAL LOG STREAMING & HELPERS
// ==========================================
function appendTerminalLog(message, colorClass = "text-slate-300") {
  const feed = document.getElementById("terminal-log-feed");
  if (!feed) return;

  const time = new Date().toLocaleTimeString();
  const line = document.createElement("div");
  line.className = `leading-relaxed break-all font-mono text-xs ${colorClass}`;
  
  if (message.startsWith("===") || message.startsWith("\n")) {
    line.innerHTML = `${escapeHtml(message)}`;
  } else {
    line.innerHTML = `<span class="text-slate-600 select-none mr-2">[${time}]</span>${escapeHtml(message)}`;
  }
  
  feed.appendChild(line);

  if (autoScrollEnabled) {
    feed.scrollTop = feed.scrollHeight;
  }
}

function clearConsoleLog() {
  const feed = document.getElementById("terminal-log-feed");
  if (feed) {
    feed.innerHTML = `<div class="text-slate-500 font-mono text-xs">[System] Terminal feed cleared. Ready for commands.</div>`;
  }
}

function copyTerminalLogs() {
  const feed = document.getElementById("terminal-log-feed");
  if (!feed) return;

  const text = feed.innerText;
  navigator.clipboard.writeText(text).then(() => {
    showToast("Copied", "Terminal logs copied to clipboard.", "info");
  }).catch(() => {
    showToast("Copy Failed", "Could not copy logs to clipboard.", "error");
  });
}

function toggleAutoScroll() {
  autoScrollEnabled = !autoScrollEnabled;
  const btn = document.getElementById("btn-autoscroll-toggle");
  if (!btn) return;

  if (autoScrollEnabled) {
    btn.className = "px-2.5 py-1 rounded bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/40 transition";
    btn.innerText = "Auto-Scroll: ON";
  } else {
    btn.className = "px-2.5 py-1 rounded bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700 transition";
    btn.innerText = "Auto-Scroll: OFF";
  }
}

function showLiveProgress(visible, modeText = "Processing...") {
  const container = document.getElementById("live-progress-container");
  const title = document.getElementById("live-progress-title");
  if (!container) return;

  if (visible) {
    container.classList.remove("hidden");
    if (title) title.innerText = `${modeText}...`;
    setLiveProgressBar(0);
  } else {
    setTimeout(() => {
      container.classList.add("hidden");
    }, 1200);
    setLiveProgressBar(100);
  }
}

function setLiveProgressBar(pct) {
  const bar = document.getElementById("live-progress-bar");
  const pctLabel = document.getElementById("live-progress-pct");
  if (bar) bar.style.width = `${pct}%`;
  if (pctLabel) pctLabel.innerText = `${Math.round(pct)}%`;
}

function setLiveProcessedCount(count) {
  const elem = document.getElementById("live-processed-count");
  if (elem) elem.innerText = `Processed: ${count} files`;
}

function setLiveCurrentFile(fileName) {
  const elem = document.getElementById("live-current-file");
  if (elem) elem.innerText = fileName;
}

// ==========================================
// 3. INTERACTIVE TERMINAL-STYLE WORKFLOW
// ==========================================

// Step 2: Scan Mode Selection
function setScanMode(deep) {
  currentScanModeDeep = deep;
  const btnStandard = document.getElementById("btn-mode-standard");
  const btnDeep = document.getElementById("btn-mode-deep");
  const hint = document.getElementById("start-summary-hint");

  if (deep) {
    btnDeep.className = "p-3 rounded-xl border border-indigo-500/50 bg-indigo-600/20 text-left transition flex items-start space-x-3 w-full";
    btnStandard.className = "p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-900 text-left transition flex items-start space-x-3 w-full";
    appendTerminalLog(`[Option Selected] Scan Type: 2. Deep Scan (Recursive subfolders + prune empty folders)`, "text-indigo-300");
  } else {
    btnStandard.className = "p-3 rounded-xl border border-indigo-500/50 bg-indigo-600/20 text-left transition flex items-start space-x-3 w-full";
    btnDeep.className = "p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-900 text-left transition flex items-start space-x-3 w-full";
    appendTerminalLog(`[Option Selected] Scan Type: 1. Standard (Top-level files only)`, "text-indigo-300");
  }

  const modeLabels = {
    "clean": "Clean (Move Files)",
    "dry_run": "Dry Run (Preview Only)",
    "summary": "Summary Counts Only"
  };
  if (hint) {
    hint.innerText = `Configured: ${deep ? "Deep Scan" : "Standard Scan"} • ${modeLabels[currentExecutionMode] || "Clean"}`;
  }
}

// Step 3: Mode Selection Click Handler
function handleModeClick(mode) {
  setExecutionMode(mode);
}

function setExecutionMode(mode) {
  currentExecutionMode = mode;
  const btnClean = document.getElementById("btn-mode-clean");
  const btnDry = document.getElementById("btn-mode-dry");
  const btnSummary = document.getElementById("btn-mode-summary");
  const radioClean = document.getElementById("radio-clean");
  const radioDry = document.getElementById("radio-dry");
  const radioSummary = document.getElementById("radio-summary");
  const startBtn = document.getElementById("btn-start-organize");
  const startLabel = document.getElementById("start-btn-label");
  const hint = document.getElementById("start-summary-hint");

  // Reset all buttons to inactive styling
  if (btnClean) btnClean.className = "p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-900 text-slate-300 text-left transition flex items-center justify-between group w-full cursor-pointer";
  if (btnDry) btnDry.className = "p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-900 text-slate-300 text-left transition flex items-center justify-between group w-full cursor-pointer";
  if (btnSummary) btnSummary.className = "p-2.5 rounded-xl border border-slate-800 bg-slate-950/60 hover:bg-slate-900 text-slate-300 text-left transition flex items-center justify-between group w-full cursor-pointer";

  // Reset radio dots
  if (radioClean) {
    radioClean.className = "w-3.5 h-3.5 rounded-full border-2 border-slate-600 bg-transparent flex items-center justify-center shrink-0";
    radioClean.innerHTML = "";
  }
  if (radioDry) {
    radioDry.className = "w-3.5 h-3.5 rounded-full border-2 border-slate-600 bg-transparent flex items-center justify-center shrink-0";
    radioDry.innerHTML = "";
  }
  if (radioSummary) {
    radioSummary.className = "w-3.5 h-3.5 rounded-full border-2 border-slate-600 bg-transparent flex items-center justify-center shrink-0";
    radioSummary.innerHTML = "";
  }

  const scanTypeText = currentScanModeDeep ? "Deep Scan" : "Standard Scan";

  if (mode === "clean") {
    if (btnClean) btnClean.className = "p-2.5 rounded-xl border border-emerald-500/50 bg-emerald-600/20 text-white text-left transition shadow-md shadow-emerald-600/20 flex items-center justify-between group w-full cursor-pointer";
    if (radioClean) {
      radioClean.className = "w-3.5 h-3.5 rounded-full border-2 border-emerald-400 bg-emerald-400 flex items-center justify-center shrink-0";
      radioClean.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-slate-950"></span>`;
    }
    if (startBtn) startBtn.className = "w-full sm:w-auto px-7 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs tracking-wide transition shadow-lg shadow-emerald-600/25 flex items-center justify-center space-x-2 group cursor-pointer";
    if (startLabel) startLabel.innerText = "Start Clean (Move Files)";
    if (hint) hint.innerText = `Configured: ${scanTypeText} • Clean (Move Files)`;
    appendTerminalLog(`[Option Selected] Execution Mode: 1. Clean (Move Files)`, "text-emerald-300");
  } else if (mode === "dry_run") {
    if (btnDry) btnDry.className = "p-2.5 rounded-xl border border-sky-500/50 bg-sky-600/20 text-white text-left transition shadow-md shadow-sky-600/20 flex items-center justify-between group w-full cursor-pointer";
    if (radioDry) {
      radioDry.className = "w-3.5 h-3.5 rounded-full border-2 border-sky-400 bg-sky-400 flex items-center justify-center shrink-0";
      radioDry.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-slate-950"></span>`;
    }
    if (startBtn) startBtn.className = "w-full sm:w-auto px-7 py-3 rounded-xl bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white font-bold text-xs tracking-wide transition shadow-lg shadow-sky-600/25 flex items-center justify-center space-x-2 group cursor-pointer";
    if (startLabel) startLabel.innerText = "Start Dry Run (Preview)";
    if (hint) hint.innerText = `Configured: ${scanTypeText} • Dry Run (Preview Only)`;
    appendTerminalLog(`[Option Selected] Execution Mode: 2. Dry Run (Preview Only)`, "text-sky-300");
  } else if (mode === "summary") {
    if (btnSummary) btnSummary.className = "p-2.5 rounded-xl border border-purple-500/50 bg-purple-600/20 text-white text-left transition shadow-md shadow-purple-600/20 flex items-center justify-between group w-full cursor-pointer";
    if (radioSummary) {
      radioSummary.className = "w-3.5 h-3.5 rounded-full border-2 border-purple-400 bg-purple-400 flex items-center justify-center shrink-0";
      radioSummary.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-slate-950"></span>`;
    }
    if (startBtn) startBtn.className = "w-full sm:w-auto px-7 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs tracking-wide transition shadow-lg shadow-purple-600/25 flex items-center justify-center space-x-2 group cursor-pointer";
    if (startLabel) startLabel.innerText = "Start Summary Scan";
    if (hint) hint.innerText = `Configured: ${scanTypeText} • Summary Counts Only`;
    appendTerminalLog(`[Option Selected] Execution Mode: 3. Summary Only`, "text-purple-300");
  }
}

// Dedicated Start Dispatcher
function startOrganize() {
  if (currentExecutionMode === "clean") {
    interactiveCleanPrompt();
  } else if (currentExecutionMode === "dry_run") {
    triggerScan(false);
  } else if (currentExecutionMode === "summary") {
    triggerScan(true);
  }
}

// Step 2 & 3: Mode 1: Interactive Clean Flow (just like terminal)
async function interactiveCleanPrompt() {
  const target = document.getElementById("target-dir-input").value.trim();
  if (!target) {
    showToast("Missing Folder", "Please choose or enter a directory path first.", "error");
    return;
  }

  appendTerminalLog(`\n[Action: Clean] Checking ${target} ...`, "text-amber-300 font-semibold");
  showLiveProgress(true, "Scanning for files");

  try {
    // Quick preview check
    const previewRes = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_dir: target, deep: currentScanModeDeep, quiet: true })
    });

    if (!previewRes.ok) {
      const err = await previewRes.json();
      throw new Error(err.detail || "Failed to scan folder");
    }

    const previewData = await previewRes.json();
    const total = previewData.total_files || 0;

    showLiveProgress(false);

    if (total === 0) {
      appendTerminalLog("No files to organize.", "text-slate-400 font-semibold");
      showToast("Nothing to Clean", "No loose files found to organize.", "info");
      return;
    }

    let confirmMsg = `This will move ${total} file(s) in ${target}`;
    if (currentScanModeDeep) {
      confirmMsg += " and remove any subfolders left empty afterward";
    }
    confirmMsg += ". Continue?";

    // Show interactive confirmation modal (mimics (y/n) in terminal)
    const confirmed = await openConfirmModal(confirmMsg);
    if (!confirmed) {
      appendTerminalLog("Cancelled. No files were moved.", "text-slate-400");
      showToast("Cancelled", "Clean cancelled. No files were moved.", "info");
      return;
    }

    // Run real clean
    await executeRealClean(target, currentScanModeDeep);

  } catch (e) {
    showLiveProgress(false);
    appendTerminalLog(`[ERROR] ${e.message}`, "text-rose-400 font-bold");
    showToast("Error", e.message, "error");
  }
}

// Real clean executor
async function executeRealClean(target, deep) {
  showLiveProgress(true, "Moving Files (Clean)");
  try {
    const res = await fetch("/api/organize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_dir: target, deep: deep, quiet: false })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Organization failed");
    }

    const data = await res.json();
    currentPreviewFiles = data.files || [];
    renderPreviewTable(currentPreviewFiles);
    updateCharts(data.counts, data.sizes, data.total_files, data.total_bytes_formatted);

    document.getElementById("stat-total-files").innerText = data.total_files;
    document.getElementById("stat-total-size").innerText = data.total_bytes_formatted;

  } catch (e) {
    showLiveProgress(false);
    appendTerminalLog(`[ERROR] ${e.message}`, "text-rose-400 font-bold");
    showToast("Execution Error", e.message, "error");
  }
}

// Mode 2 & Mode 3: Dry Run & Summary Only
async function triggerScan(quiet = false) {
  const target = document.getElementById("target-dir-input").value.trim();
  if (!target) {
    showToast("Missing Folder", "Please choose or enter a directory path first.", "error");
    return;
  }

  const modeName = quiet ? "Summary Only" : "Dry Run (Preview)";
  appendTerminalLog(`\n[Action: ${modeName}] Initiating on ${target} (Deep: ${currentScanModeDeep})...`, "text-sky-300 font-semibold");
  showLiveProgress(true, modeName);

  try {
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_dir: target, deep: currentScanModeDeep, quiet: quiet })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Scan failed");
    }

    const data = await res.json();
    currentPreviewFiles = data.files || [];
    renderPreviewTable(currentPreviewFiles);
    updateCharts(data.counts, data.sizes, data.total_files, data.total_bytes_formatted);

    document.getElementById("stat-total-files").innerText = data.total_files;
    document.getElementById("stat-total-size").innerText = data.total_bytes_formatted;

    if (!quiet) {
      showToast("Dry Run Complete", `Inspected ${data.total_files} files ready to organize.`, "success");
    } else {
      showToast("Summary Ready", `Counted ${data.total_files} files.`, "info");
    }
  } catch (e) {
    showLiveProgress(false);
    appendTerminalLog(`[ERROR] ${e.message}`, "text-rose-400 font-bold");
    showToast("Scan Failed", e.message, "error");
  }
}

// Quick Undo Last
async function triggerUndoLast() {
  try {
    const historyRes = await fetch("/api/history");
    const historyData = await historyRes.json();
    const activeRuns = historyData.filter(r => !r.undone && r.total_files > 0);

    if (activeRuns.length === 0) {
      showToast("No Runs to Undo", "There are no recent operations available to rollback.", "info");
      return;
    }

    const lastRun = activeRuns[0];
    const confirmed = await openConfirmModal(`Are you sure you want to revert run ${lastRun.run_id}? (${lastRun.total_files} files)`);
    if (confirmed) {
      await triggerUndo(lastRun.run_id);
    }
  } catch (e) {
    showToast("Undo Failed", e.message, "error");
  }
}

async function triggerUndo(runId) {
  appendTerminalLog(`\n[TRIGGER] Reverting Run ${runId}...`, "text-amber-400 font-semibold");
  try {
    const res = await fetch(`/api/history/${runId}/undo`, { method: "POST" });
    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data.message || "Failed to rollback run");
    }

    loadHistory();
  } catch (e) {
    showToast("Rollback Error", e.message, "error");
    appendTerminalLog(`[ERROR] Undo failed: ${e.message}`, "text-rose-400");
  }
}

// ==========================================
// 4. CONFIRMATION MODAL (TERMINAL Y/N)
// ==========================================
function openConfirmModal(text) {
  return new Promise((resolve) => {
    const modal = document.getElementById("confirm-modal");
    const textElem = document.getElementById("confirm-modal-text");
    if (!modal || !textElem) {
      resolve(true);
      return;
    }

    textElem.innerText = text;
    modal.classList.remove("hidden");
    confirmResolveCallback = resolve;
  });
}

function closeConfirmModal(accepted) {
  const modal = document.getElementById("confirm-modal");
  if (modal) modal.classList.add("hidden");
  if (confirmResolveCallback) {
    confirmResolveCallback(accepted);
    confirmResolveCallback = null;
  }
}

// ==========================================
// 5. CHARTS (CHART.JS)
// ==========================================
function initCharts() {
  const ctxDist = document.getElementById("categoryDistributionChart")?.getContext("2d");
  const ctxStor = document.getElementById("categoryStorageChart")?.getContext("2d");

  if (ctxDist) {
    distributionChartInstance = new Chart(ctxDist, {
      type: "doughnut",
      data: {
        labels: [],
        datasets: [{
          data: [],
          backgroundColor: Object.values(categoryColors),
          borderWidth: 2,
          borderColor: "#0f172a"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "right",
            labels: { color: "#94a3b8", boxWidth: 12, font: { size: 11 } }
          }
        },
        cutout: "68%"
      }
    });
  }

  if (ctxStor) {
    storageChartInstance = new Chart(ctxStor, {
      type: "bar",
      data: {
        labels: [],
        datasets: [{
          label: "Size (MB)",
          data: [],
          backgroundColor: "#818cf8",
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: "#94a3b8", font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { color: "#94a3b8", font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.05)" } }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }
}

function updateCharts(counts, sizes, totalFiles, totalSizeFormatted) {
  const labels = Object.keys(counts).filter(k => counts[k] > 0);
  const countValues = labels.map(k => counts[k]);
  const sizeMBValues = labels.map(k => ((sizes[k] || 0) / (1024 * 1024)).toFixed(2));
  const colors = labels.map(k => categoryColors[k] || "#6366f1");

  document.getElementById("chart-file-total-label").innerText = `${totalFiles} total files`;
  document.getElementById("chart-size-total-label").innerText = totalSizeFormatted;

  if (distributionChartInstance) {
    distributionChartInstance.data.labels = labels;
    distributionChartInstance.data.datasets[0].data = countValues;
    distributionChartInstance.data.datasets[0].backgroundColor = colors;
    distributionChartInstance.update();
  }

  if (storageChartInstance) {
    storageChartInstance.data.labels = labels;
    storageChartInstance.data.datasets[0].data = sizeMBValues;
    storageChartInstance.data.datasets[0].backgroundColor = colors;
    storageChartInstance.update();
  }
}

function updateChartsFromLiveCounts(counts, sizes) {
  if (!counts) return;
  const labels = Object.keys(counts).filter(k => counts[k] > 0);
  const countValues = labels.map(k => counts[k]);
  const sizeMBValues = labels.map(k => ((sizes[k] || 0) / (1024 * 1024)).toFixed(2));
  const colors = labels.map(k => categoryColors[k] || "#6366f1");

  if (distributionChartInstance) {
    distributionChartInstance.data.labels = labels;
    distributionChartInstance.data.datasets[0].data = countValues;
    distributionChartInstance.data.datasets[0].backgroundColor = colors;
    distributionChartInstance.update("none");
  }

  if (storageChartInstance) {
    storageChartInstance.data.labels = labels;
    storageChartInstance.data.datasets[0].data = sizeMBValues;
    storageChartInstance.data.datasets[0].backgroundColor = colors;
    storageChartInstance.update("none");
  }
}

// ==========================================
// 6. REST API DATA LOADERS
// ==========================================
async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    document.getElementById("stat-total-runs").innerText = data.total_runs || 0;
  } catch (e) {
    console.error("Failed to load status:", e);
  }
}

async function loadDrives() {
  try {
    const res = await fetch("/api/drives");
    const data = await res.json();
    renderQuickLocations(data.quick_locations || []);
  } catch (e) {
    console.error("Failed to load drives:", e);
  }
}

function renderQuickLocations(locations) {
  const container = document.getElementById("quick-locations-container");
  if (!container) return;

  container.innerHTML = "";
  locations.forEach(loc => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "px-3.5 py-1.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-700/80 text-xs font-semibold text-slate-300 hover:text-white transition flex items-center space-x-1.5 shadow-sm";
    btn.innerHTML = `<i data-lucide="folder" class="w-3.5 h-3.5 text-indigo-400"></i><span>${escapeHtml(loc.name)}</span>`;
    btn.onclick = () => {
      document.getElementById("target-dir-input").value = loc.path;
      document.getElementById("watcher-target-input").value = loc.path;
      appendTerminalLog(`[Selected Target] ${loc.name} -> ${loc.path}`, "text-slate-300");
    };
    container.appendChild(btn);
  });

  const input = document.getElementById("target-dir-input");
  if (input && !input.value && locations.length > 0) {
    input.value = locations[0].path;
    document.getElementById("watcher-target-input").value = locations[0].path;
  }

  lucide.createIcons();
}

// ==========================================
// 7. PREVIEW & DIFF TABLE
// ==========================================
function renderPreviewTable(files) {
  const tbody = document.getElementById("preview-table-body");
  const badge = document.getElementById("preview-count-badge");
  const categoryFilter = document.getElementById("preview-category-filter");
  if (!tbody) return;

  if (badge) {
    badge.innerText = files.length;
    badge.classList.remove("hidden");
  }

  const categoriesSet = new Set(files.map(f => f.category));
  if (categoryFilter) {
    categoryFilter.innerHTML = `<option value="ALL">All Categories (${files.length})</option>`;
    categoriesSet.forEach(cat => {
      const count = files.filter(f => f.category === cat).length;
      categoryFilter.innerHTML += `<option value="${cat}">${cat} (${count})</option>`;
    });
  }

  filterPreviewTable();
}

function filterPreviewTable() {
  const tbody = document.getElementById("preview-table-body");
  const query = document.getElementById("preview-search-input")?.value.toLowerCase() || "";
  const catFilter = document.getElementById("preview-category-filter")?.value || "ALL";

  if (!tbody) return;

  const filtered = currentPreviewFiles.filter(f => {
    const matchName = f.name.toLowerCase().includes(query) || f.src.toLowerCase().includes(query);
    const matchCat = catFilter === "ALL" || f.category === catFilter;
    return matchName && matchCat;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-slate-500 text-xs">No matching files found.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(f => {
    const color = categoryColors[f.category] || "#6366f1";
    const statusBadge = f.status === "moved"
      ? `<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-medium">Moved</span>`
      : `<span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-medium">Preview</span>`;

    return `
      <tr class="hover:bg-slate-800/40 transition">
        <td class="p-3 font-medium text-white break-all">${escapeHtml(f.name)}</td>
        <td class="p-3">
          <span class="px-2 py-0.5 rounded-full text-xs font-semibold" style="background-color: ${color}20; color: ${color}; border: 1px solid ${color}40">
            ${f.category}
          </span>
        </td>
        <td class="p-3 font-mono text-slate-400">${f.size_formatted}</td>
        <td class="p-3 text-slate-400 break-all text-xs font-mono">${escapeHtml(f.src)}</td>
        <td class="p-3 text-emerald-400 break-all text-xs font-mono">${escapeHtml(f.dest_path)}</td>
        <td class="p-3">${statusBadge}</td>
      </tr>
    `;
  }).join("");
}

// ==========================================
// 8. HISTORY & UNDO SYSTEM
// ==========================================
async function loadHistory() {
  const container = document.getElementById("history-container");
  if (!container) return;

  try {
    const res = await fetch("/api/history");
    const historyList = await res.json();

    if (historyList.length === 0) {
      container.innerHTML = `<div class="text-center py-8 text-slate-500 text-xs">No organizer runs recorded yet.</div>`;
      return;
    }

    container.innerHTML = historyList.map(run => {
      const date = new Date(run.timestamp).toLocaleString();
      const isUndone = run.undone;
      const undoBtn = isUndone
        ? `<span class="px-2.5 py-1 rounded bg-slate-800 text-slate-500 text-xs font-medium">Reverted</span>`
        : `<button onclick="confirmAndUndo('${run.run_id}', ${run.total_files})" class="px-3 py-1 bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 rounded-lg text-xs font-semibold transition flex items-center space-x-1">
             <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
             <span>Rollback (Undo)</span>
           </button>`;

      return `
        <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:border-slate-700 transition">
          <div class="space-y-1">
            <div class="flex items-center space-x-2">
              <span class="text-xs font-mono font-bold text-indigo-400">${escapeHtml(run.run_id)}</span>
              <span class="text-xs px-2 py-0.5 rounded-full ${run.deep ? 'bg-purple-500/20 text-purple-300' : 'bg-slate-800 text-slate-300'} font-medium">
                ${run.deep ? 'Deep Scan' : 'Standard'}
              </span>
            </div>
            <p class="text-xs text-slate-400 font-mono">${escapeHtml(run.target_dir)}</p>
            <p class="text-xs text-slate-500">${date} &bull; <strong class="text-slate-300">${run.total_files} files moved</strong></p>
          </div>
          <div>${undoBtn}</div>
        </div>
      `;
    }).join("");

    lucide.createIcons();
  } catch (e) {
    console.error("Error loading history:", e);
  }
}

async function confirmAndUndo(runId, fileCount) {
  const confirmed = await openConfirmModal(`Revert run ${runId} and move ${fileCount} file(s) back to original locations?`);
  if (confirmed) {
    await triggerUndo(runId);
  }
}

// ==========================================
// 9. BACKGROUND WATCHER DAEMON
// ==========================================
async function loadWatchers() {
  const container = document.getElementById("active-watchers-list");
  const badge = document.getElementById("watchers-badge");
  const badgeText = document.getElementById("watchers-count-text");

  try {
    const res = await fetch("/api/watchers");
    const watchers = await res.json();

    if (badge && badgeText) {
      if (watchers.length > 0) {
        badge.classList.remove("hidden");
        badge.classList.add("flex");
        badgeText.innerText = `${watchers.length} Active Watcher${watchers.length > 1 ? 's' : ''}`;
      } else {
        badge.classList.add("hidden");
        badge.classList.remove("flex");
      }
    }

    if (!container) return;

    if (watchers.length === 0) {
      container.innerHTML = `<div class="text-slate-500 text-xs py-4 text-center">No active folder watchers running.</div>`;
      return;
    }

    container.innerHTML = watchers.map(w => `
      <div class="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <div>
            <p class="text-xs font-mono font-medium text-white">${escapeHtml(w.path)}</p>
            <p class="text-xs text-slate-400">Mode: ${w.deep ? 'Recursive' : 'Root only'} &bull; Started: ${w.started_at}</p>
          </div>
        </div>
        <button onclick="stopWatcher('${escapeHtml(w.path)}')" class="px-3 py-1 bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white rounded-lg text-xs font-medium transition">
          Stop
        </button>
      </div>
    `).join("");
  } catch (e) {
    console.error("Error loading watchers:", e);
  }
}

async function startWatcherFromInput() {
  const path = document.getElementById("watcher-target-input").value.trim();
  const deep = document.getElementById("watcher-deep-select").value === "true";

  if (!path) {
    showToast("Missing Folder", "Please specify a folder to monitor.", "error");
    return;
  }

  try {
    const res = await fetch("/api/watchers/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_dir: path, deep: deep })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to start watcher");

    showToast("Watcher Active", `Now monitoring ${path} in the background.`, "success");
    loadWatchers();
  } catch (e) {
    showToast("Watcher Error", e.message, "error");
  }
}

async function stopWatcher(path) {
  try {
    const res = await fetch("/api/watchers/stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_dir: path })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to stop watcher");

    showToast("Watcher Stopped", `Stopped monitoring ${path}`, "info");
    loadWatchers();
  } catch (e) {
    showToast("Stop Error", e.message, "error");
  }
}

// ==========================================
// 10. CATEGORY RULES MANAGER
// ==========================================
async function loadCategories() {
  const container = document.getElementById("category-rules-container");
  if (!container) return;

  try {
    const res = await fetch("/api/categories");
    const data = await res.json();
    categoriesData = data.categories;

    document.getElementById("stat-active-categories").innerText = Object.keys(categoriesData).length;

    container.innerHTML = Object.entries(categoriesData).map(([cat, exts]) => {
      const color = categoryColors[cat] || "#6366f1";
      return `
        <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
          <div class="flex items-center justify-between">
            <h4 class="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${color}"></span>
              <span>${cat}</span>
            </h4>
            <span class="text-xs text-slate-500 font-mono">${exts.length} ext</span>
          </div>
          <textarea id="cat-edit-${cat}" rows="2" class="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs font-mono text-slate-300 focus:outline-none focus:border-indigo-500">${exts.join(", ")}</textarea>
        </div>
      `;
    }).join("");
  } catch (e) {
    console.error("Error loading categories:", e);
  }
}

async function saveCategoriesFromUI() {
  const updatedCategories = {};
  for (const cat of Object.keys(categoriesData)) {
    const txt = document.getElementById(`cat-edit-${cat}`)?.value || "";
    const exts = txt.split(",")
      .map(e => e.trim().toLowerCase())
      .map(e => e.startsWith(".") ? e : "." + e)
      .filter(e => e.length > 1);
    updatedCategories[cat] = exts;
  }

  try {
    const res = await fetch("/api/categories", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ categories: updatedCategories, misc_category: "Misc" })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to save categories");

    showToast("Saved", "Category rules updated successfully.", "success");
    loadCategories();
  } catch (e) {
    showToast("Save Error", e.message, "error");
  }
}

// ==========================================
// 11. NAVIGATION & TOASTS
// ==========================================
function switchTab(tabId) {
  const tabs = ["dashboard", "preview", "history", "watcher", "rules"];
  tabs.forEach(t => {
    const content = document.getElementById(`tab-content-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (content) content.classList.add("hidden");
    if (btn) {
      btn.className = "tab-btn px-4 py-2 rounded-lg text-sm font-medium transition flex items-center space-x-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50";
    }
  });

  const activeContent = document.getElementById(`tab-content-${tabId}`);
  const activeBtn = document.getElementById(`tab-btn-${tabId}`);
  if (activeContent) activeContent.classList.remove("hidden");
  if (activeBtn) {
    activeBtn.className = "tab-btn active px-4 py-2 rounded-lg text-sm font-medium transition flex items-center space-x-2 bg-indigo-600/20 text-indigo-400 border border-indigo-500/30";
  }

  lucide.createIcons();
}

function showToast(title, message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  const colors = {
    success: "bg-slate-900 border-emerald-500/50 text-emerald-300",
    error: "bg-slate-900 border-rose-500/50 text-rose-300",
    info: "bg-slate-900 border-indigo-500/50 text-indigo-300"
  };

  toast.className = `p-4 rounded-xl border shadow-2xl backdrop-blur max-w-sm pointer-events-auto transform transition-all duration-300 translate-y-2 opacity-0 ${colors[type] || colors.info}`;
  toast.innerHTML = `
    <div class="font-bold text-xs uppercase tracking-wider text-white">${escapeHtml(title)}</div>
    <div class="text-xs text-slate-300 mt-0.5">${escapeHtml(message)}</div>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.remove("translate-y-2", "opacity-0");
  }, 10);

  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-x-4");
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

