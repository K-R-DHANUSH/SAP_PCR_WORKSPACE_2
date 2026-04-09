"""
SAP PCR Parameter Extractor — Full NLP Coverage
Extracts structured parameters from free-form natural language prompts.

Handles:
  - Context-aware wage type extraction (won't confuse amounts with WTs)
  - Overtime (simple, threshold-based, hours × rate)
  - Percentage operations (increase, decrease, surcharge)
  - Fixed add / subtract
  - Rate × hours calculation
  - Copy / transfer wage type
  - Absence deductions
  - Allowance / bonus additions
  - Tax / deduction withholding
  - Threshold / conditional branching
  - Multi-source wage type accumulation
  - Reset / zero / suppress
  - Proration / partial month
  - Leave encashment (annual/monthly/calendar basis)
  - Gratuity
  - Loss of pay
  - Named field access (KBTR, BETRG, ANZHL)
"""

import re
from typing import Dict, Any, List, Optional


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────

def _find_wage_types(prompt: str) -> List[str]:
    """
    Context-aware 4-digit wage type extraction.
    Extracts numbers that appear in a WT context only.
    """
    p = prompt.lower()
    found: List[str] = []
    seen: set = set()

    # Priority 1: explicit "wage type NNNN" or "wt NNNN"
    for m in re.finditer(r"(?:wage\s*type|wt)\s+(\d{4})\b", p):
        wt = m.group(1)
        if wt not in seen:
            found.append(wt)
            seen.add(wt)

    # Priority 2: "/NNNN" node notation
    for m in re.finditer(r"/(\d{4})\b", p):
        wt = m.group(1)
        if wt not in seen:
            found.append(wt)
            seen.add(wt)

    # Priority 3: contextual keywords
    ctx_patterns = [
        r"(?:from|source|using|take from|read from)\s+(\d{4})\b",
        r"(?:into|to|store in|result in|output to|target|save to)\s+(\d{4})\b",
        r"(?:hours? in|rate from|amount from|number from)\s+(\d{4})\b",
    ]
    for pat in ctx_patterns:
        for m in re.finditer(pat, p):
            wt = m.group(1)
            if wt not in seen:
                found.append(wt)
                seen.add(wt)

    # Priority 4: bare 4-digit numbers — but skip threshold/divisor contexts
    threshold_ctx = re.compile(
        r"(?:greater than|above|exceed|more than|less than|below|under|at least|at most|"
        r"minimum|maximum|over|threshold|hours?)\s+(\d+)\b"
    )
    threshold_numbers = {m.group(1) for m in threshold_ctx.finditer(p)}

    divisor_ctx = re.compile(
        r"(?:divided? by|dividing by|÷|/)\s*(\d{1,3})\b"
    )
    divisor_numbers = {m.group(1) for m in divisor_ctx.finditer(p)}

    # Also skip numbers that are clearly amounts/scalars
    scalar_ctx = re.compile(r"(?:\$|%|x|by\s+)(\d{4})\b")
    scalar_numbers = {m.group(1) for m in scalar_ctx.finditer(p)}

    skip = threshold_numbers | scalar_numbers | divisor_numbers

    for m in re.finditer(r"\b(\d{4})\b", p):
        wt = m.group(1)
        if wt not in seen and wt not in skip:
            found.append(wt)
            seen.add(wt)

    return found


def _extract_percent(prompt: str) -> Optional[float]:
    """Extract percentage value from prompt. Returns float or None."""
    p = prompt.lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)\b", p)
    if m:
        return float(m.group(1))
    word_map = {"hundred": 100, "fifty": 50, "twenty": 20, "ten": 10, "five": 5}
    for word, val in word_map.items():
        if word in p:
            return float(val)
    return None


