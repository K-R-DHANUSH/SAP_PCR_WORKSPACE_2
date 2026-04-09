"""
SAP PCR Builder — Full Scenario Coverage (Corrected & Robust)
Builds valid SAP PE02 PCR lines from extracted parameters.
"""

from typing import List, Dict, Any

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _pct_lines(register: str, percent: float) -> List[str]:
    """Generate SAP integer percentage lines."""
    if percent == int(percent):
        return [f"{register}* {int(percent)}", f"{register}/ 100"]

    scaled_100 = percent * 100
    if scaled_100 == int(scaled_100):
        return [f"{register}* {int(scaled_100)}", f"{register}/ 10000"]

    scaled_10 = percent * 10
    if scaled_10 == int(scaled_10):
        return [f"{register}* {int(scaled_10)}", f"{register}/ 1000"]

    rounded = round(percent)
    return [f"{register}* {rounded}", f"{register}/ 100"]


def _source(params: Dict) -> str:
    return params.get("source_wage_type", "1000")


def _target(params: Dict) -> str:
    return params.get("target_wage_type", "9000")


def _register(params: Dict) -> str:
    return params.get("register_hint", "AMT")


def _multiply_amt_by_num(lines: List[str], num_wt: str):
    """Multiply AMT with NUM using correct SAP PCR logic."""
    lines.append("RTE= AMT")
    lines.append(f"NUM= {num_wt}")
    lines.append("MULTI RTE")


# ─────────────────────────────────────────────────────────────
# SCENARIO BUILDERS
# ─────────────────────────────────────────────────────────────

def _build_overtime(params: Dict) -> List[str]:
    hours_wt = params.get("hours_wt", "3010")
    source_wt = _source(params)
    target_wt = _target(params)
    percent = params.get("percent", 18)
    threshold = params.get("threshold", 8)

    lines = [f"NUM= {hours_wt}"]
    lines.append(f"NUM?> {threshold}")
    lines.append(f"AMT= {source_wt}")
    lines.extend(_pct_lines("AMT", percent))
    _multiply_amt_by_num(lines, hours_wt)
    lines.append(f"ADDWT {target_wt}")
    return lines


def _build_rate_hours(params: Dict) -> List[str]:
    rate_wt = params.get("rate_wt", "1100")
    hours_wt = params.get("hours_wt", "9100")
    target_wt = _target(params)
    return [
        f"RTE= {rate_wt}",
        f"NUM= {hours_wt}",
        "MULTI RTE",
        f"ADDWT {target_wt}"
    ]


def _build_percent(params: Dict) -> List[str]:
    lines = [f"AMT= {_source(params)}"]
    lines.extend(_pct_lines("AMT", params.get("percent", 100)))
    lines.append(f"ADDWT {_target(params)}")
    return lines


def _build_fixed_add(params: Dict) -> List[str]:
    lines = [f"AMT= {_source(params)}"]
    if params.get("add_wage_type"):
        lines.append(f"AMT+ {params['add_wage_type']}")
    elif params.get("add_amount") is not None:
        lines.append(f"AMT+ {int(params['add_amount']):04d}")
    lines.append(f"ADDWT {_target(params)}")
    return lines


def _build_fixed_sub(params: Dict) -> List[str]:
    lines = [f"AMT= {_source(params)}"]
    if params.get("sub_wage_type"):
        lines.append(f"AMT- {params['sub_wage_type']}")
    elif params.get("sub_amount") is not None:
        lines.append(f"AMT- {int(params['sub_amount']):04d}")
    lines.append(f"ADDWT {_target(params)}")
    return lines


def _build_copy(params: Dict) -> List[str]:
    return [f"AMT= {_source(params)}", f"ADDWT {_target(params)}"]


def _build_absence(params: Dict) -> List[str]:
    wts = params.get("wage_types", [])
    percent = params.get("percent")
    source = _source(params)
    target = _target(params)

    if len(wts) >= 3:
        return [
            f"NUM= {wts[0]}",
            f"AMT= {wts[1]}",
            "DIVI NUM",
            f"NUM= {wts[2]}",
            "MULTI RTE",
            "AMT* -1",
            f"ADDWT {target}"
        ]
    elif percent:
        lines = [f"AMT= {source}"]
        lines.extend(_pct_lines("AMT", percent))
        lines.append("AMT* -1")
        lines.append(f"ADDWT {target}")
        return lines
    else:
        return [f"AMT= {source}", f"ADDWT {target}"]


def _build_allowance(params: Dict) -> List[str]:
    source = _source(params)
    target = _target(params)
    percent = params.get("percent")

    lines = [f"AMT= {source}"]
    if percent:
        lines.extend(_pct_lines("AMT", percent))
    lines.append(f"ADDWT {target}")
    return lines


def _build_tax_deduction(params: Dict) -> List[str]:
    source = _source(params)
    target = _target(params)
    percent = params.get("percent", 20)

    lines = [f"AMT= {source}"]
    lines.extend(_pct_lines("AMT", percent))
    lines.append(f"ADDWT {target}")
    return lines


def _build_reset_suppress(params: Dict) -> List[str]:
    action = params.get("action", "ZERO")
    source = _source(params)
    if action == "SUPPRESS":
        return [f"AMT= {source}", "SUPPRESS"]
    else:
        return [f"AMT= {source}", "ZERO=", f"ADDWT {source}"]


def _build_accumulate(params: Dict) -> List[str]:
    sources = params.get("source_wage_types", [])
    target = _target(params)

    if not sources:
        return [f"AMT= {_source(params)}", f"ADDWT {target}"]

    lines = [f"AMT= {sources[0]}"]
    for wt in sources[1:]:
        lines.append(f"AMT+ {wt}")
    lines.append(f"ADDWT {target}")
    return lines


def _build_threshold(params: Dict) -> List[str]:
    source = _source(params)
    target = _target(params)
    threshold = params.get("threshold", 0)
    op = params.get("condition_operator", ">")
    percent = params.get("percent")
    reg = _register(params)
    wts = params.get("wage_types", [])
    check_wt = params.get("hours_wt", wts[0] if wts else source)
    thresh_val = int(threshold) if threshold == int(threshold) else threshold

    lines = [
        f"{reg}= {check_wt}",
        f"{reg}?{op} {thresh_val}",
        f"AMT= {source}"
    ]
    if percent:
        lines.extend(_pct_lines("AMT", percent))
    lines.append(f"ADDWT {target}")
    return lines


def _build_proration(params: Dict) -> List[str]:
    source = _source(params)
    target = _target(params)
    days_wt = params.get("days_wt", "9010")
    divisor = params.get("divisor", 26)

    lines = [f"AMT= {source}"]
    _multiply_amt_by_num(lines, days_wt)
    lines.append(f"AMT/ {int(divisor)}")
    lines.append(f"ADDWT {target}")
    return lines


def _build_loss_of_pay(params: Dict) -> List[str]:
    source = _source(params)
    target = _target(params)
    days_wt = params.get("days_wt", "9010")
    divisor = params.get("divisor", 26)

    lines = [
        f"AMT= {source}",
        f"AMT/ {int(divisor)}"
    ]
    _multiply_amt_by_num(lines, days_wt)
    lines.append(f"ADDWT {target}")
    return lines


def _build_leave_encashment(params: Dict) -> List[str]:
    source = _source(params)
    target = _target(params)
    days_wt = params.get("leave_days_wt", "9110")
    divisor = params.get("divisor", 26)

    lines = [f"AMT= {source}", f"AMT/ {divisor}"]
    _multiply_amt_by_num(lines, days_wt)
    lines.append(f"ADDWT {target}")
    return lines


def _build_gratuity(params: Dict) -> List[str]:
    source = _source(params)
    target = _target(params)
    years_wt = params.get("years_wt", "9120")

    lines = [
        f"AMT= {source}",
        "AMT/ 26",
        "AMT* 15"
    ]
    _multiply_amt_by_num(lines, years_wt)
    lines.append(f"ADDWT {target}")
    return lines


def _build_generic(params: Dict) -> List[str]:
    source = _source(params)
    target = _target(params)

    lines = [f"AMT= {source}"]
    if params.get("percent"):
        lines.extend(_pct_lines("AMT", params["percent"]))
    if params.get("multiplier"):
        lines.append(f"AMT* {int(params['multiplier'])}")
    lines.append(f"ADDWT {target}")
    return lines


# ─────────────────────────────────────────────────────────────
# SCENARIO REGISTRY
# ─────────────────────────────────────────────────────────────

SCENARIO_BUILDERS = {
    "OVERTIME": _build_overtime,
    "RATE_HOURS": _build_rate_hours,
    "PERCENT": _build_percent,
    "PERCENT_INCREASE": _build_percent,
    "PERCENT_DECREASE": _build_percent,
    "FIXED_ADD": _build_fixed_add,
    "FIXED_SUB": _build_fixed_sub,
    "COPY_WT": _build_copy,
    "ABSENCE": _build_absence,
    "ALLOWANCE": _build_allowance,
    "TAX_DEDUCTION": _build_tax_deduction,
    "RESET_SUPPRESS": _build_reset_suppress,
    "ACCUMULATE": _build_accumulate,
    "THRESHOLD": _build_threshold,
    "PRORATION": _build_proration,
    "LOSS_OF_PAY": _build_loss_of_pay,
    "LEAVE_ENCASHMENT": _build_leave_encashment,
    "GRATUITY": _build_gratuity,
    "GENERIC": _build_generic,
}


# ─────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

def build_pcr(intent: str, params: Dict[str, Any]) -> List[str]:
    scenario = params.get("scenario", "GENERIC")
    builder = SCENARIO_BUILDERS.get(scenario, _build_generic)
    return builder(params)