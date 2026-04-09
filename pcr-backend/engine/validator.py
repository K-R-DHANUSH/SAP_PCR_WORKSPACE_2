"""
SAP PCR Validator — Maximum Coverage Edition
Validates every SAP PE02 PCR operation and structure.
Returns list of human-readable issues (empty = valid).
"""

import re
from typing import List

# ─────────────────────────────────────────────────────────────
#  COMPLETE VALID OPCODE SET  (sourced from PE02 + Excel reference)
# ─────────────────────────────────────────────────────────────
VALID_OPCODES = {
    # AMT register
    "AMT=", "AMT+", "AMT-", "AMT*", "AMT/",
    "AMT?>", "AMT?<", "AMT?=", "AMT?>=", "AMT?<=", "AMT?<>",
    # NUM register
    "NUM=", "NUM+", "NUM-", "NUM*", "NUM/",
    "NUM?>", "NUM?<", "NUM?=", "NUM?>=", "NUM?<=", "NUM?<>",
    # RTE register
    "RTE=", "RTE+", "RTE-", "RTE*", "RTE/",
    "RTE?>", "RTE?<", "RTE?=", "RTE?>=", "RTE?<=", "RTE?<>",
    # Cross-register
    "MULTI", "DIVI", "DIVID",
    # Output
    "ADDWT", "SUBWT", "ELIMI", "ADDNA", "ADDCU",
    # Control
    "OUTWP", "OUTWPP", "ZERO=", "SUPPRESS", "RESET", "BLOCK",
    # Table/field access
    "TABLE", "TABLB", "TABLP",
    # Other valid PCR operations
    "ACTIO", "AVERA", "COLER", "DTDIF", "PRINT",
    "SCLAS", "COLOP", "SUBRC", "VAKEY", "VALEN",
}

LOAD_OPS       = {"AMT=", "AMT+", "AMT-", "NUM=", "NUM+", "NUM-", "RTE=", "RTE+", "RTE-"}
SCALAR_OPS     = {"AMT*", "AMT/", "NUM*", "NUM/", "RTE*", "RTE/"}
COMPARE_OPS    = {
    "AMT?>", "AMT?<", "AMT?=", "AMT?>=", "AMT?<=", "AMT?<>",
    "NUM?>", "NUM?<", "NUM?=", "NUM?>=", "NUM?<=", "NUM?<>",
    "RTE?>", "RTE?<", "RTE?=", "RTE?>=", "RTE?<=", "RTE?<>",
}
WT_OUTPUT_OPS  = {"ADDWT", "SUBWT", "ELIMI", "ADDNA", "ADDCU"}
NO_OPERAND_OPS = {"OUTWP", "OUTWPP", "ZERO=", "SUPPRESS", "RESET"}
MULTI_REGS     = {"RTE", "NUM", "AMT"}

# Structural line patterns
RE_SEPARATOR   = re.compile(r"^\*+\s*$")
RE_WT_NODE     = re.compile(r"^/[A-Z0-9*?]{1,4}(\s|$)")
RE_RULE_HEADER = re.compile(r"^[A-Z][A-Z0-9]{3}\s+\S")


def _is_wt_or_star(s: str) -> bool:
    return s == "*" or re.match(r"^\d{4}$", s) is not None


def _is_numeric(s: str) -> bool:
    return re.match(r"^-?\d+(\.\d+)?$", s) is not None


def _parse_opcode(line: str):
    """Parse opcode and operand from a PCR line."""
    # Compound: AMT?>, NUM?<=, AMT=, AMT*, etc.
    m = re.match(r"^([A-Z]{2,6}[=+\-*/]|[A-Z]{2,6}\?[><=]{1,2})\s*(.*)", line.strip())
    if m:
        return m.group(1).upper(), m.group(2).strip()
    # Word: ADDWT, MULTI, OUTWP, etc.
    m = re.match(r"^([A-Z]{2,8})\s*(.*)", line.strip())
    if m:
        return m.group(1).upper(), m.group(2).strip()
    return line.strip().upper(), ""


