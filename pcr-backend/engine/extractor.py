import re


def extract_params(prompt: str, intent: str) -> dict:

    prompt_lower = prompt.lower()
    params = {}

    # --------------------------------
    # Extract all 4-digit numbers
    # --------------------------------
    all_numbers = re.findall(r"\b\d{4}\b", prompt)

    wage_types = []

    for num in all_numbers:
        # Skip threshold numbers
        if re.search(rf"(greater than|above|less than|below|exceed)\s*{num}", prompt_lower):
            continue
        wage_types.append(num)

    if wage_types:
        params["wage_types"] = wage_types

    # --------------------------------
    # SOURCE / TARGET DETECTION
    # --------------------------------
    if len(wage_types) >= 2:
        params["source_wage_type"] = wage_types[0]
        params["target_wage_type"] = wage_types[-1]

    elif len(wage_types) == 1:
        params["source_wage_type"] = wage_types[0]

    # --------------------------------
    # PERCENT
    # --------------------------------
    percent = re.search(r"(\d+(?:\.\d+)?)\s*%", prompt_lower)
    if percent:
        params["percent"] = float(percent.group(1))

    percent_words = re.search(r"(\d+)\s*percent", prompt_lower)
    if percent_words:
        params["percent"] = float(percent_words.group(1))

    # --------------------------------
    # MULTIPLIER
    # --------------------------------
    mult = re.search(r"by\s*(\d+(?:\.\d+)?)", prompt_lower)
    if mult:
        params["multiplier"] = float(mult.group(1))

    if "double" in prompt_lower:
        params["multiplier"] = 2

    if "triple" in prompt_lower:
        params["multiplier"] = 3

    # --------------------------------
    # FIXED ADD
    # --------------------------------
    add_match = re.search(r"(add|plus)\s+(\d+)", prompt_lower)
    if add_match:
        params["add_amount"] = int(add_match.group(2))

    # --------------------------------
    # FIXED SUBTRACT
    # --------------------------------
    sub_match = re.search(r"(deduct|subtract|minus)\s+(\d+)", prompt_lower)
    if sub_match:
        params["sub_amount"] = int(sub_match.group(2))

    # --------------------------------
    # THRESHOLD
    # --------------------------------
    threshold_match = re.search(
        r"(greater than|above|exceed)\s*(\d+)",
        prompt_lower
    )

    if threshold_match:
        params["threshold"] = int(threshold_match.group(2))
        params["condition_operator"] = ">"

    threshold_match2 = re.search(
        r"(less than|below)\s*(\d+)",
        prompt_lower
    )

    if threshold_match2:
        params["threshold"] = int(threshold_match2.group(2))
        params["condition_operator"] = "<"

    # --------------------------------
    # OVERTIME DETECTION
    # --------------------------------
    if "overtime" in prompt_lower and len(wage_types) >= 3:

        params["scenario"] = "OVERTIME"
        params["hours_wt"] = wage_types[0]
        params["target_wage_type"] = wage_types[-1]

        sources = wage_types[1:-1]

        if len(sources) == 1:
            params["source_wage_type"] = sources[0]
        elif len(sources) > 1:
            params["source_wage_types"] = sources

    elif "overtime" in prompt_lower:
        params["scenario"] = "OVERTIME"

    return params