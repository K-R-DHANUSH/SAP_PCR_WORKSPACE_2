"""
SAP PCR Workspace Backend — main.py
Hybrid accuracy: Rule engine generates structural hints → LLM uses them for precise output.
"""

from dotenv import load_dotenv
import os
import re
import time
import requests

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.pcr_prompt import SAP_PCR_SYSTEM_PROMPT, SAP_PCR_CORRECTION_PREFIX
from engine.validator import validate

# Try to import rule engine components — fail gracefully if model not loaded
try:
    from engine.classifier import classify
    from engine.extractor import extract_params
    from engine.builder import build_pcr
    RULE_ENGINE_AVAILABLE = True
except Exception as _e:
    RULE_ENGINE_AVAILABLE = False
    print(f"[WARN] Rule engine unavailable: {_e}")

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in .env")

# ─────────────────────────────────────────────────────────────
#  FastAPI
# ─────────────────────────────────────────────────────────────
app = FastAPI(title="SAP PCR Workspace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    prompt: str
    hint: str | None = None


# ─────────────────────────────────────────────────────────────
#  Groq models
# ─────────────────────────────────────────────────────────────
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
]


def call_groq(system: str, user: str, temperature: float = 0.05) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error = None
    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "temperature": temperature,
            "max_tokens": 512,
        }
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            if r.status_code == 429:
                time.sleep(1)
                last_error = f"Rate limit on {model}"
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as e:
            if r.status_code == 400 and "decommissioned" in r.text:
                last_error = f"Model {model} decommissioned"
                continue
            raise

    raise RuntimeError(f"All Groq models failed. Last error: {last_error}")


# ─────────────────────────────────────────────────────────────
#  PCR post-processing
# ─────────────────────────────────────────────────────────────
def clean_pcr(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"```(?:pcr|txt|sap|plaintext)?\s*", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")

    lines = text.split("\n")
    cleaned = []
    skip_prefixes = (
        "here is", "here's", "note:", "explanation:", "the pcr",
        "this pcr", "output:", "result:", "below is", "---"
    )
    for line in lines:
        stripped = line.strip()
        if not stripped and not cleaned:
            continue
        if any(stripped.lower().startswith(p) for p in skip_prefixes):
            continue
        cleaned.append(line.rstrip())

    while cleaned and not cleaned[-1].strip():
        cleaned.pop()

    return "\n".join(cleaned)


def fix_common_issues(pcr: str) -> str:
    lines = pcr.split("\n")
    fixed = []

    for line in lines:
        stripped = line.strip()

        if re.search(r"\bTHEN\b", stripped, re.IGNORECASE):
            stripped = re.sub(r"\s*\bTHEN\b\s*", " ", stripped, flags=re.IGNORECASE).strip()

        stripped = re.sub(r"^(AMT|NUM|RTE)([=+\-*/])(\S)", r"\1\2 \3", stripped)

        dec_pct = re.match(r"^(AMT|NUM|RTE)\*\s+(0\.\d+|\d+\.\d+)$", stripped)
        if dec_pct:
            reg = dec_pct.group(1)
            val = float(dec_pct.group(2))
            if val < 10:
                int_val = int(round(val * 100))
                fixed.append(f"{reg}* {int_val}")
                fixed.append(f"{reg}/ 100")
                continue

        if re.match(r"^IF\b", stripped, re.IGNORECASE):
            continue

        if re.match(r"^(ELSE|ENDIF)\b", stripped, re.IGNORECASE):
            continue

        fixed.append(line[:len(line) - len(line.lstrip())] + stripped if stripped else line)

    return "\n".join(fixed)


# ─────────────────────────────────────────────────────────────
#  Rule engine hint generation
# ─────────────────────────────────────────────────────────────
def generate_rule_engine_hint(prompt: str) -> str:
    """
    Run the classifier + extractor + builder pipeline to produce
    a structural hint for the LLM. Returns empty string on any failure.
    """
    if not RULE_ENGINE_AVAILABLE:
        return ""
    try:
        intent, confidence = classify(prompt)
        params = extract_params(prompt, intent)
        lines  = build_pcr(intent, params)
        scenario = params.get("scenario", "GENERIC")
        wts = params.get("wage_types", [])

        hint_parts = [
            f"Detected intent: {intent} (confidence: {confidence:.2f})",
            f"Scenario: {scenario}",
            f"Wage types found: {wts}",
            "",
            "Structural pattern from rule engine (use as reference):",
        ]
        hint_parts.extend(f"  {line}" for line in lines)
        return "\n".join(hint_parts)
    except Exception as e:
        return f"[Rule engine error: {e}]"


def build_user_prompt(prompt: str, hint: str | None, rule_hint: str) -> str:
    """Build the enriched user message for the LLM."""
    msg = f"""Generate a complete, valid SAP PE02 PCR for this payroll scenario:

SCENARIO:
{prompt}

CRITICAL INSTRUCTIONS:
- Use the EXACT wage type numbers from the scenario — do not invent new ones
- For percentages: use TWO integer lines e.g. AMT* 150 then AMT/ 100 (NEVER decimals like AMT* 1.5)
- For conditional hours: use NUM?> N style (NEVER IF/THEN/ELSE/ENDIF)
- For leave encashment/gratuity: multiply BEFORE dividing to avoid integer truncation
- For rate × hours: use RTE= <rate_wt>, NUM= <hours_wt>, MULTI NUM pattern
- Output ONLY the PCR code — no explanation, no markdown, no fences
"""

    if rule_hint:
        msg += f"""
STRUCTURAL HINT FROM RULE ENGINE:
{rule_hint}

Follow this structural pattern closely. Use the exact wage types from the scenario above.
"""

    if hint:
        msg += f"""
ERRORS FROM PREVIOUS ATTEMPT — FIX ALL OF THESE:
{hint}
"""
    return msg


# ─────────────────────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "SAP PCR Workspace API v4",
        "rule_engine": RULE_ENGINE_AVAILABLE,
    }