def validate(lines: List[str]) -> List[str]:
    """
    Validate PCR lines. Returns list of issue strings.
    Empty list = valid PCR.
    """
    issues = []
    has_header = False
    has_node   = False
    has_init   = False
    addwt_seen = False
    node_ops   = 0

    for i, raw in enumerate(lines):
        line   = raw.strip()
        lineno = i + 1

        if not line:
            continue

        # ── Structural lines ───────────────────────────────────
        if RE_SEPARATOR.match(line):
            continue

        if RE_WT_NODE.match(line):
            # Check previous node had ADDWT
            if node_ops > 0 and not addwt_seen:
                issues.append(f"Line {lineno}: Previous wage type node has operations but no ADDWT — result lost")
            has_node  = True
            has_init  = False
            addwt_seen = False
            node_ops  = 0
            continue

        if RE_RULE_HEADER.match(line) and not has_header and i <= 3:
            has_header = True
            continue

        node_ops += 1

        # ── Absolute forbidden patterns ────────────────────────
        if re.search(r"\bTHEN\b", line, re.IGNORECASE):
            issues.append(f"Line {lineno}: 'THEN' is not valid SAP PCR — use register comparison e.g. NUM?> 8")

        if re.match(r"^IF\b", line, re.IGNORECASE):
            issues.append(f"Line {lineno}: 'IF' is not valid SAP PCR — use 'NUM?> 8' style comparisons")
            continue

        if re.match(r"^(ELSE|ELSEIF|ENDIF)\b", line, re.IGNORECASE):
            issues.append(f"Line {lineno}: '{line.split()[0].upper()}' is not valid SAP PCR — use OUTWP for conditional exit")
            continue

        # Indexed access AMT(1000)
        if re.match(r"^(AMT|NUM|RTE)\s*\(", line, re.IGNORECASE):
            issues.append(f"Line {lineno}: Indexed access not allowed — use 'AMT= 1000' format")
            continue

        # Inline arithmetic
        if re.match(r"^(AMT|NUM|RTE)\s*=\s*\S+\s*[+\-*/]\s*\S+", line, re.IGNORECASE):
            issues.append(f"Line {lineno}: Inline arithmetic not allowed — use separate operations")
            continue

        # Missing space between opcode and operand
        if re.match(r"^(AMT|NUM|RTE)[=+\-*/]\S", line):
            issues.append(f"Line {lineno}: Missing space after operator — write 'AMT= 1000' not 'AMT=1000'")
            continue

        # ── Parse and validate opcode ──────────────────────────
        opcode, operand = _parse_opcode(line)

        # Unknown opcode
        if opcode not in VALID_OPCODES:
            if re.match(r"^[A-Z]{2,}", opcode):
                issues.append(f"Line {lineno}: Unknown SAP PCR operation '{opcode}'")
            continue

        # ── No-operand ops ─────────────────────────────────────
        if opcode in NO_OPERAND_OPS:
            if operand:
                issues.append(f"Line {lineno}: '{opcode}' takes no operand — remove '{operand}'")
            continue

        # ── MULTI / DIVI ───────────────────────────────────────
        if opcode in ("MULTI", "DIVI", "DIVID"):
            if not operand:
                issues.append(f"Line {lineno}: '{opcode}' requires a register: RTE, NUM, or AMT")
            elif operand.upper() not in MULTI_REGS:
                issues.append(f"Line {lineno}: '{opcode}' operand must be RTE, NUM, or AMT — got '{operand}'")
            if not has_init:
                issues.append(f"Line {lineno}: '{opcode}' used before any register initialization")
            continue

        # ── Load ops ───────────────────────────────────────────
        if opcode in LOAD_OPS:
            if not operand:
                issues.append(f"Line {lineno}: '{opcode}' requires a wage type — e.g. '{opcode} 1000'")
            elif not _is_wt_or_star(operand) and not re.match(r"^[A-Z]{2,6}$", operand):
                issues.append(f"Line {lineno}: '{opcode}' operand '{operand}' must be a 4-digit wage type or *")
            if opcode in ("AMT=", "NUM=", "RTE="):
                has_init = True
            continue

        # ── Scalar ops ─────────────────────────────────────────
        if opcode in SCALAR_OPS:
            if not operand:
                issues.append(f"Line {lineno}: '{opcode}' requires a numeric scalar — e.g. '{opcode} 100'")
            elif not _is_numeric(operand):
                issues.append(f"Line {lineno}: '{opcode}' operand '{operand}' must be a number")
            else:
                val = float(operand)
                if "." in operand and val < 10:
                    reg = opcode[:3]
                    int_val = int(round(val * 100))
                    issues.append(
                        f"Line {lineno}: Decimal percentage '{operand}' not allowed — "
                        f"use '{reg}* {int_val}' then '{reg}/ 100'"
                    )
                if opcode.endswith("/") and val == 0:
                    issues.append(f"Line {lineno}: Division by zero — '{opcode} 0' will crash payroll")
            continue

        # ── Compare ops ────────────────────────────────────────
        if opcode in COMPARE_OPS:
            if not operand:
                issues.append(f"Line {lineno}: '{opcode}' requires a comparison value — e.g. '{opcode} 8'")
            elif not _is_numeric(operand):
                issues.append(f"Line {lineno}: '{opcode}' comparison value '{operand}' must be a number")
            has_init = True
            continue

        # ── Output ops ─────────────────────────────────────────
        if opcode in WT_OUTPUT_OPS:
            if opcode == "ADDWT":
                if not has_init:
                    issues.append(f"Line {lineno}: ADDWT before any register initialization — load a register first")
                if not operand:
                    issues.append(f"Line {lineno}: ADDWT requires a wage type — e.g. 'ADDWT 9000'")
                elif not _is_wt_or_star(operand):
                    issues.append(f"Line {lineno}: ADDWT target '{operand}' must be a 4-digit wage type or *")
                addwt_seen = True
            else:
                if not operand or not _is_wt_or_star(operand):
                    issues.append(f"Line {lineno}: '{opcode}' requires a 4-digit wage type — e.g. '{opcode} 9000'")
            continue

    # ── End checks ─────────────────────────────────────────────
    if not has_header:
        issues.append("PCR missing rule header — first line should be e.g. 'Z001 My rule description'")
    if not has_node:
        issues.append("PCR has no wage type node — add '/NNNN Description' line")
    if node_ops > 0 and not addwt_seen:
        issues.append("Last wage type node has operations but no ADDWT — result will be lost")

    return issues