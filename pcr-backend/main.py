from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.classifier import classify
from engine.extractor import extract_params
from engine.builder import build_pcr
from engine.validator import validate

print("THIS IS THE ACTIVE MAIN.PY")

app = FastAPI()

# Open CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Prompt(BaseModel):
    prompt: str


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/generate")
def generate(data: Prompt):
    intent, confidence = classify(data.prompt)

    # -----------------------------
    # Confidence Guardrail
    # -----------------------------
    if confidence < 0.60:
        return {
            "ok": False,
            "error": "Low confidence prediction",
            "confidence": confidence
        }

    params = extract_params(data.prompt, intent)

    # -----------------------------
    # Complex Overtime Validation
    # -----------------------------
    if params.get("operation") == "OVERTIME_COMPLEX":
        if (
            "wage_types" not in params
            or len(params["wage_types"]) < 3
            or "percent" not in params
            or "threshold" not in params
        ):
            return {
                "ok": False,
                "error": "Incomplete complex overtime description",
                "confidence": confidence
            }

    # -----------------------------
    # Simple Percent Increase
    # -----------------------------
    elif intent == "PERCENT_INCREASE":
        if "percent" not in params or "wage_types" not in params:
            return {
                "ok": False,
                "error": "Missing percent or wage type",
                "confidence": confidence
            }

    # -----------------------------
    # Percent Decrease
    # -----------------------------
    elif intent == "PERCENT_DECREASE":
        if "percent" not in params or "wage_types" not in params:
            return {
                "ok": False,
                "error": "Missing percent or wage type",
                "confidence": confidence
            }

    # -----------------------------
    # Multiplier
    # -----------------------------
    elif intent == "PERCENT_MULTIPLIER":
        if "multiplier" not in params or "wage_types" not in params:
            return {
                "ok": False,
                "error": "Missing multiplier or wage type",
                "confidence": confidence
            }

    # -----------------------------
    # Build PCR
    # -----------------------------
    pcr = build_pcr(intent, params)

    # Validate structure
    validate(pcr)

    return {
        "ok": True,
        "intent": intent,
        "confidence": confidence,
        "pcr": "\n".join(pcr)
    }