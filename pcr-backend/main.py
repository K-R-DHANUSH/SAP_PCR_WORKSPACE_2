"""
SAP PCR Workspace Backend — main.py
Generates exact, valid SAP PCR using Groq (llama3-70b) with expert system prompt.
"""

from dotenv import load_dotenv
import os
import re
import json
import requests

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.pcr_prompt import SAP_PCR_SYSTEM_PROMPT, SAP_PCR_CORRECTION_PREFIX
from engine.validator import validate, ValidationError

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in .env")

# ──────────────────────────────────────────────
#  FastAPI setup
# ──────────────────────────────────────────────
app = FastAPI(title="SAP PCR Workspace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "https://k-r-dhanush.github.io"
    ],
    allow_origin_regex=r"https://.*\.github\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
#  Request schema
# ──────────────────────────────────────────────
class GenerateRequest(BaseModel):
    prompt: str
    hint: str | None = None   # optional correction hint from frontend re-validate


# ──────────────────────────────────────────────
#  Groq LLM call
# ──────────────────────────────────────────────
def call_groq(system: str, user: str, temperature: float = 0.05) -> str:
    """
    Call Groq API with llama3-70b-8192.
    Low temperature = deterministic, rules-following output.
    """
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "temperature": temperature,
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


# ──────────────────────────────────────────────
#  PCR post-processing
# ──────────────────────────────────────────────
def clean_pcr_output(raw: str) -> str:
    """
    Strip markdown fences, extra blank lines, and common LLM artifacts.
    Preserves the exact SAP PCR content.
    """
    text = raw.strip()

    # Remove markdown code fences
    text = re.sub(r"```(?:pcr|txt|sap)?\s*", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")

    # Remove lines that are pure LLM commentary (start with NOTE:, Here is, etc.)
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip empty lines at start
        if not stripped and not cleaned:
            continue
        # Skip obvious LLM commentary lines (not PCR)
        if re.match(
            r"^(here is|here'?s|note:|explanation|the pcr|this pcr|output:|result:)",
            stripped,
            re.IGNORECASE,
        ):
            continue
        cleaned.append(line.rstrip())

    # Remove trailing empty lines
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()

    return "\n".join(cleaned)


def enrich_user_prompt(prompt: str, hint: str | None) -> str:
    """
    Build the full user message sent to the LLM.
    Adds context about what the user wants and any correction hints.
    """
    msg = f"""Generate a complete, valid SAP PE02 PCR for the following payroll scenario:

SCENARIO:
{prompt}

REQUIREMENTS:
- Output only the PCR code (no explanation, no markdown, no comments)
- Follow all SAP PCR syntax rules exactly
- Use the exact wage type numbers mentioned in the scenario
- If the scenario mentions a rule ID, use it; otherwise use Z001
- The PCR must be immediately usable in SAP PE02
"""
    if hint:
        msg += f"""
CORRECTION REQUIRED — previous output had these issues:
{hint}

Fix ALL listed issues and output the corrected PCR only.
"""
    return msg


# ──────────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "service": "SAP PCR Workspace API"}


@app.post("/generate")
def generate(data: GenerateRequest):
    try:
        prompt = data.prompt.strip()
        if not prompt:
            return {"ok": False, "error": "Prompt is empty"}

        # ── Pass 1: Generate ──────────────────────────────
        user_msg = enrich_user_prompt(prompt, data.hint)
        raw = call_groq(SAP_PCR_SYSTEM_PROMPT, user_msg, temperature=0.05)
        pcr = clean_pcr_output(raw)

        # ── Pass 2: Validate ──────────────────────────────
        lines = [l for l in pcr.split("\n") if l.strip()]
        issues = validate(lines)

        # ── Pass 3: Auto-correction (if issues found) ─────
        if issues:
            correction_system = SAP_PCR_SYSTEM_PROMPT
            correction_user = (
                SAP_PCR_CORRECTION_PREFIX
                + "\n".join(f"- {i}" for i in issues)
                + f"\n\nORIGINAL SCENARIO:\n{prompt}"
                + f"\n\nFAULTY PCR (fix this):\n{pcr}"
            )
            raw2 = call_groq(correction_system, correction_user, temperature=0.02)
            pcr2 = clean_pcr_output(raw2)
            lines2 = [l for l in pcr2.split("\n") if l.strip()]
            issues2 = validate(lines2)

            # Use corrected version (even if still has minor issues, it's better)
            pcr = pcr2
            issues = issues2

        return {
            "ok": True,
            "pcr": pcr,
            "warnings": issues,   # frontend can show these as hints
        }

    except requests.exceptions.HTTPError as e:
        return {"ok": False, "error": f"Groq API error: {e.response.status_code} — {e.response.text[:200]}"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Request to Groq timed out. Try again."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/validate")
def validate_pcr(data: dict):
    """
    Standalone validation endpoint — frontend can call this
    to check user-typed PCR before saving.
    """
    try:
        pcr_text = data.get("pcr", "")
        lines = [l for l in pcr_text.split("\n") if l.strip()]
        issues = validate(lines)
        return {"ok": True, "valid": len(issues) == 0, "issues": issues}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/ops")
def get_ops():
    """
    Returns operation metadata for the frontend autocomplete/oplib panel.
    """
    ops = [
        # AMT
        {"code": "AMT=",    "group": "amt",    "description": "Load AMT register from wage type or *"},
        {"code": "AMT+",    "group": "amt",    "description": "Add wage type amount to AMT"},
        {"code": "AMT-",    "group": "amt",    "description": "Subtract wage type amount from AMT"},
        {"code": "AMT*",    "group": "amt",    "description": "Multiply AMT by scalar value"},
        {"code": "AMT/",    "group": "amt",    "description": "Divide AMT by scalar value"},
        # NUM
        {"code": "NUM=",    "group": "num",    "description": "Load NUM register from wage type or *"},
        {"code": "NUM+",    "group": "num",    "description": "Add wage type number to NUM"},
        {"code": "NUM-",    "group": "num",    "description": "Subtract from NUM"},
        {"code": "NUM*",    "group": "num",    "description": "Multiply NUM by scalar"},
        {"code": "NUM/",    "group": "num",    "description": "Divide NUM by scalar"},
        # RTE
        {"code": "RTE=",    "group": "rte",    "description": "Load RTE register from wage type or *"},
        {"code": "RTE*",    "group": "rte",    "description": "Multiply RTE by scalar"},
        {"code": "RTE/",    "group": "rte",    "description": "Divide RTE by scalar"},
        # Cross-register
        {"code": "MULTI",   "group": "multi",  "description": "Multiply AMT by RTE or NUM register"},
        {"code": "DIVI",    "group": "multi",  "description": "Divide AMT by RTE or NUM register"},
        # Condition checks
        {"code": "AMT?>",   "group": "cond",   "description": "Branch if AMT > value"},
        {"code": "AMT?<",   "group": "cond",   "description": "Branch if AMT < value"},
        {"code": "AMT?=",   "group": "cond",   "description": "Branch if AMT = value"},
        {"code": "NUM?>",   "group": "cond",   "description": "Branch if NUM > value"},
        {"code": "NUM?<",   "group": "cond",   "description": "Branch if NUM < value"},
        {"code": "NUM?=",   "group": "cond",   "description": "Branch if NUM = value"},
        {"code": "RTE?>",   "group": "cond",   "description": "Branch if RTE > value"},
        # Transfer
        {"code": "ADDWT",   "group": "output", "description": "Add AMT/NUM/RTE to output wage type"},
        {"code": "SUBWT",   "group": "output", "description": "Subtract from output wage type"},
        # Control
        {"code": "OUTWP",   "group": "ctrl",   "description": "Output wage type and return to caller"},
        {"code": "OUTWPP",  "group": "ctrl",   "description": "Output wage type and return to parent"},
        {"code": "ZERO=",   "group": "ctrl",   "description": "Zero all registers"},
        {"code": "SUPPRESS","group": "ctrl",   "description": "Suppress output of current wage type"},
    ]
    return {"ok": True, "ops": ops}