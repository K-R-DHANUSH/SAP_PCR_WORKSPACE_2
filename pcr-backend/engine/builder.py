# pcr-backend/engine/builder.py

def build_pcr(intent: str, params: dict) -> list:
    """
    Build SAP PCR lines based on intent + extracted parameters.
    Returns list of PCR lines (strings).
    """

    if intent == "PERCENT_INCREASE":
        return build_percent_increase(params)

    if intent == "MULTIPLY_AMOUNT":
        return build_multiply(params)

    if intent == "THRESHOLD_CHECK":
        return build_threshold(params)

    # fallback
    return [
        "RTE= 0",
        "ADDWT *"
    ]

def build_complex_overtime(params: dict) -> list:
    wage_types = params.get("wage_types", [])
    percent = params.get("percent")
    threshold = params.get("threshold")

    if len(wage_types) < 3:
        raise ValueError("Not enough wage types provided")

    hours_wt = wage_types[0]
    basic_wt = wage_types[1]
    result_wt = wage_types[2]

    return [
        f"AMT?{threshold}",
        f"IF AMT > {threshold}",
        f"RTE= {percent}",
        f"MULTI {basic_wt}",
        "DIVI 100",
        f"ADDWT {result_wt}",
        "ENDIF"
    ]

# -------------------------------
# 150% / percent logic
# -------------------------------
def build_percent_increase(params: dict) -> list:
    wt = params.get("wage_type", "*")
    percent = params.get("percent", 100)

    return [
        f"RTE= {percent}",
        "MULTI RTE",
        "DIVI 100",
        f"ADDWT {wt}"
    ]


# -------------------------------
# Multiply logic
# -------------------------------
def build_multiply(params: dict) -> list:
    wt = params.get("wage_type", "*")
    multiplier = params.get("multiplier", 1)

    return [
        f"RTE= {multiplier}",
        "MULTI RTE",
        f"ADDWT {wt}"
    ]


# -------------------------------
# Threshold IF logic
# -------------------------------
def build_threshold(params: dict) -> list:
    wt = params.get("wage_type", "*")
    threshold = params.get("threshold", 0)

    return [
        f"IF AMT > {threshold}",
        f"ADDWT {wt}",
        "ENDIF"
    ]