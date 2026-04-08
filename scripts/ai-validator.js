// scripts/ai-validator.js
// SAP PCR Frontend Validator — enforces PE02 syntax rules in the browser
(function () {
  "use strict";

  // ── Valid opcodes known by the frontend ──────────────────────────────
  const VALID_OPCODES = new Set([
    "AMT=", "AMT+", "AMT-", "AMT*", "AMT/",
    "AMT?>", "AMT?<", "AMT?=",
    "NUM=", "NUM+", "NUM-", "NUM*", "NUM/",
    "NUM?>", "NUM?<", "NUM?=",
    "RTE=", "RTE*", "RTE/",
    "RTE?>", "RTE?<", "RTE?=",
    "MULTI", "DIVI",
    "ADDWT", "SUBWT",
    "OUTWP", "OUTWPP",
    "ZERO=", "SUPPRESS",
    "PRINT", "TABLE",
  ]);

  // ── Opcodes that require a space + operand ───────────────────────────
  const NEEDS_OPERAND = new Set([
    "AMT=", "AMT+", "AMT-", "AMT*", "AMT/",
    "NUM=", "NUM+", "NUM-", "NUM*", "NUM/",
    "RTE=", "RTE*", "RTE/",
    "AMT?>", "AMT?<", "AMT?=",
    "NUM?>", "NUM?<", "NUM?=",
    "RTE?>", "RTE?<", "RTE?=",
    "MULTI", "DIVI",
    "ADDWT", "SUBWT",
  ]);

  // ── Opcodes that take NO operand ─────────────────────────────────────
  const NO_OPERAND = new Set(["OUTWP", "OUTWPP", "ZERO=", "SUPPRESS"]);

  // ── Structural line patterns ─────────────────────────────────────────
  function isStructuralLine(line) {
    if (!line || !line.trim()) return true;
    if (/^\*\s*$/.test(line.trim())) return true;   // separator
    if (/^\/\d{4}/.test(line.trim())) return true;   // /NNNN wage type node
    if (/^[A-Z0-9]{4}\s+\S/.test(line.trim())) return true; // ZXXX rule header
    return false;
  }

  // ── Normalize input ──────────────────────────────────────────────────
  function normalize(text) {
    return text
      .replace(/\r/g, "")
      .split("\n")
      .map((l) => l.trimEnd());
  }

  // ── Main validate function ───────────────────────────────────────────
  function validate(lines) {
    const issues = [];
    let hasInit = false;

    lines.forEach((rawLine, i) => {
      const line = rawLine.trim();
      const lineno = i + 1;

      if (!line) return;
      if (isStructuralLine(line)) {
        // Reset init tracker at wage type node
        if (/^\/\d{4}/.test(line)) hasInit = false;
        return;
      }

      // ── 1. THEN keyword ─────────────────────────────────────────────
      if (/\bTHEN\b/i.test(line)) {
        issues.push(`Line ${lineno}: Remove 'THEN' keyword — SAP PCR does not use IF/THEN`);
      }

      // ── 2. IF/ELSE/ENDIF keywords ───────────────────────────────────
      if (/^IF\s+/i.test(line)) {
        issues.push(`Line ${lineno}: 'IF' is not SAP PCR syntax — use register comparison e.g. NUM?> 8`);
      }
      if (/^(ELSE|ENDIF)\b/i.test(line)) {
        issues.push(`Line ${lineno}: '${line.split(" ")[0]}' is not valid SAP PCR — use OUTWP for conditional exit`);
      }

      // ── 3. Indexed access AMT(x), NUM(x), RTE(x) ────────────────────
      if (/(AMT|NUM|RTE)\s*\(\s*\d+\s*\)/i.test(line)) {
        issues.push(`Line ${lineno}: Indexed access (e.g. AMT(1000)) not allowed — use 'AMT= NNNN'`);
      }

      // ── 4. Inline arithmetic ─────────────────────────────────────────
      if (/^(AMT|NUM|RTE)\s*=\s*.+[+\-*/].+/i.test(line)) {
        issues.push(`Line ${lineno}: Inline arithmetic not allowed — use separate operations (AMT+, AMT*, etc.)`);
      }

      // ── 5. Decimal percentage shortcut ───────────────────────────────
      const decPct = line.match(/^(AMT|NUM|RTE)\*\s+(\d+\.\d+)$/i);
      if (decPct) {
        const val = parseFloat(decPct[2]);
        if (val < 10) {
          issues.push(
            `Line ${lineno}: Use 'AMT* ${Math.round(val * 100)}' then 'AMT/ 100' instead of decimal '${decPct[2]}'`
          );
        }
      }

      // ── 6. ADDWT before init ─────────────────────────────────────────
      if (/^ADDWT\s+/i.test(line)) {
        if (!hasInit) {
          issues.push(`Line ${lineno}: ADDWT used before any AMT/NUM/RTE= initialization`);
        }
        // Validate ADDWT operand
        const addwtOp = line.replace(/^ADDWT\s+/i, "").trim();
        if (addwtOp !== "*" && !/^\d{4}$/.test(addwtOp)) {
          issues.push(`Line ${lineno}: ADDWT operand '${addwtOp}' must be a 4-digit wage type or *`);
        }
      }

      // ── 7. MULTI/DIVI operand check ──────────────────────────────────
      const multiDiviMatch = line.match(/^(MULTI|DIVI)\s+(\S+)$/i);
      if (multiDiviMatch) {
        const op2 = multiDiviMatch[2].toUpperCase();
        if (!["RTE", "NUM", "AMT"].includes(op2)) {
          issues.push(`Line ${lineno}: ${multiDiviMatch[1].toUpperCase()} operand must be RTE, NUM, or AMT — got '${op2}'`);
        }
      }

      // ── 8. Track register initialization ────────────────────────────
      if (/^(AMT|NUM|RTE)=\s+\S/i.test(line)) {
        hasInit = true;
      }

      // ── 9. Missing space between opcode and operand ──────────────────
      // e.g. AMT=1000 (no space)
      if (/^(AMT|NUM|RTE)[=+\-*/]\S/.test(line)) {
        issues.push(`Line ${lineno}: Missing space after operator — use 'AMT= 1000' not 'AMT=1000'`);
      }
    });

    return issues;
  }

  // ── Highlight helpers ─────────────────────────────────────────────────
  function getIssueSeverity(issue) {
    // All validator issues are errors in SAP PCR
    return "error";
  }

  // ── Public API ───────────────────────────────────────────────────────
  window.PCRAIValidator = {
    normalize,
    validate,
    getIssueSeverity,
    VALID_OPCODES,
  };
})();