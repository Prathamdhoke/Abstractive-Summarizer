(() => {
  "use strict";

  const HISTORY_KEY = "summarizer.history";
  const THEME_KEY = "summarizer.theme";
  const MAX_HISTORY = 20;

  // ---------- Elements ----------
  const els = {
    themeToggle: document.getElementById("theme-toggle"),
    historyToggle: document.getElementById("history-toggle"),
    historyPanel: document.getElementById("history-panel"),
    historyList: document.getElementById("history-list"),
    historyEmpty: document.getElementById("history-empty"),
    clearHistory: document.getElementById("clear-history"),

    tabs: document.querySelectorAll(".tab"),
    panels: document.querySelectorAll(".tab-panel"),

    textInput: document.getElementById("dialogue-input"),
    wordCount: document.getElementById("word-count"),

    dropzone: document.getElementById("dropzone"),
    fileInput: document.getElementById("file-input"),
    dropzoneFilename: document.getElementById("dropzone-filename"),

    lengthOpts: document.querySelectorAll(".length-opt"),
    summarizeBtn: document.getElementById("summarize-btn"),
    inputError: document.getElementById("input-error"),

    emptyState: document.getElementById("empty-state"),
    result: document.getElementById("result"),
    outputActions: document.getElementById("output-actions"),
    summaryText: document.getElementById("summary-text"),
    statOriginal: document.getElementById("stat-original"),
    statSummary: document.getElementById("stat-summary"),
    statCutValue: document.getElementById("stat-cut-value"),
    cutRingFill: document.getElementById("cut-ring-fill"),
    readingTimeLine: document.getElementById("reading-time-line"),

    copyBtn: document.getElementById("copy-btn"),
    downloadBtn: document.getElementById("download-btn"),
    toast: document.getElementById("toast"),
  };

  let state = {
    activeTab: "paste",
    length: "medium",
    file: null,
    lastSummary: "",
  };

  // ---------- Theme ----------
  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const theme = saved || (prefersDark ? "dark" : "light");
    applyTheme(theme);
  }
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }
  els.themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    applyTheme(current === "dark" ? "light" : "dark");
  });

  // ---------- Tabs ----------
  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const name = tab.dataset.tab;
      state.activeTab = name;
      els.tabs.forEach((t) => {
        t.classList.toggle("is-active", t === tab);
        t.setAttribute("aria-selected", t === tab ? "true" : "false");
      });
      els.panels.forEach((p) => p.classList.toggle("is-active", p.dataset.panel === name));
      clearError();
    });
  });

  // ---------- Word count ----------
  function countWords(text) {
    const trimmed = text.trim();
    return trimmed ? trimmed.split(/\s+/).length : 0;
  }
  els.textInput.addEventListener("input", () => {
    els.wordCount.textContent = `${countWords(els.textInput.value)} words`;
  });

  // ---------- Length picker ----------
  els.lengthOpts.forEach((btn) => {
    btn.addEventListener("click", () => {
      state.length = btn.dataset.length;
      els.lengthOpts.forEach((b) => b.classList.toggle("is-active", b === btn));
    });
  });

  // ---------- File upload / dropzone ----------
  function setFile(file) {
    state.file = file || null;
    els.dropzoneFilename.textContent = file ? `Selected: ${file.name}` : "";
  }
  els.fileInput.addEventListener("change", () => setFile(els.fileInput.files[0]));

  ["dragenter", "dragover"].forEach((evt) =>
    els.dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      els.dropzone.classList.add("is-dragover");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    els.dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      els.dropzone.classList.remove("is-dragover");
    })
  );
  els.dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) {
      els.fileInput.files = e.dataTransfer.files;
      setFile(file);
    }
  });

  // ---------- Error / toast ----------
  function showError(msg) {
    els.inputError.textContent = msg;
  }
  function clearError() {
    els.inputError.textContent = "";
  }
  let toastTimer;
  function showToast(msg) {
    els.toast.textContent = msg;
    els.toast.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => els.toast.classList.remove("is-visible"), 2200);
  }

  // ---------- Summarize ----------
  function setLoading(isLoading) {
    els.summarizeBtn.disabled = isLoading;
    els.summarizeBtn.classList.toggle("is-loading", isLoading);
  }

  async function handleSummarize() {
    clearError();

    if (state.activeTab === "paste") {
      const text = els.textInput.value.trim();
      if (!text) {
        showError("Paste some text first.");
        return;
      }
      await runSummarize(() =>
        fetch("/api/summarize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, length: state.length }),
        })
      );
    } else {
      if (!state.file) {
        showError("Choose a file first.");
        return;
      }
      const formData = new FormData();
      formData.append("file", state.file);
      formData.append("length", state.length);
      await runSummarize(() => fetch("/api/summarize-file", { method: "POST", body: formData }));
    }
  }

  async function runSummarize(makeRequest) {
    setLoading(true);
    try {
      const response = await makeRequest();
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || `Server error (${response.status})`);
      }
      renderResult(data);
      saveToHistory(data);
    } catch (err) {
      showError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  els.summarizeBtn.addEventListener("click", handleSummarize);

  // ---------- Render result ----------
  const RING_CIRCUMFERENCE = 2 * Math.PI * 30;

  function renderResult(data) {
    state.lastSummary = data.summary;

    els.emptyState.hidden = true;
    els.result.hidden = false;
    els.outputActions.hidden = false;

    els.summaryText.textContent = data.summary;
    els.statOriginal.textContent = data.original_word_count.toLocaleString();
    els.statSummary.textContent = data.summary_word_count.toLocaleString();
    els.statCutValue.textContent = `${Math.round(data.reduction_percent)}%`;

    const clamped = Math.max(0, Math.min(100, data.reduction_percent));
    const offset = RING_CIRCUMFERENCE * (1 - clamped / 100);
    els.cutRingFill.style.strokeDasharray = String(RING_CIRCUMFERENCE);
    els.cutRingFill.style.strokeDashoffset = String(RING_CIRCUMFERENCE);
    requestAnimationFrame(() => {
      els.cutRingFill.style.strokeDashoffset = String(offset);
    });

    const secs = data.estimated_reading_time_saved_sec || 0;
    els.readingTimeLine.textContent =
      secs > 0 ? `≈ ${formatDuration(secs)} of reading time saved.` : "";
  }

  function formatDuration(totalSeconds) {
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    if (m === 0) return `${s}s`;
    return `${m}m ${s}s`;
  }

  // ---------- Copy / download ----------
  els.copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(state.lastSummary);
      showToast("Copied to clipboard");
    } catch {
      showToast("Couldn't copy — select the text manually");
    }
  });

  els.downloadBtn.addEventListener("click", () => {
    const blob = new Blob([state.lastSummary], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "summary.txt";
    a.click();
    URL.revokeObjectURL(url);
  });

  // ---------- History (localStorage, this browser only) ----------
  function loadHistory() {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    } catch {
      return [];
    }
  }
  function saveToHistory(data) {
    const items = loadHistory();
    items.unshift({
      summary: data.summary,
      original_word_count: data.original_word_count,
      summary_word_count: data.summary_word_count,
      reduction_percent: data.reduction_percent,
      ts: Date.now(),
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, MAX_HISTORY)));
    renderHistory();
  }
  function renderHistory() {
    const items = loadHistory();
    els.historyList.innerHTML = "";
    els.historyEmpty.hidden = items.length > 0;

    items.forEach((item) => {
      const li = document.createElement("li");
      li.className = "history-item";
      const time = document.createElement("time");
      time.textContent = new Date(item.ts).toLocaleString(undefined, {
        month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
      });
      const p = document.createElement("p");
      p.textContent = item.summary;
      li.append(time, p);
      li.addEventListener("click", () => {
        renderResult({
          summary: item.summary,
          original_word_count: item.original_word_count,
          summary_word_count: item.summary_word_count,
          reduction_percent: item.reduction_percent,
          estimated_reading_time_saved_sec: 0,
        });
        els.historyPanel.hidden = true;
        els.historyToggle.setAttribute("aria-expanded", "false");
      });
      els.historyList.appendChild(li);
    });
  }

  els.historyToggle.addEventListener("click", () => {
    const willShow = els.historyPanel.hidden;
    els.historyPanel.hidden = !willShow;
    els.historyToggle.setAttribute("aria-expanded", String(willShow));
  });
  els.clearHistory.addEventListener("click", () => {
    localStorage.removeItem(HISTORY_KEY);
    renderHistory();
  });

  // ---------- Init ----------
  initTheme();
  renderHistory();
})();