def _extract_threshold(prompt: str) -> Optional[Dict]:
    """Extract threshold value and operator."""
    p = prompt.lower()
    patterns = [
        (r"(?:greater than|above|exceed(?:s|ing)?|more than|over)\s+(\d+(?:\.\d+)?)", ">"),
        (r"(?:less than|below|under|fewer than)\s+(\d+(?:\.\d+)?)", "<"),
        (r"(?:equal to|equals?|is)\s+(\d+(?:\.\d+)?)", "="),
        (r"(?:at least|not less than)\s+(\d+(?:\.\d+)?)", ">="),
        (r"(?:at most|not more than|not exceeding)\s+(\d+(?:\.\d+)?)", "<="),
        (r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:or more|and above)", ">="),
        (r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:or less|and below)", "<="),
    ]
    for pattern, op in patterns:
        m = re.search(pattern, p)
        if m:
            return {"threshold": float(m.group(1)), "operator": op}
    return None


def _extract_divisor(prompt: str) -> Optional[float]:
    """Extract divisor from phrases like 'divide by 26', 'divided by 30', '/365'."""
    p = prompt.lower()
    m = re.search(r"(?:divided? by|dividing by|÷|/\s*)(\d{1,4})\b", p)
    if m:
        val = float(m.group(1))
        # Only accept sensible payroll divisors
        if val in (26, 30, 31, 365, 208, 12, 52, 24):
            return val
    # Also detect "/" notation in formulas like "(Basic/26)"
    m = re.search(r"\(\s*\w+\s*/\s*(\d{1,4})\s*\)", p)
    if m:
        val = float(m.group(1))
        if val in (26, 30, 31, 365, 208, 12, 52, 24):
            return val
    return None


def _extract_multiplier(prompt: str) -> Optional[float]:
    """Extract a plain multiplier (not percent)."""
    p = prompt.lower()
    if "double" in p:
        return 2.0
    if "triple" in p:
        return 3.0
    if "quadruple" in p or "4x" in p:
        return 4.0
    m = re.search(r"(?:multiply|times|×|factor of|by)\s+(\d+(?:\.\d+)?)\s*(?:x\b)?", p)
    if m:
        val = float(m.group(1))
        if val != int(val) or val < 100:
            return val
    m = re.search(r"(\d+(?:\.\d+)?)\s*x\b", p)
    if m:
        return float(m.group(1))
    return None


def _extract_fixed_amount(prompt: str) -> Dict:
    """Extract fixed add/subtract amounts."""
    p = prompt.lower()
    result = {}
    add_m = re.search(r"(?:add|plus|\+|increase by)\s+(\d+)\b(?!\s*%)", p)
    if add_m:
        result["add_amount"] = int(add_m.group(1))
    sub_m = re.search(r"(?:deduct|subtract|minus|reduce by|decrease by)\s+(\d+)\b(?!\s*%)", p)
    if sub_m:
        result["sub_amount"] = int(sub_m.group(1))
    return result


# ─────────────────────────────────────────────────────────────
#  SCENARIO DETECTION
# ─────────────────────────────────────────────────────────────

