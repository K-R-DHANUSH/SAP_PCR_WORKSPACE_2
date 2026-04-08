"""
SAP PCR Validator
Enforces exact SAP PE02 PCR syntax rules.
Returns a list of human-readable issue strings (empty = valid).
"""

import re
from typing import List

# Lines that are structural (not operations) — skip deep validation
HEADER_PATTERN = re.compile(r"^[A-Z0-9]{4}\s+.+")           # Z001 Rule description
WT_NODE_PATTERN = re.compile(r"^/\d{4}(\s.*)?$")             # /2000 Wage type
SEPARATOR_PATTERN = re.compile(r"^\*\s*$")                   # *

# All valid SAP PCR opcodes
VALID_OPCODES = {
    "AMT=", "AMT+", "AMT-", "AMT*", "AMT/",
    "AMT?>", "AMT?<", "AMT?=", "AMT?>=", "AMT?<=",
    "NUM=", "NUM+", "NUM-", "NUM*", "NUM/",
    "NUM?>", "NUM?<", "NUM?=", "NUM?>=", "NUM?<=",
    "RTE=", "RTE*", "RTE/",
    "RTE?>", "RTE?<", "RTE?=",
    "MULTI", "DIVI",
    "ADDWT", "SUBWT",
    "OUTWP", "OUTWPP",
    "ZERO=", "SUPPRESS",
    "PRINT", "TABLE",
}

# Opcodes that require an operand
REQUIRES_OPERAND = {
    "AMT=", "AMT+", "AMT-", "AMT*", "AMT/",
    "NUM=", "NUM+", "NUM-", "NUM*", "NUM/",
    "RTE=", "RTE*", "RTE/",
    "AMT?>", "AMT?<", "AMT?=",
    "NUM?>", "NUM?<", "NUM?=",
    "RTE?>", "RTE?<", "RTE?=",
    "MULTI", "DIVI",
    "ADDWT", "SUBWT",
}

# Opcodes that take NO operand
NO_OPERAND = {"OUTWP", "OUTWPP", "ZERO=", "SUPPRESS"}

# Registers for MULTI/DIVI
MULTI_DIVI_OPERANDS = {"RTE", "NUM", "AMT"}


class ValidationError(Exception):
    pass


