"""
SAP PCR Dataset Generator — Full Scenario Coverage
Generates labelled training data for the intent classifier.

Intents:
  OVERTIME, RATE_HOURS, COPY_WT, PERCENT_INCREASE, PERCENT_DECREASE,
  PERCENT_MULTI, FIXED_ADD, FIXED_SUB, ABSENCE, ALLOWANCE,
  TAX_DEDUCTION, RESET_SUPPRESS, ACCUMULATE, THRESHOLD
"""

import random
import csv

# ─────────────────────────────────────────────────────────────
#  TEMPLATE LIBRARY
# ─────────────────────────────────────────────────────────────

TEMPLATES = {

    "OVERTIME": [
        "Calculate overtime at {p}% for hours above {h} in wage type {wt}",
        "Pay overtime premium of {p}% when hours in {wt} exceed {h}, result in {wt2}",
        "If hours in wage type {wt} are greater than {h}, pay {p}% of base {wt2} into {wt3}",
        "Overtime pay at {p}% for anything over {h} hours from WT {wt}",
        "Apply {p}% overtime rate when {wt} exceeds {h} hours, store in {wt2}",
        "Calculate overtime premium for hours above {h} from wage type {wt} at {p}%",
        "Overtime calculation: hours in {wt} above {h} threshold, {p}% premium, output to {wt2}",
        "Pay {p}% for overtime hours when employee exceeds {h}h, wage type {wt}",
        "150% overtime for any hours above planned working time in {wt}, store result in {wt2}",
        "Double pay for hours exceeding {h} in {wt}, output to {wt2}",
    ],

    "RATE_HOURS": [
        "Multiply rate from wage type {wt} by hours from {wt2}, store result in {wt3}",
        "Calculate pay using rate in {wt} and hours worked in {wt2}, output to {wt3}",
        "Rate from {wt} times hours from {wt2} gives result in {wt3}",
        "Compute earnings: hourly rate {wt} multiplied by hours {wt2}, store in {wt3}",
        "Pay = rate {wt} × hours {wt2}, output wage type {wt3}",
        "Multiply hourly rate in {wt} by actual hours in {wt2} into {wt3}",
        "Calculate gross pay from rate in WT {wt} and time in WT {wt2}, result in WT {wt3}",
        "RTE from {wt} multiplied by NUM from {wt2}, ADDWT {wt3}",
    ],

    "COPY_WT": [
        "Copy wage type {wt} to {wt2}",
        "Transfer amount from wage type {wt} into {wt2}",
        "Move result of {wt} to wage type {wt2}",
        "Replicate wage type {wt} as {wt2}",
        "Mirror wage type {wt} into {wt2}",
        "Pass wage type {wt} directly to {wt2} without changes",
        "Carry forward {wt} into {wt2}",
        "Same value as {wt}, store in {wt2}",
        "Copy base salary from {wt} to output wage type {wt2}",
        "Take amount in {wt} and place it in {wt2} unchanged",
    ],

    "PERCENT_INCREASE": [
        "Calculate overtime at {p}% for wage type {wt}",
        "Apply {p}% premium to wage type {wt}",
        "Increase wage type {wt} by {p}%, store in {wt2}",
        "Make wage type {wt} {p} percent",
        "Set wage type {wt} to {p}% rate",
        "Add {p}% surcharge on top of wage type {wt}, result in {wt2}",
        "Increase {wt} by {p} percent and store in {wt2}",
        "Apply night shift premium of {p}% to {wt}",
        "Uplift wage type {wt} by {p}%, output to {wt2}",
        "Weekend allowance at {p}% of wage type {wt}, store in {wt2}",
        "{p}% holiday premium on wage type {wt} into {wt2}",
        "Shift differential of {p}% applied to {wt}",
    ],

    "PERCENT_DECREASE": [
        "Decrease wage type {wt} by {p}%",
        "Reduce wage type {wt} to {p}%",
        "Lower wage type {wt} by {p} percent",
        "Apply {p}% reduction to wage type {wt}, store in {wt2}",
        "Take {p}% of wage type {wt} as partial payment",
        "Pay only {p}% of wage type {wt} due to partial month",
        "Proportional pay at {p}% of {wt}",
        "Apply {p}% factor to reduce wage type {wt}",
    ],

    "PERCENT_MULTI": [
        "Multiply wage type {wt} by {m}",
        "Scale wage type {wt} by {m}",
        "Apply {m}x to wage type {wt}",
        "Double wage type {wt}",
        "Triple wage type {wt}",
        "Multiply {wt} by factor {m} into {wt2}",
        "Two times wage type {wt}, output to {wt2}",
        "Scale {wt} by {m} and store in {wt2}",
    ],

    "FIXED_ADD": [
        "Add fixed amount {n} to wage type {wt}, store in {wt2}",
        "Add {n} to the amount in {wt}",
        "Increase {wt} by a fixed {n} units",
        "Add constant {n} to wage type {wt} and output to {wt2}",
        "Plus {n} on top of wage type {wt}",
        "Add allowance of {n} to {wt}",
        "Supplement wage type {wt} with fixed addition of {n}",
    ],

    "FIXED_SUB": [
        "Subtract {n} from wage type {wt}",
        "Deduct fixed amount {n} from {wt}, store in {wt2}",
        "Reduce {wt} by {n}",
        "Remove {n} from wage type {wt}",
        "Minus {n} from wage type {wt} output to {wt2}",
        "Deduct fixed penalty of {n} from {wt}",
    ],

    "ABSENCE": [
        "Deduct absence hours from pay in wage type {wt}",
        "Calculate absence deduction for wage type {wt} based on hours in {wt2}",
        "Unpaid leave deduction: divide {wt} by planned hours {wt2}, multiply by absent hours {wt3}",
        "Reduce {wt} proportionally for {p}% absence",
        "Apply absence factor to wage type {wt}, store deduction in {wt2}",
        "Pro-rate wage type {wt} for partial month worked, result in {wt2}",
        "Calculate unpaid absence deduction from base pay {wt} using hours {wt2}",
        "Hours absent in {wt}, deduct proportional amount from base {wt2}, store in {wt3}",
    ],

    "ALLOWANCE": [
        "Add housing allowance from wage type {wt} to {wt2}",
        "Transport allowance wage type {wt}, output to {wt2}",
        "Meal allowance of {p}% of base pay {wt}, store in {wt2}",
        "Add fixed bonus in {wt} to result {wt2}",
        "Night shift allowance {p}% of {wt} into {wt2}",
        "Add supplement wage type {wt} to pay",
        "Child allowance in {wt}, output to {wt2}",
        "Special allowance: take {wt}, apply {p}% factor, store in {wt2}",
    ],

    "TAX_DEDUCTION": [
        "Calculate {p}% income tax on gross pay wage type {wt}, store in {wt2}",
        "Withhold {p}% tax from wage type {wt}",
        "Deduct {p}% pension contribution from {wt} into {wt2}",
        "Social insurance deduction of {p}% on {wt}",
        "Calculate {p}% provident fund contribution on {wt}, output to {wt2}",
        "Health insurance contribution: {p}% of {wt} stored in {wt2}",
        "Apply {p}% PAYE deduction to gross pay {wt}",
        "Employee contribution {p}% on base salary {wt} into WT {wt2}",
        "Calculate tax amount at {p}% from wage type {wt}",
        "Deduct {p}% as national insurance from {wt} into {wt2}",
    ],

    "RESET_SUPPRESS": [
        "Zero out wage type {wt}",
        "Suppress output of wage type {wt}",
        "Clear all registers after processing {wt}",
        "Nullify wage type {wt} in output",
        "Do not output wage type {wt}",
        "Reset wage type {wt} to zero and suppress",
        "Eliminate wage type {wt} from results",
        "Zero the amount in wage type {wt}",
    ],

    "ACCUMULATE": [
        "Sum wage types {wt}, {wt2} and {wt3} into {wt4}",
        "Add together {wt} and {wt2} and store in {wt3}",
        "Combine wage types {wt} and {wt2} into result {wt3}",
        "Accumulate {wt}, {wt2} and {wt3} into total {wt4}",
        "Total of wage types {wt} plus {wt2} plus {wt3}, output to {wt4}",
        "Aggregate amounts from {wt} and {wt2}, store in {wt3}",
        "Merge wage types {wt} and {wt2} into {wt3}",
    ],

    "THRESHOLD": [
        "If amount in {wt} exceeds {h}, apply {p}% and store in {wt2}",
        "Only process if wage type {wt} is greater than {h}",
        "When {wt} is above {h}, compute {p}% and output to {wt2}",
        "Branch when NUM in {wt} exceeds {h} hours",
        "Conditional: if {wt} > {h} then apply premium {p}% into {wt2}",
        "Process {wt2} only when {wt} amount is above {h}",
        "If hours from {wt} are less than {h}, suppress output",
        "Threshold check: {wt} must exceed {h} before outputting to {wt2}",
        "Apply {p}% bonus only when base pay {wt} is above {h}",
    ],
}


