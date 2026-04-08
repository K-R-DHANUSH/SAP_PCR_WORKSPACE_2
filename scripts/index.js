/// --------------------------------------------------------------------------------------------------------------------
// SAP PCR Workspace — Rebuilt from ORIGINAL + AI & Insert Popup (single-file index.js)
// - Restores original tree & attributes behavior
// - Adds AI generator (safe) and Insert popup (Same level / Sub-level)
// - Defensive: avoids duplicate declarations and hard failures
/// --------------------------------------------------------------------------------------------------------------------

(function () {
  "use strict";

  // --- small helper for safe DOM lookup
  const $ = (id) => document.getElementById(id);

  // Temporary global error logger (keeps console tidy)
  window.onerror = function (msg, src, line, col, err) {
    console.error("GLOBAL JS ERROR:", { message: msg, source: src, line, col, err });
  };

  document.addEventListener("DOMContentLoaded", () => {

    // ----------------------------
    // DOM references (defensive)
    // ----------------------------
    const ruleIdInput   = $("rule-id");
    const ruleTextInput = $("rule-text");
    const ruleESGrpInput= $("rule-esgrp");
    const ruleWTInput   = $("rule-wt");
    const headerHint    = $("pcr-header-hint") || $("header-hint");
    const headerScreen  = $("pcr-header-screen") || $("header-screen");
    const workspaceArea = $("workspace-area") || $("workspace");

    const editor   = $("pcr-editor");
    const treePreviewEl = $("tree-preview") || $("tree-view");
    const panelCenter = $("panel-center");

    // toolbar & buttons (guarded)
    const btnChangeMode   = $("btn-mode") || $("btn-change-mode");
    const btnCheck        = $("btn-check");
    const btnCreate       = $("btn-create");
    const btnDelete       = $("btn-delete");
    const btnCut          = $("btn-cut");
    const btnCopyBuffer   = $("btn-copy-buffer");
    const btnPaste        = $("btn-paste");
    const btnInsertExample= $("btn-insert-example");
    const btnTreeView     = $("btn-tree-view");
    const btnEditorView   = $("btn-editor-view");
    const btnReassign     = $("btn-reassign");
    const btnExport       = $("btn-export");
    const btnImport       = $("btn-import");
    const btnPing         = $("btn-ping");
    const btnDiag         = $("btn-diagnostics");
    const btnLayout       = $("btn-layout");
    const btnPlus         = $("btn-plus");
    const btnMoveUp       = $("btn-move-up");
    const btnMoveDown     = $("btn-move-down");
    const btnBeautify     = $("btn-beautify");
    const btnMinify       = $("btn-minify");
    const btnRename       = $("btn-rename");
    const btnAttributes   = $("btn-attributes");
    const btnDoc          = $("btn-doc");
    const btnExplain      = $("btn-explain");
    const btnOperand      = $("btn-operand");

    // insert popup buttons (optional)
    const insertPopup     = $("insert-popup");
    const insertSameBtn   = $("insert-same");
    const insertSubBtn    = $("insert-sub");
    const insertCancelBtn = $("insert-cancel");

    // modals & panels
    const opLibModal    = $("oplib-modal");
    const opLibTitle    = $("oplib-title");
    const opLibBody     = $("oplib-body");
    const opLibClose    = $("oplib-close");

    const attrModal     = $("attr-modal");
    const attrClose     = $("attr-close");
    const attrRule      = $("attr-rule");
    const attrRuleText  = $("attr-rule-text");
    const attrCreated   = $("attr-created");
    const attrChanged   = $("attr-changed");

    const docModal      = $("doc-modal");
    const docClose      = $("doc-close");
    const docText       = $("doc-text");

    const reassignModal = $("reassign-modal");
    const reassignClose = $("reassign-close");
    const reassignFrom  = $("reassign-from");
    const reassignTo    = $("reassign-to");
    const reassignOk    = $("reassign-ok");

    const renameModal   = $("rename-modal");
    const renameClose   = $("rename-close");
    const renameOk      = $("rename-ok");
    const renameRuleId  = $("rename-rule-id");

    // AI UI
    const aiPromptEl    = $("ai-prompt");
    const aiGenerateBtn = $("ai-generate-btn");
    const aiStatusEl    = $("ai-status");
    const aiPreviewEl   = $("ai-pcr-preview");
    const aiCopyBtn     = $("ai-copy-btn");
    const aiClearBtn    = $("ai-clear-btn");

    const aiWelcome     = $("ai-welcome");
    const overviewEl    = null;
    const structureEl   = null;
    const hintsEl       = $("ai-issues");
    const runtimeEl     = $("ai-runtime");

    const statusLines   = $("status-lines");
    const statusCursor  = $("status-cursor");
    const statusMode    = $("status-mode");
    const themeSelect   = $("theme-select");
    const minimap       = $("minimap");

    // Suggest box
    const suggestBox = $("inline-suggest");

    // Safety warnings for missing optional UI
    if (!editor) console.warn("Warning: editor element (pcr-editor) not found.");
    if (!treePreviewEl) console.warn("Warning: tree preview element not found.");
    if (!aiGenerateBtn && (aiPromptEl || aiPreviewEl || aiCopyBtn)) console.warn("AI panel present but some AI buttons are missing.");

    // ----------------------------
    // Backend config
    // ----------------------------
    const API = (() => {
  const host = window.location.hostname;

  // ✅ 1. GitHub Pages (PRODUCTION - HIGHEST PRIORITY)
  if (host.includes("github.io")) {
    return "https://sap-pcr-workspace-2-github-io.onrender.com";
  }

  // ✅ 2. Codespaces (DEV)
  if (host.includes("github.dev") || host.includes("app.github.dev")) {
    return `https://${window.location.host.replace("-3000", "-8000")}`;
  }

  // ✅ 3. Localhost (DEV)
  if (host.includes("localhost") || host.includes("127.0.0.1")) {
    return "http://localhost:8000";
  }

  // ✅ 4. Fallback (safe default)
  return "https://sap-pcr-workspace-2-github-io.onrender.com";
})();

    function apiNotConfigured() {
      return !API || String(API).trim() === "";
    }

    // ----------------------------
    // State
    // ----------------------------
    let blocks = []; // { text, indent }
    let isChangeMode = true;
    let clipboardBlocks = null;

    // Inline edit
    let inlineCell = null;
    let inlineOrigText = "";
    let suggestIndex = 0;

    // Selection/insert
    let pendingInsertIndex = null;
    const createdOn = new Date();
    let lastChanged = createdOn;
    let insertionAnchor = null; // used for mouse hover

    // Opcode meta cache
    let OPCODE_META = null;

    // ----------------------------
    // Utilities
    // ----------------------------
    function escapeHtml(s) {
      return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
    function formatDate(d) {
      if (!d) return "";
      return (d instanceof Date) ? d.toLocaleString() : new Date(d).toLocaleString();
    }
    function buildIndentGlyph(level) {
      if (!level || level < 1) return "";
      return "│   ".repeat(Math.max(0, level - 1)) + "└── ";
    }

    // ----------------------------
    // Known opcodes set (preserve original)
    // ----------------------------
    const ALL_OPS = [
      "AMT=", "AMT+", "AMT-", "AMT*", "AMT/",
      "NUM=", "NUM+", "NUM-", "NUM*", "NUM/",
      "RTE=", "RTE*", "RTE/", "DIVI",
      "ADDWT", "SUBWT", "ZERO=", "OUTWP", "OUTWPP",
      "IF", "ELSE", "ENDIF", "MULTI", "PRINT", "TABLE", "SUPPRESS"
    ];
    function isKnownOpcode(code) {
      return ALL_OPS.includes(String(code).toUpperCase());
    }

    // ----------------------------
    // Parse a line for inline desc / type
    // ----------------------------
    function parseLineForDesc(line) {
      const t = (line || "").trim();
      if (!t) return null;
      if (/^\/\d{4}/.test(t)) {
        const parts = t.split(/\s+/);
        return { type: "wt", wageType: parts[0].substring(1), rest: parts.slice(1).join(" ") };
      }
      const parts = t.split(/\s+/);
      const op = parts[0].toUpperCase();
      const operand = parts.slice(1).join(" ");
      if (!isKnownOpcode(op)) return { type: "unknown", op };
      return { type: "op", op, operand };
    }

    function inlineDescription(line) {
      const info = parseLineForDesc(line);
      if (!info) return "";
      if (info.type === "wt") return `Node for wage type ${info.wageType}`;
      if (info.type === "op") {
        switch (info.op) {
          case "ADDWT": return info.operand ? `Add result to WT ${info.operand}` : "Add result to calling wage type.";
          case "AMT=": return `Set AMT to ${info.operand || "value"}`;
          case "NUM=": return `Set NUM to ${info.operand || "value"}`;
          case "RTE=": return `Set RTE to ${info.operand || "value"}`;
          default: return "";
        }
      }
      return "";
    }

    // Disable all previous saved PCR data – start fresh always
localStorage.removeItem("pcr_workspace");
localStorage.removeItem("pcr_blocks");
localStorage.removeItem("pcr_editor");
localStorage.clear();   // optional: clears everything
sessionStorage.clear(); // optional: clears session

    // ----------------------------
    // Sync editor <-> blocks
    // ----------------------------
    function syncBlocksFromEditor() {
      if (!editor) return;
      const lines = editor.value.replace(/\r/g, "").split("\n");
      if (!Array.isArray(lines)) return;
      blocks = lines.map(line => ({ text: line, indent: 0 }));
      renderTable();
      analyze(false);
    }
    function syncEditor() {
      if (!editor) return;
      editor.value = blocks.map(b => b.text).join("\n");
      updateMinimap();
    }

    // ----------------------------
    // Status update
    // ----------------------------
    function updateStatus(i) {
      const ln = blocks.length ? (i + 1) : 1;
      if (statusLines) statusLines.textContent = blocks.length;
      if (statusCursor) statusCursor.textContent = `${ln}:1`;
    }

    // ----------------------------
    // Selection helpers
    // ----------------------------
    function getSelectedIndex() {
      if (!treePreviewEl) return -1;
      const row = treePreviewEl.querySelector(".pcr-row.selected");
      if (!row) return -1;
      return parseInt(row.dataset.index, 10);
    }

    function isProtectedRoot(idx) {
      if (idx < 0 || idx >= blocks.length) return false;
      if (idx === 0) return true;
      const t = (blocks[idx].text || "").trim();
      if (t === "*") return true;
      if (/^\/\d+/.test(t)) return true;
      return false;
    }

    function selectRow(i) {
      stopInlineEdit(); // cleanup

      if (!treePreviewEl) return;
      treePreviewEl.querySelectorAll(".pcr-row").forEach(r => r.classList.remove("selected"));
      const row = treePreviewEl.querySelector(`.pcr-row[data-index="${i}"]`);
      if (row) row.classList.add("selected");

      const protectedRoot = isProtectedRoot(i);
      if (btnDelete) btnDelete.disabled = !isChangeMode || protectedRoot;
      if (btnCut) btnCut.disabled = !isChangeMode || protectedRoot;

      updateStatus(i);
      scrollRowIntoView(i);
    }

    // ----------------------------
    // Inline editing helpers (safe)
    // ----------------------------
    function saveCell(cell) {
      if (!cell) return;
      const row = cell.closest(".pcr-row");
      if (!row) return;
      const idx = parseInt(row.dataset.index, 10);
      blocks[idx].text = String(cell.textContent || "").trim();
      syncEditor();
      lastChanged = new Date();
      if (attrChanged) attrChanged.textContent = formatDate(lastChanged);
      analyze(false);
    }

    function startInlineEdit(i) {
      if (!isChangeMode) return;
      stopInlineEdit();

      if (!treePreviewEl) return;
      const row = treePreviewEl.querySelector(`.pcr-row[data-index="${i}"]`);
      if (!row) return;
      const cell = row.querySelector(".pcr-cell");
      if (!cell) return;

      inlineCell = cell;
      inlineOrigText = cell.textContent || "";

      try {
        cell.contentEditable = "true";
        if (cell.classList && cell.classList.add) cell.classList.add("pcr-cell-edit");
        cell.focus();
        placeCaretAtEnd(cell);
      } catch (e) {
        console.warn("startInlineEdit failed:", e);
      }

      cell.oninput = () => {
        const text = (cell.textContent || "").trim();
        const token = text.split(/\s+/)[0] || "";
        if (token) {
          showSuggestList(token, cell);
        } else {
          if (suggestBox && suggestBox.classList) suggestBox.classList.add("hidden");
        }
        const descSpan = row.querySelector(".pcr-desc");
        if (descSpan) {
          const d = inlineDescription(cell.textContent);
          descSpan.textContent = d ? "   " + d : "";
        }
      };

      cell.onkeydown = (e) => {
        const items = suggestBox ? Array.from(suggestBox.querySelectorAll(".inline-suggest-item")) : [];
        if ((e.key === "ArrowDown" || e.key === "ArrowUp") && items.length) {
          e.preventDefault();
          if (e.key === "ArrowDown") suggestIndex = (suggestIndex + 1) % items.length;
          else suggestIndex = (suggestIndex - 1 + items.length) % items.length;
          items.forEach(x => x.classList.remove("active"));
          items[suggestIndex].classList.add("active");
          return;
        }

        if (e.key === "Tab" && items.length) {
          e.preventDefault();
          const code = items[suggestIndex].textContent;
          applySuggestion(code, cell);
          placeCaretAtEnd(cell);
          return;
        }

        if (e.key === "Enter") {
          e.preventDefault();
          const textNow = (cell.textContent || "").trim();
          if (textNow) {
            saveCell(cell);
            const curIdx = i;
            const indent = blocks[curIdx].indent || 0;
            blocks.splice(curIdx + 1, 0, { text: "", indent });
            syncEditor();
            renderTable();
            selectRow(curIdx + 1);
            startInlineEdit(curIdx + 1);
            if (suggestBox && suggestBox.classList) suggestBox.classList.add("hidden");
            return;
          }

          const idx = i;
          stopInlineEdit();
          if (!isProtectedRoot(idx)) {
            blocks.splice(idx, 1);
            syncEditor();
          }
          renderTable();
          selectRow(Math.max(0, idx - 1));
          if (suggestBox && suggestBox.classList) suggestBox.classList.add("hidden");
          return;
        }

        if (e.key === "Escape") {
          e.preventDefault();
          try { cell.textContent = inlineOrigText; } catch (er) {}
          stopInlineEdit();
          renderTable();
          selectRow(i);
          if (suggestBox && suggestBox.classList) suggestBox.classList.add("hidden");
          return;
        }
      };

      cell.onblur = () => {
        const now = (cell.textContent || "").trim();
        const rowB = cell.closest(".pcr-row");
        const idx = rowB ? parseInt(rowB.dataset.index, 10) : -1;
        if (now) {
          saveCell(cell);
        } else if (idx >= 0 && !isProtectedRoot(idx)) {
          blocks.splice(idx, 1);
          syncEditor();
        } else {
          try { cell.textContent = inlineOrigText; } catch (e) {}
        }
        stopInlineEdit();
        renderTable();
        if (suggestBox && suggestBox.classList) suggestBox.classList.add("hidden");
      };
    }

    function stopInlineEdit() {
      if (!inlineCell) return;
      try {
        inlineCell.contentEditable = "false";
        if (inlineCell.classList && inlineCell.classList.remove) inlineCell.classList.remove("pcr-cell-edit");
        inlineCell.oninput = null;
        inlineCell.onkeydown = null;
        inlineCell.onblur = null;
      } catch (e) {
        console.warn("Inline edit cleanup failed (ignored):", e);
      } finally {
        inlineCell = null;
        inlineOrigText = "";
        suggestIndex = 0;
        if (suggestBox && suggestBox.classList) suggestBox.classList.add("hidden");
      }
    }

    function placeCaretAtEnd(el) {
      try {
        const range = document.createRange();
        range.selectNodeContents(el);
        range.collapse(false);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      } catch (e) { /* ignore */ }
    }

    // Suggestion utilities
    function buildSuggestionList(token) {
      const q = String(token || "").toUpperCase();
      if (!q) return [];
      const scored = ALL_OPS.map(code => {
        const up = code.toUpperCase();
        let score = 0;
        if (up.startsWith(q)) score = 2;
        else if (up.includes(q)) score = 1;
        return { code, score };
      }).filter(x => x.score > 0);
      scored.sort((a, b) => b.score - a.score || a.code.localeCompare(b.code));
      return scored.map(x => x.code);
    }

    function showSuggestList(token, cell) {
      if (!token) {
        if (suggestBox && suggestBox.classList) suggestBox.classList.add("hidden");
        return;
      }
      if (!cell || !cell.getBoundingClientRect) return;
      if (!document.body.contains(cell)) {
        if (suggestBox && suggestBox.classList) suggestBox.classList.add("hidden");
        return;
      }

      const list = buildSuggestionList(token);
      if (!list.length) {
        if (suggestBox && suggestBox.classList) suggestBox.classList.add("hidden");
        return;
      }

      if (!suggestBox) return;
      suggestBox.innerHTML = "";
      suggestIndex = 0;
      list.forEach((code, idx) => {
        const item = document.createElement("div");
        item.className = "inline-suggest-item";
        if (idx === 0) item.classList.add("active");
        item.textContent = code;
        item.addEventListener("mousedown", (e) => {
          e.preventDefault();
          applySuggestion(code, cell);
          placeCaretAtEnd(cell);
        });
        suggestBox.appendChild(item);
      });

      // Position box relative to panelCenter
      try {
        const cellRect = cell.getBoundingClientRect();
        const panelRect = panelCenter ? panelCenter.getBoundingClientRect() : { top: 0, left: 0 };
        suggestBox.style.position = "absolute";
        suggestBox.style.top = (cellRect.bottom - panelRect.top + 2) + "px";
        suggestBox.style.left = (cellRect.left - panelRect.left) + "px";
        suggestBox.style.width = Math.max(120, cellRect.width) + "px";
        suggestBox.classList.remove("hidden");
        suggestBox.style.opacity = 1;
      } catch (e) { /* ignore layout errors */ }
    }

    function applySuggestion(cmd, cell) {
      if (!cell) return;
      const current = cell.textContent;
      const rest = current.replace(/^\S+/, "").trim();
      cell.textContent = rest ? `${cmd} ${rest}` : cmd;
      saveCell(cell);
      const row = cell.closest(".pcr-row");
      if (row) {
        const descSpan = row.querySelector(".pcr-desc");
        if (descSpan) descSpan.textContent = "   " + (inlineDescription(cell.textContent) || "");
      }
    }

    // ----------------------------
    // Table rendering (original)
    // ----------------------------
    function renderTable() {
  if (!treePreviewEl) return;
  const prevSel = getSelectedIndex();
  treePreviewEl.innerHTML = "";

  blocks.forEach((b, i) => {
    const row = document.createElement("div");
    row.className = "pcr-row";
    row.dataset.index = i;

    const indentSpan = document.createElement("span");
    indentSpan.className = "pcr-indent";

    // ORIGINAL GLYPH LOGIC
    const indent = b.indent || 0;
    indentSpan.textContent =
      indent === 0 ? "" :
      indent === 1 ? "└── " :
      "│   ".repeat(indent - 1) + "└── ";

    const cell = document.createElement("span");
    cell.className = "pcr-cell";
    cell.textContent = b.text;

    const descSpan = document.createElement("span");
    descSpan.className = "pcr-desc";
    const d = inlineDescription(b.text);
    if (d) descSpan.textContent = "   " + d;

    cell.addEventListener("dblclick", () => {
      selectRow(i);
      startInlineEdit(i);
    });
    row.addEventListener("click", () => selectRow(i));

    row.appendChild(indentSpan);
    row.appendChild(cell);
    row.appendChild(descSpan);

    treePreviewEl.appendChild(row);
  });

  const sel = prevSel === -1 ? 0 : prevSel;
  if (blocks.length) selectRow(Math.min(sel, blocks.length - 1));
  updateStatus(sel);
}

    // -------------------------------------------------------------------
// PCR violation detector (AI correction support)
/// -------------------------------------------------------------------
function detectPCRViolations(text) {
  const issues = [];

  if (/\bTHEN\b/i.test(text)) {
    issues.push("Remove THEN keyword (PCR does not support THEN)");
  }

  if (/(AMT|RTE)\(\d+\)/i.test(text)) {
    issues.push("Indexed AMT()/RTE() is illegal in PCR");
  }

  if (/[+\-*/]/.test(text)) {
    issues.push("Inline arithmetic forbidden; use MULTI / DIVI");
  }

  return issues;
}

   function buildCorrectionHint(issues) {
  if (!issues.length) return "";

  return (
`CORRECTION REQUIRED (STRICT SAP PCR RULES):

${issues.map(i => `- ${i}`).join("\n")}

IMPORTANT:
- NUM may ONLY reference the CURRENT wage type
- Cross-wage-type NUM access is NOT allowed
- Do NOT use NUM(xxxx) in IF conditions
- Rewrite logic using WT selection + MULTI / DIVI only
- If requirement is impossible in PCR, rewrite it into a valid equivalent

Return PCR code only.`
  );
}

    // ----------------------------
    // Validation
    // ----------------------------
    function validateAll() {
      const diags = [];
      const ifStack = [];

      blocks.forEach((b, idx) => {
        const ln = idx + 1;
        if (idx <= 2) return; // skip headers
        const info = parseLineForDesc(b.text);
        if (!info) return;

        if (info.type === "unknown") {
          diags.push({ line: ln, severity: "E", message: `Unknown operation '${info.op}'` });
          return;
        }

        if (info.type === "wt") {
          if (!/^\d{4}$/.test(info.wageType)) {
            diags.push({ line: ln, severity: "E", message: "Wage type must be 4 digits" });
          }
          return;
        }

        if (info.type === "op") {
          const op = info.op;
          const operand = info.operand;
          const amtOps = ["AMT=", "AMT+", "AMT-", "AMT*", "AMT/","NUM=","NUM+","NUM-","NUM*","NUM/","RTE="];

          if (amtOps.includes(op)) {
            if (!operand) {
              diags.push({ line: ln, severity: "E", message: `${op} requires operand` });
            } else if (!/^-?\d+(\.\d+)?$/.test(operand) && !/^[A-Z]+\(.+\)$/i.test(operand)) {
              // allow numeric or function-like NUM(2001)
              diags.push({ line: ln, severity: "E", message: `Operand must be numeric or valid expression` });
            }
          }

          if (op === "IF") ifStack.push(ln);
          if (op === "ENDIF") {
            if (!ifStack.length) diags.push({ line: ln, severity: "E", message: "ENDIF without matching IF" });
            else ifStack.pop();
          }
          if (op === "ELSE" && !ifStack.length) diags.push({ line: ln, severity: "E", message: "ELSE without matching IF" });
        }
      });

      if (ifStack.length) diags.push({ line: ifStack[0], severity: "E", message: "IF not closed by ENDIF" });

      return diags;
    }

    function applyLocalHighlights(diags) {
      if (!treePreviewEl) return;
      treePreviewEl.querySelectorAll(".pcr-row").forEach(r => r.classList.remove("pcr-warn", "pcr-danger"));

      if (!diags || !diags.length) {
        if (hintsEl) hintsEl.innerHTML = "";
        return;
      }

      diags.forEach(d => {
        const row = treePreviewEl.querySelector(`.pcr-row[data-index="${d.line - 1}"]`);
        if (!row) return;
        row.classList.add(d.severity === "E" ? "pcr-danger" : "pcr-warn");
      });

      if (hintsEl) {
        hintsEl.innerHTML = diags.map(d => {
          const icon = d.severity === "E" ? "❌" : "⚠️";
          return `• ${icon} Line ${d.line}: ${escapeHtml(d.message)}`;
        }).join("<br>");
      }
    }

    /// -------------------------------------------------------------------
// AI regeneration with correction hints
/// -------------------------------------------------------------------
async function regeneratePCRWithHints(originalPrompt, hint) {
  const res = await fetch(`${API}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: originalPrompt,
      hint
    })
  });

  const data = await res.json();
  if (!data?.ok || !data.pcr) {
    throw new Error("AI regeneration failed");
  }

  return data.pcr;
}

    // ----------------------------
    // Backend run (defensive)
    // ----------------------------
    async function runEngineCheck() {
      const text = blocks.map(b => b.text).join("\n");
      if (!text.trim()) {
        if (hintsEl) hintsEl.innerHTML = "Nothing to check yet.";
        if (runtimeEl) runtimeEl.textContent = "";
        return;
      }
      if (apiNotConfigured()) {
        if (hintsEl) hintsEl.innerHTML = "Backend unavailable. Set BACKEND_URL.";
        return;
      }

      try {
        const res = await fetch(`${API}/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text })
        });
        const raw = await res.text();
        if (!raw || !raw.trim()) throw new Error("Empty response from engine");
        let data;
        try { data = JSON.parse(raw); } catch (err) { throw new Error("Invalid JSON from engine: " + raw.slice(0, 300)); }
        if (!data || !data.ok) throw new Error(data?.error || "Engine returned an error");

        // apply parsed highlights (if any)
        applyParsedHighlights(data.parsed || { lines: [] });
        renderStructureModel(data.model || null);
        renderRuntime(data.runtime || null);
      } catch (err) {
        console.error("runEngineCheck:", err);
        if (hintsEl) hintsEl.innerHTML = "Engine error: " + (err.message || err.toString());
        if (runtimeEl) runtimeEl.textContent = "";
      }
    }

    function applyParsedHighlights(parsed) {
      if (!treePreviewEl) return;
      treePreviewEl.querySelectorAll(".pcr-row").forEach(r => r.classList.remove("pcr-danger", "pcr-warn"));
      if (!parsed || !Array.isArray(parsed.lines)) {
        if (hintsEl) hintsEl.innerHTML = "No parsed data returned from engine.";
        return;
      }
      const issues = [];
      const ifStack = [];
      parsed.lines.forEach(line => {
        const ln = (line.index || 0) + 1;
        const op = (line.opcode || "").toUpperCase();
        if (op === "IF") ifStack.push(ln);
        if (op === "ENDIF") {
          if (!ifStack.length) issues.push({ line: ln, message: "ENDIF without matching IF" });
          else ifStack.pop();
        }
      });
      if (ifStack.length) issues.push({ line: ifStack[0], message: "IF not closed by ENDIF" });

      if (!issues.length) {
        if (hintsEl) hintsEl.innerHTML = "✔ No blocking or warning issues found.";
        return;
      }

      if (hintsEl) hintsEl.innerHTML = issues.map(it => `• ❌ Line ${it.line}: ${escapeHtml(it.message)}`).join("<br>");
      issues.forEach(it => {
        const row = treePreviewEl.querySelector(`.pcr-row[data-index="${it.line - 1}"]`);
        if (row && row.classList) row.classList.add("pcr-danger");
      });
    }

    function renderStructureModel(model) {
      if (!structureEl) return;
      if (!model) {
        structureEl.textContent = "No structure information.";
        return;
      }
      let out = `Rule: ${model.title || ""}\nWage Types:\n`;
      (model.wageTypes || []).forEach(wt => {
        out += `  /${wt.code}\n`;
        (wt.items || []).forEach(it => {
          if (it.type === "op") out += `    ${it.opcode} ${it.arg || ""}\n`;
          else if (it.type === "if") out += `    IF ${it.condition}\n`;
          else if (it.type === "out") out += `    OUTWP ${it.returnCode}\n`;
        });
      });
      structureEl.textContent = out;
    }

    function renderRuntime(runtime) {
      if (!runtimeEl) return;
      if (!runtime || typeof runtime !== "object") {
        runtimeEl.textContent = "No runtime information.";
        return;
      }
      const {
        amt = 0, num = 0, rte = 0,
        currentWageType = "-", callingWageType = "-", returnCode = "00",
        transfers = [], log = []
      } = runtime;

      const header = `AMT=${amt}  NUM=${num}  RTE=${rte}\nCurrent WT=${currentWageType}  Calling WT=${callingWageType}\nReturn code=${returnCode}\n`;
      const transfersText = transfers.length
        ? transfers.map(t => `  • WT ${t.wageType}: AMT=${t.amt} NUM=${t.num} RTE=${t.rte} (from ${t.fromLine})`).join("\n")
        : "  No transfers.";
      const logText = log.length ? log.map(l => `  • ${l}`).join("\n") : "  (no log entries).";
      runtimeEl.textContent = header + "\n--- Transfers ---\n" + transfersText + "\n\n--- Log ---\n" + logText;
    }

    // ----------------------------
    // Load opcode meta (optional)
    // ----------------------------
    async function loadOpcodeMeta() {
      if (OPCODE_META) return OPCODE_META;
      if (apiNotConfigured()) { OPCODE_META = []; return OPCODE_META; }
      try {
        const res = await fetch(`${API}/ops`);
        const text = await res.text();
        if (!text) { OPCODE_META = []; return OPCODE_META; }
        const data = JSON.parse(text);
        if (data && data.ok && Array.isArray(data.ops)) OPCODE_META = data.ops;
        else OPCODE_META = [];
      } catch (err) {
        console.warn("loadOpcodeMeta failed:", err);
        OPCODE_META = [];
      }
      return OPCODE_META;
    }

    async function showCatFromOps(groupName, fallbackTitle) {
      const ops = await loadOpcodeMeta();
      const title = fallbackTitle || groupName;
      if (!ops.length) {
        if (opLibTitle) opLibTitle.textContent = title;
        if (opLibBody) opLibBody.textContent = "Operation metadata not available from backend (/ops).";
        if (opLibModal && opLibModal.classList) opLibModal.classList.remove("hidden");
        return;
      }
      const filtered = ops.filter(o => (o.group || "").toLowerCase() === groupName.toLowerCase());
      const bodyLines = (filtered.length ? filtered : ops).map(o => `${(o.code || "").padEnd(8, " ")}  ${o.description || ""}`);
      if (opLibTitle) opLibTitle.textContent = title;
      if (opLibBody) opLibBody.textContent = bodyLines.join("\n");
      if (opLibModal && opLibModal.classList) opLibModal.classList.remove("hidden");
    }

    // ----------------------------
    // Analysis orchestrator
    // ----------------------------
    function analyze(runBackend = false) {
      if (!blocks.length) {
        if (aiWelcome) aiWelcome.style.display = "block";
        //if (overviewEl) overviewEl.innerHTML = "Start by creating a rule and wage type.";
        //if (structureEl) structureEl.textContent = "";
        if (runtimeEl) runtimeEl.textContent = "";
        if (hintsEl) hintsEl.innerHTML = "";
        return;
      }

      if (aiWelcome) aiWelcome.style.display = "none";

      if (structureEl) {
        structureEl.textContent = blocks.filter(b => b.text.trim()).map(b => {
          const mark = b.indent === 0 ? "•" : "│ ".repeat(Math.max(0, b.indent - 1)) + "└─";
          return `${mark} ${b.text.trim()}`;
        }).join("\n");
      }

      const diags = validateAll();
      applyLocalHighlights(diags);

      if (runBackend) runEngineCheck();
    }

    // ----------------------------
    // Toolbar actions & wiring
    // ----------------------------
    if (btnCheck) btnCheck.onclick = () => { stopInlineEdit(); renderTable(); analyze(true); };

    if (btnInsertExample) btnInsertExample.onclick = () => {
      const i = getSelectedIndex();
      const insertAt = i < 0 ? blocks.length : i + 1;
      const sample = [
        { text: "* Example", indent: 0 },
        { text: "/2000 Sample WT", indent: 1 },
        { text: "AMT= 1000", indent: 2 },
        { text: "ADDWT *", indent: 2 }
      ];
      blocks.splice(insertAt, 0, ...sample);
      syncEditor();
      renderTable();
      selectRow(insertAt);
      analyze(false);
    };

   if (btnCreate) btnCreate.onclick = () => {
  if (!isChangeMode) return;
  const i = getSelectedIndex();
  if (i < 0) return;

  // FIX: clear leftover AI text so it doesn’t auto-insert again
  if (insertPopup && insertPopup.dataset) {
    delete insertPopup.dataset.pendingAIPCR;
  }

  pendingInsertIndex = i;
  if (insertPopup && insertPopup.classList)
    insertPopup.classList.remove("hidden");
};

    if (insertCancelBtn) insertCancelBtn.onclick = () => {
  if (insertPopup) {
    insertPopup.classList.add("hidden");
    delete insertPopup.dataset.pendingAIPCR;   // <-- FIX
  }
  pendingInsertIndex = null;
};
    if (insertSameBtn) insertSameBtn.onclick = () => {
      if (pendingInsertIndex == null) return;
      const ref = blocks[pendingInsertIndex];
      const newBlock = { text: "", indent: ref.indent };
      blocks.splice(pendingInsertIndex + 1, 0, newBlock);
      syncEditor(); renderTable(); selectRow(pendingInsertIndex + 1); startInlineEdit(pendingInsertIndex + 1);
      if (insertPopup) insertPopup.classList.add("hidden");
      pendingInsertIndex = null;
    };
    if (insertSubBtn) insertSubBtn.onclick = () => {
      if (pendingInsertIndex == null) return;
      const ref = blocks[pendingInsertIndex];
      const newBlock = { text: "", indent: (ref.indent || 0) + 1 };
      blocks.splice(pendingInsertIndex + 1, 0, newBlock);
      syncEditor(); renderTable(); selectRow(pendingInsertIndex + 1); startInlineEdit(pendingInsertIndex + 1);
      if (insertPopup) insertPopup.classList.add("hidden");
      pendingInsertIndex = null;
    };

    if (btnDelete) btnDelete.onclick = () => {
      if (!isChangeMode) return;
      const i = getSelectedIndex(); if (i < 0) return;
      if (isProtectedRoot(i)) { alert("Root PCR nodes cannot be deleted."); return; }
      blocks.splice(i, 1); syncEditor(); renderTable(); analyze(false);
    };

    if (btnCut) btnCut.onclick = () => {
      if (!isChangeMode) return;
      const i = getSelectedIndex(); if (i < 0) return;
      if (isProtectedRoot(i)) { alert("Root PCR nodes cannot be cut."); return; }
      clipboardBlocks = [{ ...blocks[i] }]; blocks.splice(i, 1); syncEditor(); renderTable(); analyze(false);
    };

    if (btnCopyBuffer) btnCopyBuffer.onclick = () => {
      const i = getSelectedIndex(); if (i < 0) return;
      clipboardBlocks = [{ ...blocks[i] }];
    };

    if (btnPaste) btnPaste.onclick = () => {
      if (!isChangeMode) return;
      if (!clipboardBlocks) return;
      const i = getSelectedIndex(); const at = i < 0 ? blocks.length : i + 1;
      blocks.splice(at, 0, ...clipboardBlocks.map(b => ({ ...b })));
      syncEditor(); renderTable(); selectRow(at); analyze(false);
    };

    if (btnAttributes) btnAttributes.onclick = () => {
      if (!attrModal) return;
      // ORIGINAL behavior: do not pre-fill with examples; show current header values if present
      if (attrCreated) attrCreated.textContent = formatDate(createdOn);
      if (attrChanged) attrChanged.textContent = formatDate(lastChanged);
      if (attrRule) attrRule.value = ruleIdInput ? ruleIdInput.value.trim() : "";
      if (attrRuleText) attrRuleText.value = ruleTextInput ? ruleTextInput.value.trim() : "";
      attrModal.classList.remove("hidden");
    };
    if (attrClose) attrClose.onclick = () => { if (attrModal) attrModal.classList.add("hidden"); };

    if (btnDoc) btnDoc.onclick = () => { if (!docModal) return; docText.value = docText.value || ""; docModal.classList.remove("hidden"); };
    if (docClose) docClose.onclick = () => { if (!docModal) return; docModal.classList.add("hidden"); };

    if (opLibClose) opLibClose.onclick = () => { if (opLibModal) opLibModal.classList.add("hidden"); };

// THEME HANDLER — corrected (no double declaration)
if (themeSelect) {
    themeSelect.addEventListener("change", () => {
        // Remove old theme classes
        document.body.classList.remove("theme-classic", "theme-modern", "theme-dark");

        const val = themeSelect.value;

        if (val === "classic") {
            document.body.classList.add("theme-classic");
        } 
        else if (val === "modern") {
            document.body.classList.add("theme-modern");
        }
        else if (val === "sap-dark") {     // IMPORTANT: match value in index.html
            document.body.classList.add("theme-dark");
        }
    });
}

    if (btnTreeView) btnTreeView.onclick = () => {
      if (treePreviewEl) treePreviewEl.classList.add("active");
      if (editor && editor.parentElement) editor.parentElement.classList.remove("active");
      if (btnTreeView) btnTreeView.classList.add("active");
      if (btnEditorView) btnEditorView.classList.remove("active");
      refreshPanels();
    };
    if (btnEditorView) btnEditorView.onclick = () => {
      if (editor && editor.parentElement) editor.parentElement.classList.add("active");
      if (treePreviewEl) treePreviewEl.classList.remove("active");
      if (btnEditorView) btnEditorView.classList.add("active");
      if (btnTreeView) btnTreeView.classList.remove("active");
    };

    //if (editor) editor.addEventListener("input", syncBlocksFromEditor);

    // global click to hide suggest box
    document.addEventListener("mousedown", (e) => {
      if (suggestBox && suggestBox.contains && suggestBox.contains(e.target)) return;
      if (inlineCell && inlineCell.contains && inlineCell.contains(e.target)) return;
      if (suggestBox && suggestBox.classList) suggestBox.classList.add("hidden");
    });

    // Enter on wage type opens workspace (original behavior restored)
    if (ruleWTInput) {
      ruleWTInput.addEventListener("keydown", (e) => {
        if (e.key !== "Enter") return;
        e.preventDefault();
        const ok = (ruleIdInput && ruleIdInput.value && ruleIdInput.value.trim())
                && (ruleTextInput && ruleTextInput.value && ruleTextInput.value.trim())
                && (ruleESGrpInput && ruleESGrpInput.value && ruleESGrpInput.value.trim())
                && (ruleWTInput && ruleWTInput.value && ruleWTInput.value.trim());
        if (!ok) {
          if (headerHint) headerHint.innerHTML = "Please fill all fields – missing ones are highlighted.";
          return;
        }
        if (headerScreen) headerScreen.classList.add("hidden");
        if (workspaceArea) workspaceArea.classList.remove("hidden");

        const rid = ruleIdInput.value.trim();
        const rtx = ruleTextInput.value.trim();
        const esg = ruleESGrpInput.value.trim();
        const wt = ruleWTInput.value.trim();

        const hdrMiniRule = $("hdr-mini-rule");
        const hdrMiniESGrp = $("hdr-mini-esgrp");
        const hdrMiniWT = $("hdr-mini-wt");
        if (hdrMiniRule) hdrMiniRule.textContent = `Rule: ${rid}`;
        if (hdrMiniESGrp) hdrMiniESGrp.textContent = `ESGrp: ${esg}`;
        if (hdrMiniWT) hdrMiniWT.textContent = `WT: ${wt}`;

        blocks = [
          { text: `${rid} ${rtx}`, indent: 0 },
          { text: `*`, indent: 1 },
          { text: `/${wt} ${rtx}`, indent: 2 }
        ];

        syncEditor();
        renderTable();
        selectRow(2);

        if (attrRule) attrRule.value = rid;
        if (attrRuleText) attrRuleText.value = rtx;
        if (attrCreated) attrCreated.textContent = formatDate(createdOn);
        if (attrChanged) attrChanged.textContent = formatDate(createdOn);

        analyze(false);
      });
    }

    // initial render
    renderTable();
    analyze(false);
    if (statusMode) statusMode.textContent = "Change";

    // default enable/disable toolbar safely
    [btnCreate, btnDelete, btnCut, btnCopyBuffer, btnPaste, btnReassign].forEach(b => { if (b) b.disabled = false; });

    // ----------------------------
    // AI generator integration (non-destructive)
    // ----------------------------

    function replaceWorkspaceWithPCR(pcrText) {
  if (!pcrText || !pcrText.trim()) return false;

  // Preserve header (rule line, *, /WT)
  if (blocks.length < 3) return false;

  const header = blocks.slice(0, 3); // keep:
  // 0: rule title
  // 1: *
  // 2: /WT xxxx

  // Normalize & split PCR
  const normalized = normalizeAIPCR(pcrText);
  const lines = normalized.split("\n").map(l => l.trim()).filter(Boolean);

  // Rebuild PCR body under /WT
  const body = applyPCRIndentation(lines, header[2].indent + 1);

  blocks = [...header, ...body];

  syncEditor();
  renderTable();
  selectRow(3);
  analyze(false);

  return true;
}
    
   function normalizeAIPCR(raw) {
  if (!raw) return "";

  let out = String(raw).replace(/\r/g, "");

  // Strip fenced blocks ONLY
  const fenced = out.match(/```(?:pcr|txt)?\n?([\s\S]*?)```/i);
  if (fenced && fenced[1]) out = fenced[1];

  // Trim empty edges ONLY — no rewriting
  let lines = out
    .split("\n")
    .map(l => l.replace(/\t/g, " ").trimEnd());

  while (lines.length && lines[0].trim() === "") lines.shift();
  while (lines.length && lines[lines.length - 1].trim() === "") lines.pop();

  return lines.join("\n");
}

    /// -------------------------------------------------------------------
// PE02-style hard rejection of illegal PCR syntax
/// -------------------------------------------------------------------
function validateAndFixPCR(text) {
  // 🔒 AI PCR is already validated by backend
  // Frontend must NEVER rewrite PCR
  return text;
}

  function rewritePCRMath(lines) {
  const out = [];

  for (let raw of lines) {
    const line = raw.trim();

    // 1. Remove illegal THEN keyword
    if (/^IF\s+.*\bTHEN\b/i.test(line)) {
      out.push(line.replace(/\bTHEN\b/i, "").trim());
      continue;
    }

    // 2. Fix illegal RTE(2001) / AMT(2001)
    let m = line.match(/^(AMT|RTE|NUM)\s*\(\s*\d+\s*\)\s*=\s*(.+)$/i);
    if (m) {
      out.push(`${m[1].toUpperCase()}= ${m[2]}`);
      continue;
    }

    // 3. Rewrite AMT = X * Y / Z
    m = line.match(/^AMT=\s*(NUM|AMT|RTE)\s*\*\s*(NUM|AMT|RTE)\s*\/\s*(\d+)$/i);
    if (m) {
      out.push(`RTE= ${m[1]}`);
      out.push(`MULTI ${m[2]}`);
      out.push(`DIVI ${m[3]}`);
      out.push(`AMT= RTE`);
      continue;
    }

    // 4. Rewrite AMT = X * Y
    m = line.match(/^AMT=\s*(NUM|AMT|RTE)\s*\*\s*(NUM|AMT|RTE)$/i);
    if (m) {
      out.push(`RTE= ${m[1]}`);
      out.push(`MULTI ${m[2]}`);
      out.push(`AMT= RTE`);
      continue;
    }

    // 5. Rewrite AMT = X / N
    m = line.match(/^AMT=\s*(NUM|AMT|RTE)\s*\/\s*(\d+)$/i);
    if (m) {
      out.push(`RTE= ${m[1]}`);
      out.push(`DIVI ${m[2]}`);
      out.push(`AMT= RTE`);
      continue;
    }

    // 6. Pass-through legal lines
    out.push(line);
  }

  return out;
}
    function applyPCRIndentation(lines, baseIndent) {
  let indent = baseIndent;
  const out = [];

  lines.forEach(raw => {
    const line = raw.trim();

    // ENDIF reduces indent BEFORE placing
    if (/^ENDIF\b/i.test(line)) {
      indent = Math.max(baseIndent, indent - 1);
    }

    out.push({
      text: raw,
      indent
    });

    // IF / ELSE increase indent AFTER placing
    if (/^(IF|ELSEIF|ELSE)\b/i.test(line)) {
      indent++;
    }
  });

  return out;
}

 async function insertAIPCRAtSelection(pcrText, preferSublevel = false) {
  if (!pcrText || !pcrText.trim()) return false;

  // ---------------------------------------
  // STEP 1: Normalize initial AI output
  // ---------------------------------------
  let candidate = normalizeAIPCR(pcrText);
   // 🔒 Backend PCR is already verified — DO NOT TOUCH
// 🔒 Backend PCR is authoritative — skip all frontend correction
if (pcrText && /ADDWT\s+\d{4}/i.test(pcrText)) {
  candidate = pcrText.trim();
  // jump directly to insertion
  const sel = getSelectedIndex();
  if (sel >= 0) {
    const ref = blocks[sel];
    const indent = ref.indent || 0;
    const newBlocks = applyPCRIndentation(candidate.split("\n"), indent);
    blocks.splice(sel + 1, 0, ...newBlocks);
    syncEditor();
    renderTable();
    selectRow(sel + 1);
    analyze(false);
    return true;
  }
}

  // Fallback: insert into editor cursor
  if (editor) {
    const pos = editor.selectionStart ?? editor.value.length;
    const before = editor.value.slice(0, pos);
    const after  = editor.value.slice(pos);

    const insert =
      (before.endsWith("\n") || before.length === 0 ? "" : "\n") +
      candidate +
      (after.startsWith("\n") || after.length === 0 ? "" : "\n");

    editor.value = before + insert + after;
    editor.dispatchEvent(new Event("input", { bubbles: true }));

    blocks = [];
    renderTable();
    analyze(false);
    return true;
  }

  return false;
}

    // AI generate + wiring (uses API /generate if configured)
    if (aiGenerateBtn) {
      aiGenerateBtn.addEventListener("click", async () => {
        if (!aiPromptEl || !aiStatusEl) return;
        const prompt = (aiPromptEl.value || "").trim();
        if (!prompt) { aiStatusEl.textContent = "Please describe your payroll scenario first."; return; }
        if (apiNotConfigured()) { aiStatusEl.textContent = "Backend not configured. Set BACKEND_URL."; return; }

        aiGenerateBtn.disabled = true;
        aiCopyBtn.disabled = true;
        aiPreviewEl.value = "";
        aiStatusEl.textContent = "Generating PCR…";

        try {
          const res = await fetch(`${API}/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
          });
          const raw = await res.text();
          if (!raw || !raw.trim()) throw new Error("Empty response from /generate");
          let data;
          try { data = JSON.parse(raw); } catch (e) { throw new Error("Invalid JSON from /generate: " + raw.slice(0, 200)); }
          if (!data || !data.ok) { const msg = data?.error || "AI generation failed"; aiStatusEl.textContent = `AI error: ${msg}`; return; }
          const pcr = (data.pcr || "").trim();
          if (!pcr) { aiStatusEl.textContent = "AI responded but no PCR text detected."; aiPreviewEl.value = data.raw || ""; return; }
          aiPreviewEl.value = normalizeAIPCR(pcr);
          aiCopyBtn.disabled = false;
          aiStatusEl.textContent = "PCR generated. Review and click 'Copy to workspace'.";
        } catch (err) {
          console.error("/generate error", err);
          if (aiStatusEl) aiStatusEl.textContent = "Network error calling /generate. Check backend.";
        } finally {
          aiGenerateBtn.disabled = false;
        }
      });
    }

    if (aiCopyBtn) {
      aiCopyBtn.addEventListener("click", () => {
        const text = (
  aiPreviewEl
    ? (aiPreviewEl.value ?? aiPreviewEl.textContent)
    : ""
).trim();
        if (!text) {
          if (aiStatusEl) aiStatusEl.textContent = "Nothing to copy. Generate first.";
          return;
        }

        // If insert popup exists, ask user choice; otherwise default to same-level
        if (insertPopup && insertSameBtn && insertSubBtn) {
          // show popup and remember candidate content
          pendingInsertIndex = getSelectedIndex();
          // pre-store into a data attribute to retrieve on click
          insertPopup.dataset.pendingAIPCR = text;
          insertPopup.classList.remove("hidden");
          if (aiStatusEl) aiStatusEl.textContent = "Choose insertion type: Same level or Sub-level.";
          return;
        }

        // no popup — insert at selection (same-level)
        const ok = insertAIPCRAtSelection(text, false);
        if (aiStatusEl) aiStatusEl.textContent = ok ? "PCR copied into workspace." : "Could not insert PCR.";
      });
    }

    if (aiClearBtn) aiClearBtn.addEventListener("click", () => {
      if (aiPromptEl) aiPromptEl.value = "";
      if (aiPreviewEl) aiPreviewEl.value = "";
      if (aiStatusEl) aiStatusEl.textContent = "";
      if (aiCopyBtn) aiCopyBtn.disabled = true;
    });

    // Hook for insertPopup buttons to handle AI pasted content if shown
  insertSameBtn.onclick = () => {
  if (pendingInsertIndex == null) return;

  // 🔥 AI case
  if (insertPopup.dataset.pendingAIPCR) {
    insertAIPCRAtSelection(insertPopup.dataset.pendingAIPCR, false);
    delete insertPopup.dataset.pendingAIPCR;
  } 
  // 🧱 Normal create case
  else {
    const ref = blocks[pendingInsertIndex];
    blocks.splice(pendingInsertIndex + 1, 0, { text: "", indent: ref.indent });
    syncEditor();
    renderTable();
    selectRow(pendingInsertIndex + 1);
    startInlineEdit(pendingInsertIndex + 1);
  }

  insertPopup.classList.add("hidden");
  pendingInsertIndex = null;
};

    insertSubBtn.onclick = () => {
  if (pendingInsertIndex == null) return;

  if (insertPopup.dataset.pendingAIPCR) {
    insertAIPCRAtSelection(insertPopup.dataset.pendingAIPCR, true);
    delete insertPopup.dataset.pendingAIPCR;
  } 
  else {
    const ref = blocks[pendingInsertIndex];
    blocks.splice(pendingInsertIndex + 1, 0, { text: "", indent: (ref.indent || 0) + 1 });
    syncEditor();
    renderTable();
    selectRow(pendingInsertIndex + 1);
    startInlineEdit(pendingInsertIndex + 1);
  }

  insertPopup.classList.add("hidden");
  pendingInsertIndex = null;
};

    // ----------------------------
    // More helpers, autosave, restore
    // ----------------------------


    function dedupeBlocks() {
      const seen = new Set();
      const out = [];
      blocks.forEach((b) => {
        const key = (b.text || "") + "::" + (b.indent || 0);
        if (!seen.has(key)) { out.push(b); seen.add(key); }
      });
      blocks = out;
    }

    function validateTitleFormat() {
      if (!blocks.length) return;
      const line1 = (blocks[0].text || "").trim();
      const ruleId = ruleIdInput ? ruleIdInput.value.trim() : "";
      if (!line1.startsWith(ruleId) && ruleId) {
        blocks[0].text = `${ruleId} ` + line1.replace(/^\S+/, "");
        syncEditor();
      }
    }

    // minor helpers
    function updateMinimap() {
      if (!minimap || !editor) return;
      minimap.textContent = editor.value.slice(0, 2000);
    }

    if (editor) editor.addEventListener("input", updateMinimap);

    function syncScroll() {
      if (!editor || !treePreviewEl) return;
      const ratio = editor.scrollTop / (editor.scrollHeight - editor.clientHeight || 1);
      treePreviewEl.scrollTop = ratio * (treePreviewEl.scrollHeight - treePreviewEl.clientHeight || 1);
    }
    if (editor) editor.addEventListener("scroll", syncScroll);

    // ----------------------------
    // Structure compute (original)
    // ----------------------------
    function computeStructure() {
      const result = [];
      const stack = [];
      blocks.forEach((b, i) => {
        const txt = (b.text || "").trim();
        if (!txt) return;
        const info = parseLineForDesc(txt);
        if (!info) return;
        if (info.type === "wt") { result.push({ line: i + 1, type: "wt", code: info.wageType }); stack.length = 0; }
        else if (info.type === "op") {
          const op = info.op;
          if (op === "IF") { result.push({ line: i + 1, type: "if", cond: info.operand }); stack.push(i + 1); }
          else if (op === "ELSE") result.push({ line: i + 1, type: "else" });
          else if (op === "ENDIF") { result.push({ line: i + 1, type: "endif" }); if (stack.length) stack.pop(); }
          else result.push({ line: i + 1, type: "op", op, operand: info.operand });
        }
      });
      return result;
    }

    // ----------------------------
    // Move rows up/down
    // ----------------------------
    if (btnMoveUp) {
      btnMoveUp.onclick = () => {
        if (!isChangeMode) return;
        const i = getSelectedIndex();
        if (i <= 2) return;
        if (i < 3 || i >= blocks.length) return;
        const tmp = blocks[i - 1];
        blocks[i - 1] = blocks[i];
        blocks[i] = tmp;
        syncEditor(); renderTable(); selectRow(i - 1); analyze(false);
      };
    }
    if (btnMoveDown) {
      btnMoveDown.onclick = () => {
        if (!isChangeMode) return;
        const i = getSelectedIndex();
        if (i < 2 || i >= blocks.length - 1) return;
        const tmp = blocks[i + 1];
        blocks[i + 1] = blocks[i];
        blocks[i] = tmp;
        syncEditor(); renderTable(); selectRow(i + 1); analyze(false);
      };
    }

    // ----------------------------
    // Reassign modal handling
    // ----------------------------
    if (btnReassign) {
      btnReassign.onclick = () => {
        const found = [];
        blocks.forEach(b => { const t = (b.text || "").trim(); const m = t.match(/^\/(\d{4})/); if (m) found.push(m[1]); });
        const unique = [...new Set(found)];
        if (!unique.length) { alert("No wage types found in this PCR."); return; }
        if (reassignFrom) reassignFrom.innerHTML = unique.map(x => `<option value="${x}">${x}</option>`).join("");
        if (reassignModal && reassignModal.classList) reassignModal.classList.remove("hidden");
      };
    }
    if (reassignClose) reassignClose.onclick = () => { if (reassignModal) reassignModal.classList.add("hidden"); };
    if (reassignOk) {
      reassignOk.onclick = () => {
        const from = reassignFrom ? reassignFrom.value.trim() : "";
        const to = reassignTo ? reassignTo.value.trim() : "";
        if (!/^\d{4}$/.test(to)) { alert("Target WT must be 4 digits."); return; }
        blocks.forEach(b => {
          const t = (b.text || "").trim();
          if (t.startsWith("/" + from)) { b.text = t.replace("/" + from, "/" + to); }
        });
        syncEditor(); renderTable(); analyze(false);
        if (reassignModal) reassignModal.classList.add("hidden");
      };
    }

    // ----------------------------
    // Export / Import
    // ----------------------------
    if (btnExport) {
      btnExport.onclick = async () => {
        const data = { header: { ruleId: ruleIdInput ? ruleIdInput.value.trim() : "", ruleText: ruleTextInput ? ruleTextInput.value.trim() : "", esg: ruleESGrpInput ? ruleESGrpInput.value.trim() : "", wt: ruleWTInput ? ruleWTInput.value.trim() : "" }, blocks };
        try {
          await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
          alert("PCR copied to clipboard.");
        } catch {
          alert("Clipboard copy failed.");
        }
      };
    }

    if (btnImport) {
      btnImport.onclick = () => {
        const pasted = prompt("Paste PCR text:");
        if (!pasted) return;
        const lines = pasted.replace(/\r/g, "").split("\n");
        if (lines.length < 3) { alert("Invalid PCR."); return; }
        blocks = lines.map(t => ({ text: t.trimEnd(), indent: 0 }));
         renderTable(); analyze(false);
      };
    }

   

    // ----------------------------
    // Final initialization
    // ----------------------------
    (function initializeWorkspace() {
      try {
        if (editor) editor.value = "";
        syncBlocksFromEditor();
        renderTable();
        analyze(false);
        if (statusMode) statusMode.textContent = "Change";
        console.log("PCR Workspace initialized.");
      } catch (e) {
        console.error("Initialization failed:", e);
      }
    })();

    // Export API for debugging
    window.PCR = {
      blocks,
      renderTable,
      analyze,
      runEngineCheck,
      computeStructure,
      insertAIPCRAtSelection
    };

    // Smooth scroll helper
    function scrollRowIntoView(i) {
      if (!treePreviewEl) return;
      const row = treePreviewEl.querySelector(`.pcr-row[data-index="${i}"]`);
      if (!row) return;
      const rect = row.getBoundingClientRect();
      const parentRect = treePreviewEl.getBoundingClientRect();
      if (rect.top < parentRect.top || rect.bottom > parentRect.bottom) {
        row.scrollIntoView({ block: "center", behavior: "smooth" });
      }
    }

  }); // DOMContentLoaded end

})(); // IIFE end