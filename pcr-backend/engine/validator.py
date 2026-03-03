def validate(pcr_lines: list):

    if not pcr_lines:
        raise ValueError("Empty PCR output")

    first_line = pcr_lines[0].strip()

    if first_line.startswith("ADDWT"):
        raise ValueError("PCR cannot start with ADDWT")

    for line in pcr_lines:
        if "MULTI " in line and not any(x in line for x in ["RTE", "AMT", "NUM"]):
            raise ValueError("MULTI must specify RTE, AMT or NUM")

    return True