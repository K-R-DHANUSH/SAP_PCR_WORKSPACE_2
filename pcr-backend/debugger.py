from ollama_client import ask_llm


def debug_pcr(expected, actual, code):

    prompt = f"""
You are an SAP PCR expert and Python developer.

Expected PCR:
{expected}

Actual PCR:
{actual}

Python code:
{code}

Task:
1. Identify the issue
2. Suggest EXACT code fix (only changed lines)
3. Be precise

Output format:
ISSUE:
FIX:
"""

    return ask_llm(prompt)