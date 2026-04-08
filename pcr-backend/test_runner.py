import requests

TEST_CASES = [
    {
        "input": "Add 500 to wage type 1000 and store in 2000",
        "expected": [
            "AMT= 1000",
            "AMT+ 500",
            "ADDWT 2000"
        ]
    },
    {
        "input": "Calculate 10% of 1000 and store in 2000",
        "expected": [
            "AMT= 1000",
            "AMT* 10",
            "AMT/100",
            "ADDWT 2000"
        ]
    },
    {
        "input": "If overtime hours 3000 exceed 8 then calculate 150% of 1000 and store in 4000",
        "expected": [
            "NUM= 3000",
            "NUM?8",
            "AMT= 1000",
            "AMT* 150",
            "AMT/100",
            "ADDWT 4000"
        ]
    }
]


def run_tests():
    url = "http://localhost:8000/generate"

    passed = 0

    for i, test in enumerate(TEST_CASES, 1):

        res = requests.post(url, json={"prompt": test["input"]})
        data = res.json()

        if not data.get("ok"):
            print(f"\n❌ Test {i} FAILED (API error)")
            continue

        output = data["pcr"].split("\n")

        if output == test["expected"]:
            print(f"✅ Test {i} PASSED")
            passed += 1
        else:
            print(f"\n❌ Test {i} FAILED")
            print("Input:", test["input"])
            print("Expected:", test["expected"])
            print("Got:", output)

    print(f"\n{passed}/{len(TEST_CASES)} tests passed")


if __name__ == "__main__":
    run_tests()