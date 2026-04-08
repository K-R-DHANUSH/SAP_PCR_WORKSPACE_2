from dotenv import load_dotenv
import os
import json
import requests

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.classifier import classify
from engine.extractor import extract_params
from engine.builder import build_pcr
from engine.validator import validate

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")


# ----------------------------------------
# FastAPI setup
# ----------------------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------
# Request schema
# ----------------------------------------

class Prompt(BaseModel):
    prompt: str


# ----------------------------------------
# LLM config
# ----------------------------------------

SYSTEM_PROMPT = """
Extract payroll parameters as JSON only.
"""


def llm_extract(prompt: str):

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )

    return r.json()["choices"][0]["message"]["content"]


# ----------------------------------------
# Root endpoint
# ----------------------------------------

@app.get("/")
def root():
    return {"status": "ok"}


# ----------------------------------------
# PCR generation endpoint
# ----------------------------------------

@app.post("/generate")
def generate(data: Prompt):

    try:

        prompt = data.prompt

        # 1. Classify
        intent, confidence = classify(prompt)

        # ----------------------------------------
        # FIX WRONG DECREASE DETECTION
        # ----------------------------------------
        prompt_lower = prompt.lower()

        if ("percent" in prompt_lower or "%" in prompt_lower):
            if not any(word in prompt_lower for word in ["decrease", "reduce", "deduct", "minus"]):
                intent = "PERCENT_INCREASE"

        # 2. Extract params
        params = extract_params(prompt, intent)

        # 3. LLM fallback (safe merge)
        if confidence < 0.6 or len(params) < 2:
            try:
                parsed = json.loads(llm_extract(prompt))

                for k, v in parsed.items():
                    if k not in params:
                        params[k] = v

            except:
                pass

        # 4. Build PCR
        pcr = build_pcr(intent, params)

        # 5. Validate
        validate(pcr)

        return {
            "ok": True,
            "intent": intent,
            "confidence": confidence,
            "params": params,
            "pcr": "\n".join(pcr)
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }