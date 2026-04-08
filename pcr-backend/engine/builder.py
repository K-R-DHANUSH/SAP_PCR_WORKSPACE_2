# pcr-backend/engine/builder.py


def build_pcr(intent: str, params: dict) -> list:

    # --------------------------------
    # OVERTIME FIRST (PRIORITY)
    # --------------------------------
    if params.get("scenario") == "OVERTIME":
        return build_complex_overtime(params)

    lines = []

    source = params.get("source_wage_type", "1000")
    target = params.get("target_wage_type", "1000")

    # --------------------------------
    # STEP 1 — BASE
    # --------------------------------
    lines.append(f"AMT= {source}")

    # --------------------------------
    # STEP 2 — ADD
    # --------------------------------
    if "add_amount" in params:
        lines.append(f"AMT+ {params['add_amount']}")

    # --------------------------------
    # STEP 3 — SUBTRACT
    # --------------------------------
    if "sub_amount" in params:
        lines.append(f"AMT- {params['sub_amount']}")

    # --------------------------------
    # STEP 4 — THRESHOLD
    # --------------------------------
    if params.get("threshold"):
        lines.append(f"AMT?{params.get('condition_operator','>')}{params['threshold']}")

    # --------------------------------
    # STEP 5 — PERCENT
    # --------------------------------
    if "percent" in params:
        lines.append(f"AMT* {params['percent']}")
        lines.append("AMT/100")

    # --------------------------------
    # STEP 6 — MULTIPLIER
    # --------------------------------
    elif "multiplier" in params:
        lines.append(f"AMT* {params['multiplier']}")

    # --------------------------------
    # FINAL
    # --------------------------------
    lines.append(f"ADDWT {target}")

    return lines


# --------------------------------
# OVERTIME (FINAL)
# --------------------------------

def build_complex_overtime(params: dict) -> list:

    hours_wt = params.get("hours_wt")
    result_wt = params.get("target_wage_type")

    percent = params.get("percent", 100)
    threshold = params.get("threshold", 8)

    if not hours_wt or not result_wt:
        return ["NUM= 0", "ADDWT 1000"]

    lines = [
        f"NUM= {hours_wt}",
        f"NUM?{threshold}"
    ]

    sources = params.get("source_wage_types")

    if sources:
        lines.append(f"AMT= {sources[0]}")
        for wt in sources[1:]:
            lines.append(f"AMT+ {wt}")
    else:
        source = params.get("source_wage_type")
        if source:
            lines.append(f"AMT= {source}")

    # ADD support inside overtime
    if "add_amount" in params:
        lines.append(f"AMT+ {params['add_amount']}")

    if "sub_amount" in params:
        lines.append(f"AMT- {params['sub_amount']}")

    lines.extend([
        f"AMT* {percent}",
        "AMT/100",
        f"ADDWT {result_wt}"
    ])

    return lines