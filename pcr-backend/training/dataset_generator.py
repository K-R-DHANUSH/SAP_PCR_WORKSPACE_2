import random
import csv

increase_templates = [
    "Calculate overtime at {p}% for wage type {wt}",
    "Apply {p}% premium to wage type {wt}",
    "Increase wage type {wt} by {p}%",
    "Make wage type {wt} {p} percent",
    "Set wage type {wt} to {p}% rate"
]

decrease_templates = [
    "Decrease wage type {wt} by {p}%",
    "Reduce wage type {wt} to {p}%",
    "Lower wage type {wt} by {p} percent",
    "Apply {p}% rate to wage type {wt}",
    "Set wage type {wt} to {p}%"
]

multiplier_templates = [
    "Multiply wage type {wt} by {m}",
    "Scale wage type {wt} by {m}",
    "Apply {m}x to wage type {wt}",
    "Double wage type {wt}",
    "Triple wage type {wt}"
]

def generate_dataset(filename="dataset.csv", samples=300):
    rows = [("prompt", "intent")]

    for _ in range(samples):
        wt = str(random.randint(1000, 9999))
        percent = random.choice([110, 120, 125, 130, 150, 175, 200])
        multiplier = random.choice([2, 3, 4, 1.5])

        t = random.choice(increase_templates)
        rows.append((t.format(p=percent, wt=wt), "PERCENT_INCREASE"))

        t = random.choice(decrease_templates)
        rows.append((t.format(p=random.choice([70, 75, 80, 85, 90]), wt=wt), "PERCENT_DECREASE"))

        t = random.choice(multiplier_templates)
        rows.append((t.format(m=multiplier, wt=wt), "PERCENT_MULTIPLIER"))

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

if __name__ == "__main__":
    generate_dataset()