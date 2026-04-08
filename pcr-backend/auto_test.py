import requests
from debugger import debug_pcr

TEST_CASE = {
    "input": "Add 500 to wage type 1000 then calculate 10% and store in 4000",
    "expected": [
        "AMT= 1000",
        "AMT+ 500",
        "AMT* 10",
        "AMT/100",
        "ADDWT 4000"
    ]
}


def run():

    res = requests.post(
        "http://localhost:8000/generate",
        json={"prompt": TEST_CASE["input"]}
    )

    data = res.json()

    actual = data["pcr"].split("\n")

    if actual == TEST_CASE["expected"]:
        print("✅ PASS")
    else:
        print("❌ FAIL")
        print("Expected:", TEST_CASE["expected"])
        print("Actual:", actual)

        with open("engine/builder.py") as f:
            code = f.read()

        fix = debug_pcr(TEST_CASE["expected"], actual, code)

        print("\n🧠 AI DEBUG SUGGESTION:\n")
        print(fix)


if __name__ == "__main__":
    run()