def validate(lines: List[str]) -> List[str]:
    """
    Validate PCR lines. Returns list of issue strings.
    Empty list = valid PCR.
    """
    issues = []

    if not lines:
        return ["PCR is empty"]

    has_init = False   # tracks if AMT=, NUM=, or RTE= seen before ADDWT
    has_addwt = False

    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        lineno = i + 1

        if not line:
            continue

        # ── Skip structural lines ──────────────────────────
        if SEPARATOR_PATTERN.match(line):
            continue
        if WT_NODE_PATTERN.match(line):
            # Reset init tracker per wage type node
            has_init = False
            continue
        if HEADER_PATTERN.match(line) and i <= 2:
            continue

        # ── Forbidden patterns ─────────────────────────────

        # THEN keyword
        if re.search(r"\bTHEN\b", line, re.IGNORECASE):
            issues.append(f"Line {lineno}: 'THEN' keyword is not valid in SAP PCR — remove it")

        # Indexed access e.g. AMT(1000), NUM(2001)
        if re.match(r"^(AMT|NUM|RTE)\s*\(\s*\d+\s*\)", line, re.IGNORECASE):
            issues.append(f"Line {lineno}: Indexed access '{line}' is not allowed — use 'AMT= NNNN' format")

        # Inline math expressions
        if re.search(r"(AMT|NUM|RTE)\s*=\s*.+[+\-*/].+", line, re.IGNORECASE):
            issues.append(f"Line {lineno}: Inline arithmetic not allowed — use separate AMT+, AMT*, etc. operations")

        # IF/THEN pattern (not valid PCR)
        if re.match(r"^IF\s+", line, re.IGNORECASE):
            issues.append(f"Line {lineno}: 'IF' keyword is not valid SAP PCR — use register comparison (e.g. NUM?> 8)")

        # ELSE/ENDIF (not valid PCR)
        if re.match(r"^(ELSE|ENDIF)\b", line, re.IGNORECASE):
            issues.append(f"Line {lineno}: '{line.split()[0]}' is not valid SAP PCR syntax — use OUTWP for conditional exit")

        # ── Parse the opcode ──────────────────────────────
        # Handle condition operators like AMT?>, NUM?<
        cond_match = re.match(r"^(AMT|NUM|RTE)\?([><=]{1,2})\s+(.+)$", line)
        assign_match = re.match(r"^(AMT[=+\-*/]|NUM[=+\-*/]|RTE[=*/])\s+(.+)$", line)
        word_match = re.match(r"^([A-Z=?<>+\-*/]{2,8})\s*(.*)$", line)

        if cond_match:
            reg, op, operand = cond_match.groups()
            operand = operand.strip()
            # Operand must be numeric
            if not re.match(r"^-?\d+(\.\d+)?$", operand):
                issues.append(f"Line {lineno}: Condition operand '{operand}' must be a number")
            has_init = True
            continue

        if assign_match:
            opcode, operand = assign_match.groups()
            operand = operand.strip()
            opcode_up = opcode.upper()

            # Track initialization
            if opcode_up in ("AMT=", "NUM=", "RTE="):
                has_init = True

            # Operand must be numeric or * or a 4-digit wage type
            if opcode_up in ("AMT=", "NUM=", "RTE=", "AMT+", "AMT-", "NUM+", "NUM-"):
                if operand != "*" and not re.match(r"^\d{4}$", operand) and not re.match(r"^-?\d+$", operand):
                    issues.append(
                        f"Line {lineno}: Operand '{operand}' for {opcode_up} must be a 4-digit wage type, *, or a number"
                    )
            elif opcode_up in ("AMT*", "AMT/", "NUM*", "NUM/", "RTE*", "RTE/"):
                if not re.match(r"^\d+(\.\d+)?$", operand):
                    issues.append(f"Line {lineno}: Scalar operand '{operand}' for {opcode_up} must be a number")
                # Warn about decimal percentage shortcut
                if "." in operand and float(operand) < 10:
                    issues.append(
                        f"Line {lineno}: Use 'AMT* 150' then 'AMT/ 100' instead of decimal '{operand}' for percentages"
                    )
            continue

        # Word opcode (ADDWT, SUBWT, MULTI, DIVI, OUTWP, etc.)
        if word_match:
            opcode = word_match.group(1).upper()
            operand = word_match.group(2).strip()

            if opcode == "ADDWT":
                has_addwt = True
                if not has_init and lineno > 3:
                    issues.append(f"Line {lineno}: ADDWT appears before any AMT/NUM/RTE initialization")
                if operand != "*" and not re.match(r"^\d{4}$", operand):
                    issues.append(f"Line {lineno}: ADDWT operand '{operand}' must be a 4-digit wage type or *")

            elif opcode == "SUBWT":
                if not re.match(r"^\d{4}$", operand):
                    issues.append(f"Line {lineno}: SUBWT operand '{operand}' must be a 4-digit wage type")

            elif opcode in ("MULTI", "DIVI"):
                if operand.upper() not in MULTI_DIVI_OPERANDS:
                    issues.append(
                        f"Line {lineno}: {opcode} operand '{operand}' must be RTE, NUM, or AMT"
                    )

            elif opcode in NO_OPERAND:
                if operand:
                    issues.append(f"Line {lineno}: {opcode} takes no operand — remove '{operand}'")

            elif opcode not in VALID_OPCODES and not WT_NODE_PATTERN.match(line) and not HEADER_PATTERN.match(line):
                # Unknown opcode — but only flag if it looks like an intended opcode
                if len(opcode) >= 3 and re.match(r"^[A-Z]+", opcode):
                    issues.append(f"Line {lineno}: Unknown SAP PCR operation '{opcode}'")

    return issues