def _detect_scenario(prompt: str, intent: str) -> str:
    """
    Determine the payroll scenario from natural language + classifier intent.
    Returns one of the scenario keys used by builder.py.
    """
    p = prompt.lower()

    # Explicit intent from classifier
    intent_map = {
        "OVERTIME":         "OVERTIME",
        "RATE_HOURS":       "RATE_HOURS",
        "COPY_WT":          "COPY_WT",
        "PERCENT_INCREASE": "PERCENT",
        "PERCENT_DECREASE": "PERCENT",
        "PERCENT_MULTI":    "PERCENT",
        "FIXED_ADD":        "FIXED_ADD",
        "FIXED_SUB":        "FIXED_SUB",
        "ABSENCE":          "ABSENCE",
        "ALLOWANCE":        "ALLOWANCE",
        "TAX_DEDUCTION":    "TAX_DEDUCTION",
        "RESET_SUPPRESS":   "RESET_SUPPRESS",
        "THRESHOLD":        "THRESHOLD",
        "ACCUMULATE":       "ACCUMULATE",
    }
    if intent in intent_map:
        # Refine certain classifier intents with NLP
        base = intent_map[intent]

        # Check for proration / leave encashment / gratuity / loss of pay within PERCENT or GENERIC
        if base in ("PERCENT", "GENERIC", "ABSENCE"):
            if any(w in p for w in ["leave encashment", "leave days", "encash"]):
                return "LEAVE_ENCASHMENT"
            if any(w in p for w in ["gratuity", "years of service", "years service"]):
                return "GRATUITY"
            if any(w in p for w in ["loss of pay", "lop", "absent days", "unpaid leave"]):
                return "LOSS_OF_PAY"
            if any(w in p for w in ["prorate", "pro-rate", "prorat", "partial month", "worked days", "actual days"]):
                return "PRORATION"

        return base

    # NLP fallback — ordered from most specific to least specific

    if any(w in p for w in ["leave encashment", "leave days", "encash"]):
        return "LEAVE_ENCASHMENT"

    if any(w in p for w in ["gratuity", "years of service"]):
        return "GRATUITY"

    if any(w in p for w in ["loss of pay", "lop"]):
        return "LOSS_OF_PAY"

    if any(w in p for w in ["prorate", "pro-rate", "prorat", "partial month", "worked days", "actual days"]):
        return "PRORATION"

    if any(w in p for w in ["overtime", "over time", "ot pay", "extra hours"]):
        return "OVERTIME"

    if any(w in p for w in ["rate", "hourly", "per hour"]) and \
       any(w in p for w in ["multiply", "times", "calculate pay", "×", "multi num"]):
        return "RATE_HOURS"

    if any(w in p for w in ["copy", "transfer", "move", "same as", "mirror", "replicate"]):
        return "COPY_WT"

    if any(w in p for w in ["absence", "leave", "absent", "unpaid"]):
        return "ABSENCE"

    if any(w in p for w in ["allowance", "bonus", "supplement", "housing", "transport", "meal",
                              "dearness", "hra", "lta", "medical"]):
        return "ALLOWANCE"

    if any(w in p for w in ["tax", "withhold", "tds", "pf deduction", "esi deduction",
                              "deduction", "contribution", "insurance", "provident", "paye"]):
        return "TAX_DEDUCTION"

    if any(w in p for w in ["suppress", "zero out", "reset", "clear", "nullify", "eliminate"]):
        return "RESET_SUPPRESS"

    if any(w in p for w in ["accumulate", "sum up", "combine", "aggregate", "total of",
                              "add together", "gross pay", "net pay"]):
        return "ACCUMULATE"

    if _extract_threshold(p):
        return "THRESHOLD"

    if _extract_percent(p):
        return "PERCENT"

    fixed = _extract_fixed_amount(p)
    if "add_amount" in fixed:
        return "FIXED_ADD"
    if "sub_amount" in fixed:
        return "FIXED_SUB"

    return "GENERIC"


# ─────────────────────────────────────────────────────────────
#  MAIN EXTRACT FUNCTION
# ─────────────────────────────────────────────────────────────