@app.post("/generate")
def generate(data: GenerateRequest):
    try:
        prompt = data.prompt.strip()
        if not prompt:
            return {"ok": False, "error": "Prompt is empty"}

        # ── Rule engine structural hint ───────────────────────
        rule_hint = generate_rule_engine_hint(prompt)

        # ── Pass 1: Generate ──────────────────────────────────
        user_msg = build_user_prompt(prompt, data.hint, rule_hint)
        raw = call_groq(SAP_PCR_SYSTEM_PROMPT, user_msg, temperature=0.05)
        pcr = clean_pcr(raw)
        pcr = fix_common_issues(pcr)

        # ── Pass 2: Validate ──────────────────────────────────
        lines  = [l for l in pcr.split("\n") if l.strip()]
        issues = validate(lines)

        # ── Pass 3: Auto-correction if needed ────────────────
        if issues:
            correction_user = (
                SAP_PCR_CORRECTION_PREFIX
                + "\n".join(f"- {i}" for i in issues)
                + f"\n\nORIGINAL SCENARIO:\n{prompt}"
                + (f"\n\nRULE ENGINE HINT:\n{rule_hint}" if rule_hint else "")
                + f"\n\nFAULTY PCR (fix this):\n{pcr}"
            )
            raw2   = call_groq(SAP_PCR_SYSTEM_PROMPT, correction_user, temperature=0.02)
            pcr2   = clean_pcr(raw2)
            pcr2   = fix_common_issues(pcr2)
            lines2 = [l for l in pcr2.split("\n") if l.strip()]
            issues2 = validate(lines2)
            pcr    = pcr2
            issues = issues2

        return {
            "ok":       True,
            "pcr":      pcr,
            "warnings": issues,
            "intent":   _safe_intent(prompt),
        }

    except RuntimeError as e:
        return {"ok": False, "error": str(e)}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Groq API timed out. Please try again."}
    except requests.exceptions.HTTPError as e:
        return {"ok": False, "error": f"Groq API error: {e.response.status_code} — {e.response.text[:300]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _safe_intent(prompt: str) -> str:
    if not RULE_ENGINE_AVAILABLE:
        return "UNKNOWN"
    try:
        intent, _ = classify(prompt)
        return intent
    except Exception:
        return "UNKNOWN"


@app.post("/validate")
def validate_endpoint(data: dict):
    try:
        pcr_text = data.get("pcr", "")
        lines    = [l for l in pcr_text.split("\n") if l.strip()]
        issues   = validate(lines)
        return {"ok": True, "valid": len(issues) == 0, "issues": issues}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/classify")
def classify_endpoint(data: dict):
    """Classify a prompt and return intent + extracted params."""
    if not RULE_ENGINE_AVAILABLE:
        return {"ok": False, "error": "Rule engine not available"}
    try:
        prompt = data.get("prompt", "").strip()
        intent, confidence = classify(prompt)
        params = extract_params(prompt, intent)
        lines  = build_pcr(intent, params)
        return {
            "ok":         True,
            "intent":     intent,
            "confidence": confidence,
            "params":     params,
            "rule_pcr":   "\n".join(lines),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/ops")
def get_ops():
    """Returns all valid SAP PCR operations for frontend autocomplete."""
    ops = [
        {"code": "AMT=",    "group": "amt",    "description": "Load amount from wage type into AMT"},
        {"code": "AMT+",    "group": "amt",    "description": "Add wage type amount to AMT"},
        {"code": "AMT-",    "group": "amt",    "description": "Subtract wage type amount from AMT"},
        {"code": "AMT*",    "group": "amt",    "description": "Multiply AMT by integer scalar"},
        {"code": "AMT/",    "group": "amt",    "description": "Divide AMT by integer scalar"},
        {"code": "AMT?>",   "group": "cond",   "description": "Continue only if AMT > value"},
        {"code": "AMT?<",   "group": "cond",   "description": "Continue only if AMT < value"},
        {"code": "AMT?=",   "group": "cond",   "description": "Continue only if AMT = value"},
        {"code": "AMT?>=",  "group": "cond",   "description": "Continue only if AMT >= value"},
        {"code": "AMT?<=",  "group": "cond",   "description": "Continue only if AMT <= value"},
        {"code": "NUM=",    "group": "num",    "description": "Load number/hours from wage type into NUM"},
        {"code": "NUM+",    "group": "num",    "description": "Add wage type number to NUM"},
        {"code": "NUM-",    "group": "num",    "description": "Subtract from NUM"},
        {"code": "NUM*",    "group": "num",    "description": "Multiply NUM by scalar"},
        {"code": "NUM/",    "group": "num",    "description": "Divide NUM by scalar"},
        {"code": "NUM?>",   "group": "cond",   "description": "Continue only if NUM > value"},
        {"code": "NUM?<",   "group": "cond",   "description": "Continue only if NUM < value"},
        {"code": "NUM?=",   "group": "cond",   "description": "Continue only if NUM = value"},
        {"code": "NUM?>=",  "group": "cond",   "description": "Continue only if NUM >= value"},
        {"code": "NUM?<=",  "group": "cond",   "description": "Continue only if NUM <= value"},
        {"code": "RTE=",    "group": "rte",    "description": "Load rate from wage type into RTE"},
        {"code": "RTE*",    "group": "rte",    "description": "Multiply RTE by scalar"},
        {"code": "RTE/",    "group": "rte",    "description": "Divide RTE by scalar"},
        {"code": "RTE?>",   "group": "cond",   "description": "Continue only if RTE > value"},
        {"code": "RTE?<",   "group": "cond",   "description": "Continue only if RTE < value"},
        {"code": "MULTI",   "group": "cross",  "description": "Multiply AMT by RTE or NUM register"},
        {"code": "DIVI",    "group": "cross",  "description": "Divide AMT by RTE or NUM register"},
        {"code": "ADDWT",   "group": "output", "description": "Add AMT/NUM/RTE to output wage type"},
        {"code": "SUBWT",   "group": "output", "description": "Subtract from output wage type"},
        {"code": "ELIMI",   "group": "output", "description": "Eliminate wage type from result table"},
        {"code": "OUTWP",   "group": "ctrl",   "description": "Output and return to caller"},
        {"code": "OUTWPP",  "group": "ctrl",   "description": "Output and return two levels up"},
        {"code": "ZERO=",   "group": "ctrl",   "description": "Zero all registers"},
        {"code": "SUPPRESS","group": "ctrl",   "description": "Suppress output of current wage type"},
    ]
    return {"ok": True, "ops": ops}