def validate(pcr_lines: list):

    if not pcr_lines:
        raise ValueError("Empty PCR output")

    first_line = pcr_lines[0].strip()

    if first_line.startswith("ADDWT"):
        raise ValueError("PCR cannot start with ADDWT")

    # --------------------------------
    # VALID FIELD INITIALIZATION
    # --------------------------------
    has_amt = any(line.startswith("AMT=") for line in pcr_lines)
    has_num = any(line.startswith("NUM=") for line in pcr_lines)

    if not has_amt and not has_num:
        raise ValueError("PCR must initialize AMT or NUM")

    # --------------------------------
    # MULTI VALIDATION
    # --------------------------------
    for line in pcr_lines:
        if "MULTI " in line and not any(x in line for x in ["RTE", "AMT", "NUM"]):
            raise ValueError("MULTI must specify RTE, AMT or NUM")

    # --------------------------------
    # ADDWT SAFETY
    # --------------------------------
    for line in pcr_lines:
        if line.strip() == "ADDWT *":
            raise ValueError("Unsafe ADDWT * detected")

    return True