def extract_params(prompt: str, intent: str) -> Dict[str, Any]:
    """
    Extract all parameters needed by builder.py from a natural language prompt.
    """
    p       = prompt.lower()
    params: Dict[str, Any] = {}

    wage_types = _find_wage_types(prompt)
    if wage_types:
        params["wage_types"] = wage_types

    scenario = _detect_scenario(prompt, intent)
    params["scenario"] = scenario

    # ── WT assignment by scenario ─────────────────────────────
    if scenario == "OVERTIME":
        if len(wage_types) >= 3:
            params["hours_wt"]           = wage_types[0]
            params["source_wage_type"]   = wage_types[1]
            params["target_wage_type"]   = wage_types[-1]
            if len(wage_types) > 3:
                params["source_wage_types"] = wage_types[1:-1]
        elif len(wage_types) == 2:
            params["hours_wt"]           = wage_types[0]
            params["target_wage_type"]   = wage_types[1]
        elif len(wage_types) == 1:
            params["target_wage_type"]   = wage_types[0]

    elif scenario == "RATE_HOURS":
        rate_m  = re.search(r"rate\s+(?:from\s+)?(\d{4})\b", p)
        hours_m = re.search(r"hours?\s+(?:from\s+|in\s+)?(\d{4})\b", p)
        store_m = re.search(r"(?:into|store in|result in|output to)\s+(\d{4})\b", p)

        if rate_m:
            params["rate_wt"] = rate_m.group(1)
        elif len(wage_types) >= 1:
            params["rate_wt"] = wage_types[0]

        if hours_m:
            params["hours_wt"] = hours_m.group(1)
        elif len(wage_types) >= 2:
            params["hours_wt"] = wage_types[1]

        if store_m:
            params["target_wage_type"] = store_m.group(1)
        elif len(wage_types) >= 3:
            params["target_wage_type"] = wage_types[2]
        elif len(wage_types) == 2:
            params["target_wage_type"] = wage_types[-1]

    elif scenario == "ACCUMULATE":
        if len(wage_types) >= 2:
            params["source_wage_types"] = wage_types[:-1]
            params["target_wage_type"]  = wage_types[-1]
        elif len(wage_types) == 1:
            params["source_wage_type"]  = wage_types[0]
            params["target_wage_type"]  = wage_types[0]

    elif scenario in ("LEAVE_ENCASHMENT", "GRATUITY", "LOSS_OF_PAY", "PRORATION"):
        # First WT = source (basic pay), second-to-last = days/years WT, last = target
        if len(wage_types) >= 3:
            params["source_wage_type"] = wage_types[0]
            params["hours_wt"]         = wage_types[-2]
            params["target_wage_type"] = wage_types[-1]
        elif len(wage_types) == 2:
            params["source_wage_type"] = wage_types[0]
            params["hours_wt"]         = wage_types[0]
            params["target_wage_type"] = wage_types[1]
        elif len(wage_types) == 1:
            params["source_wage_type"] = wage_types[0]
            params["target_wage_type"] = wage_types[0]

        # Divisor extraction (26, 30, 365, etc.)
        divisor = _extract_divisor(prompt)
        if divisor:
            params["divisor"] = divisor
            if divisor == 365:
                params["formula"] = "annual"
            elif divisor == 30:
                params["formula"] = "calendar"
            else:
                params["formula"] = "monthly"

        # Days per year for gratuity (usually 15)
        grat_m = re.search(r"\b(15|30)\s*days?\b", p)
        if grat_m and scenario == "GRATUITY":
            params["days_per_year"] = int(grat_m.group(1))

    else:
        # Default: first = source, last = target
        if len(wage_types) >= 2:
            params["source_wage_type"] = wage_types[0]
            params["target_wage_type"] = wage_types[-1]
        elif len(wage_types) == 1:
            params["source_wage_type"] = wage_types[0]
            params["target_wage_type"] = wage_types[0]

    # ── Percentage ────────────────────────────────────────────
    pct = _extract_percent(prompt)
    if pct is not None:
        params["percent"] = pct

    # ── Threshold / condition ─────────────────────────────────
    thresh = _extract_threshold(prompt)
    if thresh:
        params["threshold"]          = thresh["threshold"]
        params["condition_operator"] = thresh["operator"]

    # ── Multiplier ────────────────────────────────────────────
    mult = _extract_multiplier(prompt)
    if mult and "percent" not in p:
        params["multiplier"] = mult

    # ── Fixed add / subtract ──────────────────────────────────
    fixed = _extract_fixed_amount(prompt)
    params.update(fixed)

    # ── Divisor (for non-leave scenarios needing division) ─────
    if "divisor" not in params:
        divisor = _extract_divisor(prompt)
        if divisor:
            params["divisor"] = divisor

    # ── Named fields ──────────────────────────────────────────
    if "kbtr" in p:
        params["named_field"] = "KBTR"
    elif "betrg" in p:
        params["named_field"] = "BETRG"
    elif "anzhl" in p:
        params["named_field"] = "ANZHL"

    # ── Register preference hint ──────────────────────────────
    if any(w in p for w in ["rate", "hourly rate", "rte"]):
        params["register_hint"] = "RTE"
    elif any(w in p for w in ["hours", "number", "count", "quantity", "days", "num"]):
        params["register_hint"] = "NUM"
    else:
        params["register_hint"] = "AMT"

    # ── Suppress / reset flag ─────────────────────────────────
    if scenario == "RESET_SUPPRESS":
        if any(w in p for w in ["suppress", "hide", "nullify", "remove output"]):
            params["action"] = "SUPPRESS"
        else:
            params["action"] = "ZERO"

    return params