# ─────────────────────────────────────────────────────────────
#  RANDOM VALUE POOLS
# ─────────────────────────────────────────────────────────────

WAGE_TYPES    = [str(i) for i in range(1000, 9999, 111)]  # spread of 4-digit WTs
PERCENTS_UP   = [110, 115, 120, 125, 130, 140, 150, 175, 200, 225, 250]
PERCENTS_DOWN = [50, 60, 70, 75, 80, 85, 90, 95]
PERCENTS_TAX  = [5, 7, 10, 12, 15, 18, 20, 22, 25, 28, 30]
MULTIPLIERS   = [2, 3, 4]
THRESHOLDS    = [4, 6, 7, 8, 10, 12, 40, 160, 173, 180]
FIXED_AMOUNTS = [100, 200, 250, 500, 750, 1000]


def _wt():
    return random.choice(WAGE_TYPES)

def _wts(n):
    pool = random.sample(WAGE_TYPES, n)
    return pool


def _fill(template: str, intent: str) -> str:
    wts = _wts(4)
    return template.format(
        wt   = wts[0],
        wt2  = wts[1],
        wt3  = wts[2],
        wt4  = wts[3],
        p    = random.choice(PERCENTS_UP   if intent in ("OVERTIME","PERCENT_INCREASE","ALLOWANCE") else
                             PERCENTS_TAX  if intent == "TAX_DEDUCTION" else
                             PERCENTS_DOWN if intent == "PERCENT_DECREASE" else
                             PERCENTS_UP),
        m    = random.choice(MULTIPLIERS),
        h    = random.choice(THRESHOLDS),
        n    = random.choice(FIXED_AMOUNTS),
    )


# ─────────────────────────────────────────────────────────────
#  GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_dataset(filename: str = "dataset.csv", samples_per_intent: int = 80):
    rows = [("prompt", "intent")]

    for intent, templates in TEMPLATES.items():
        count = 0
        while count < samples_per_intent:
            template = random.choice(templates)
            try:
                prompt = _fill(template, intent)
                rows.append((prompt, intent))
                count += 1
            except (KeyError, IndexError):
                continue

    # Shuffle (keep header first)
    header = rows[0]
    data   = rows[1:]
    random.shuffle(data)
    rows = [header] + data

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Generated {len(rows)-1} samples across {len(TEMPLATES)} intents → {filename}")


if __name__ == "__main__":
    generate_dataset()