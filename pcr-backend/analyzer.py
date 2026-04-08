def analyze_failure(expected, actual):

    issues = []

    if "AMT=" not in "\n".join(actual):
        issues.append("Missing AMT initialization")

    if "NUM=" in "\n".join(expected) and "NUM=" not in "\n".join(actual):
        issues.append("Overtime logic missing")

    if any("AMT+" in e for e in expected) and not any("AMT+" in a for a in actual):
        issues.append("Addition logic missing")

    if any("AMT*" in e for e in expected) and not any("AMT*" in a for a in actual):
        issues.append("Percent logic missing")

    return issues