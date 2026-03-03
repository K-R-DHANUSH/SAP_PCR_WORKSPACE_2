import re

def extract_params(prompt: str, intent: str) -> dict:
    prompt_lower = prompt.lower()
    params = {}

    # -----------------------
    # Extract wage types (4 digit)
    # -----------------------
    wage_types = re.findall(r"\b\d{4}\b", prompt)
    if wage_types:
        params["wage_types"] = wage_types

    # -----------------------
    # Extract percent
    # -----------------------
    percent_match = re.search(r"(\d+)\s*%", prompt)
    if percent_match:
        params["percent"] = int(percent_match.group(1))

    # -----------------------
    # Extract threshold (handles typos + no space)
    # -----------------------
    threshold_match = re.search(
        r"(more than|more then|greater than)\s*(\d+)",
        prompt_lower
    )

    if not threshold_match:
        threshold_match = re.search(
            r"(more than|more then|greater than)\s*(\d+)\s*hours?",
            prompt_lower
        )

    if threshold_match:
        params["threshold"] = int(threshold_match.group(2))
        params["condition_operator"] = ">"

    # -----------------------
    # Detect complex overtime scenario
    # -----------------------
    if (
        "overtime" in prompt_lower
        and ("multiply" in prompt_lower or "*" in prompt_lower)
        and ("append" in prompt_lower or "store" in prompt_lower)
    ):
        params["operation"] = "OVERTIME_COMPLEX"

    return params