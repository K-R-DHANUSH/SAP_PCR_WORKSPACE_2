// scripts/ai-validator.js
// SAP PCR Frontend Validator — Full PE02 syntax coverage
// Mirrors validator.py rules so users see consistent errors in both editor and backend
(function () {
  "use strict";

  // ══════════════════════════════════════════════════════════
  //  COMPLETE VALID OPCODE TABLE (matches validator.py exactly)
  // ══════════════════════════════════════════════════════════
  const VALID_OPCODES = new Set([
    // AMT register
    "AMT=", "AMT+", "AMT-", "AMT*", "AMT/",
    "AMT?>", "AMT?<", "AMT?=", "AMT?>=", "AMT?<=", "AMT?<>",
    // NUM register
    "NUM=", "NUM+", "NUM-", "NUM*", "NUM/",
    "NUM?>", "NUM?<", "NUM?=", "NUM?>=", "NUM?<=", "NUM?<>",
    // RTE register
    "RTE=", "RTE+", "RTE-", "RTE*", "RTE/",
    "RTE?>", "RTE?<", "RTE?=", "RTE?>=", "RTE?<=", "RTE?<>",
    // Cross-register
    "MULTI", "DIVI", "DIVID",
    // Wage type transfer
    "ADDWT", "SUBWT", "ELIMI", "ADDIT", "SUBIT",
    // Control/exit
    "OUTWP", "OUTWPP",
    // Reset/suppress
    "ZERO=", "SUPPRESS", "RESET",
    // Table access
    "TABLB", "TABLP", "VARAB", "VARPA", "TABLE",
    // Field ops
    "FILLB", "SET", "GET",
    // Payroll ops
    "COLER", "DTDIF", "GCY", "HRS00", "PRINT", "ACTIO", "BLOCK", "PASSA",
    // Decision/branch
    "DECB", "DECP", "SCLAS", "COLOP",
  ]);

  // ── Operand categories ──────────────────────────────────────────────
  const LOAD_OPS = new Set([
    "AMT=", "AMT+", "AMT-", "NUM=", "NUM+", "NUM-", "RTE=", "RTE+", "RTE-"
  ]);

  const SCALAR_OPS = new Set([
    "AMT*", "AMT/", "NUM*", "NUM/", "RTE*", "RTE/"
  ]);

  const COMPARE_OPS = new Set([
    "AMT?>", "AMT?<", "AMT?=", "AMT?>=", "AMT?<=", "AMT?<>",
    "NUM?>", "NUM?<", "NUM?=", "NUM?>=", "NUM?<=", "NUM?<>",
    "RTE?>", "RTE?<", "RTE?=", "RTE?>=", "RTE?<=", "RTE?<>",
  ]);

  const WT_OPERAND_OPS = new Set(["ADDWT", "SUBWT", "ELIMI", "ADDIT", "SUBIT"]);
  const NO_OPERAND_OPS = new Set(["OUTWP", "OUTWPP", "ZERO=", "SUPPRESS", "RESET"]);
  const MULTI_DIVI_REGS = new Set(["RTE", "NUM", "AMT"]);

  // ── Helpers ──────────────────────────────────────────────────────────
  function is4DigitWT(s) {
    return /^\d{4}$/.test(s);
  }

  function isWTorStar(s) {
    return s === "*" || is4DigitWT(s);
  }

  function isNumeric(s) {
    return /^-?\d+(\.\d+)?$/.test(s);
  }

  function isInteger(s) {
    return /^-?\d+$/.test(s);
  }

  function isStructural(line) {
    if (!line || !line.trim()) return true;
    if (/^\*/.test(line.trim())) return true;          // * or ** comment
    if (/^\/[A-Z0-9*?]{1,4}(\s|$)/.test(line.trim())) return true;  // /NNNN node
    if (/^[A-Z][A-Z0-9]{3}\s+.+/.test(line.trim())) return true;    // rule header
    return false;
  }

  // ── Parse opcode + operand from a line ───────────────────────────────
  function parseOpcodeOperand(line) {
    // Compound opcodes: AMT?>, NUM?<=, AMT=, AMT*, etc.
    let m = line.match(/^([A-Z]{2,6}[=+\-*/]|[A-Z]{2,6}\?[><=]{1,2})\s*(.*)/);
    if (m) return [m[1].toUpperCase(), m[2].trim()];
    // Word opcodes: ADDWT, MULTI, OUTWP, etc.
    m = line.match(/^([A-Z]{2,8})\s*(.*)/);
    if (m) return [m[1].toUpperCase(), m[2].trim()];
    return [line.trim().toUpperCase(), ""];
  }

  // ── Normalise input ──────────────────────────────────────────────────
  function normalize(text) {
    return text
      .replace(/\r/g, "")
      .split("\n")
      .map(l => l.trimEnd());
  }

  // ══════════════════════════════════════════════════════════
  //  MAIN VALIDATE FUNCTION
  // ══════════════════════════════════════════════════════════
  function validate(lines) {
    const issues = [];

    let hasInit      = false;
    let hasHeader    = false;
    let hasNode      = false;
    let addwtTargets = new Set();
    let nodeOpCount  = 0;

    lines.forEach((rawLine, i) => {
      const line   = rawLine.trim();
      const lineno = i + 1;

      if (!line) return;

      // Comment / separator
      if (/^\*/.test(line)) return;

      // Rule header
      if (/^[A-Z][A-Z0-9]{3}\s+.+/.test(line) && !hasHeader && i <= 3) {
        hasHeader = true;
        return;
      }

      // Wage type node
      if (/^\/[A-Z0-9*?]{1,4}(\s|$)/.test(line)) {
        if (nodeOpCount > 0 && addwtTargets.size === 0) {
          issues.push(`Line ${lineno}: Previous node has operations but no ADDWT — result will be lost`);
        }
        hasInit      = false;
        addwtTargets = new Set();
        nodeOpCount  = 0;
        hasNode      = true;
        return;
      }

      nodeOpCount++;

      // ── Forbidden patterns ────────────────────────────────
      if (/\bTHEN\b/i.test(line)) {
        issues.push(`Line ${lineno}: 'THEN' is not valid SAP PCR — use register comparison e.g. NUM?> 8`);
      }

      if (/^IF\b/i.test(line)) {
        issues.push(`Line ${lineno}: 'IF' is not valid SAP PCR — use 'NUM?> 8' style comparisons`);
        return;
      }

      if (/^(ELSE|ELSEIF|ENDIF)\b/i.test(line)) {
        issues.push(`Line ${lineno}: '${line.split(" ")[0].toUpperCase()}' is not valid SAP PCR — use OUTWP for conditional exit`);
        return;
      }

      if (/^(FOR|WHILE|DO|LOOP)\b/i.test(line)) {
        issues.push(`Line ${lineno}: '${line.split(" ")[0].toUpperCase()}' is programming syntax, not valid SAP PCR`);
        return;
      }

      // Indexed access
      if (/^(AMT|NUM|RTE)\s*\(/i.test(line)) {
        issues.push(`Line ${lineno}: Indexed access not allowed — use 'AMT= 1000' format`);
        return;
      }

      // Inline math
      if (/^(AMT|NUM|RTE)\s*=\s*\S+\s*[+\-*/]\s*\S+/i.test(line)) {
        issues.push(`Line ${lineno}: Inline arithmetic not allowed — use separate operations`);
        return;
      }

      // Missing space after operator
      if (/^(AMT|NUM|RTE)[=+\-*/]\S/.test(line)) {
        issues.push(`Line ${lineno}: Missing space after operator — write 'AMT= 1000' not 'AMT=1000'`);
        return;
      }

      // ── Parse opcode + operand ────────────────────────────
      const [opcode, operand] = parseOpcodeOperand(line);

      // Unknown opcode
      if (!VALID_OPCODES.has(opcode)) {
        if (/^[A-Z]{2,}/.test(opcode)) {
          issues.push(`Line ${lineno}: Unknown SAP PCR operation '${opcode}'`);
        }
        return;
      }

      // ── No-operand ops ────────────────────────────────────
      if (NO_OPERAND_OPS.has(opcode)) {
        if (operand) {
          issues.push(`Line ${lineno}: '${opcode}' takes no operand — remove '${operand}'`);
        }
        return;
      }

      // ── MULTI / DIVI ──────────────────────────────────────
      if (opcode === "MULTI" || opcode === "DIVI" || opcode === "DIVID") {
        if (!operand) {
          issues.push(`Line ${lineno}: '${opcode}' requires a register operand: RTE, NUM, or AMT`);
        } else if (!MULTI_DIVI_REGS.has(operand.toUpperCase())) {
          issues.push(`Line ${lineno}: '${opcode}' operand must be RTE, NUM, or AMT — got '${operand}'`);
        }
        if (!hasInit) {
          issues.push(`Line ${lineno}: '${opcode}' used before any register initialization`);
        }
        return;
      }

      // ── Load ops ──────────────────────────────────────────
      if (LOAD_OPS.has(opcode)) {
        if (!operand) {
          issues.push(`Line ${lineno}: '${opcode}' requires a wage type operand e.g. '${opcode} 1000'`);
        } else if (!isWTorStar(operand) && !/^[A-Z]{4,6}$/.test(operand)) {
          issues.push(`Line ${lineno}: '${opcode}' operand '${operand}' must be a 4-digit wage type or *`);
        }
        if (opcode === "AMT=" || opcode === "NUM=" || opcode === "RTE=") {
          hasInit = true;
        }
        return;
      }

      // ── Scalar ops ────────────────────────────────────────
      if (SCALAR_OPS.has(opcode)) {
        if (!operand) {
          issues.push(`Line ${lineno}: '${opcode}' requires a numeric scalar e.g. '${opcode} 100'`);
        } else if (!isNumeric(operand)) {
          issues.push(`Line ${lineno}: '${opcode}' scalar '${operand}' must be a number`);
        } else {
          const val = parseFloat(operand);
          if (operand.includes(".") && val < 10) {
            issues.push(
              `Line ${lineno}: Avoid decimal '${operand}' for percentages — ` +
              `use '${opcode.slice(0,3)}* ${Math.round(val * 100)}' then '${opcode.slice(0,3)}/ 100'`
            );
          }
          if (opcode.endsWith("/") && val === 0) {
            issues.push(`Line ${lineno}: Division by zero — '${opcode} 0' will crash`);
          }
        }
        return;
      }

      // ── Comparison ops ────────────────────────────────────
      if (COMPARE_OPS.has(opcode)) {
        if (!operand) {
          issues.push(`Line ${lineno}: '${opcode}' requires a comparison value e.g. '${opcode} 8'`);
        } else if (!isNumeric(operand)) {
          issues.push(`Line ${lineno}: '${opcode}' comparison value '${operand}' must be a number`);
        }
        hasInit = true;
        return;
      }

      // ── ADDWT / SUBWT / ELIMI / ADDIT / SUBIT ────────────
      if (WT_OPERAND_OPS.has(opcode)) {
        if (opcode === "ADDWT") {
          if (!hasInit) {
            issues.push(`Line ${lineno}: ADDWT before any register initialization — load a register first`);
          }
          if (!operand) {
            issues.push(`Line ${lineno}: ADDWT requires a wage type e.g. 'ADDWT 9000'`);
          } else if (!isWTorStar(operand)) {
            issues.push(`Line ${lineno}: ADDWT target '${operand}' must be a 4-digit wage type or *`);
          } else {
            if (addwtTargets.has(operand)) {
              issues.push(`Line ${lineno}: ADDWT ${operand} appears twice in this node — check if intentional`);
            }
            addwtTargets.add(operand);
          }
        } else {
          if (!operand || !isWTorStar(operand)) {
            issues.push(`Line ${lineno}: '${opcode}' requires a 4-digit wage type e.g. '${opcode} 9000'`);
          }
        }
        return;
      }
    });

    // End-of-PCR checks
    if (!hasHeader) {
      issues.push("PCR is missing a rule header — first line should be e.g. 'Z001 My rule description'");
    }
    if (!hasNode) {
      issues.push("PCR has no wage type node — add '/NNNN Description' line");
    }
    if (nodeOpCount > 0 && addwtTargets.size === 0) {
      issues.push("Last wage type node has no ADDWT — computed result will be lost");
    }

    return issues;
  }

  // ── Severity classification ───────────────────────────────────────────
  function getIssueSeverity(issue) {
    const lower = issue.toLowerCase();
    if (
      lower.includes("division by zero") ||
      lower.includes("before any register") ||
      lower.includes("result will be lost") ||
      lower.includes("not valid sap pcr")
    ) return "error";
    if (
      lower.includes("avoid decimal") ||
      lower.includes("appears twice") ||
      lower.includes("no addwt")
    ) return "warning";
    return "info";
  }

  // ── Public API ────────────────────────────────────────────────────────
  window.PCRAIValidator = {
    normalize,
    validate,
    getIssueSeverity,
    VALID_OPCODES,
  };
})();