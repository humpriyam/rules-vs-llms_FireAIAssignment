"""Implementation (b): LLM at query time.

An LLM reads the relevant statutory rule text for each request and computes the answer.
"""
import os
import json
import time
import warnings

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
import google.generativeai as genai
load_dotenv()

DEFAULT_RULE_TEXT_PATH = os.path.join(
    os.path.dirname(__file__), "rules", "rule_text_fy2024_25.txt"
)

# Configure API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"), transport="rest")

# Pricing per million tokens (USD) for Gemini Flash-Lite tier
COST_PER_M_INPUT_TOKENS = 0.075
COST_PER_M_OUTPUT_TOKENS = 0.30


def load_rule_text(path: str = None) -> str:
    path = path or DEFAULT_RULE_TEXT_PATH
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(inp: dict, regime: str, rule_text: str) -> str:
    return f"""You are an income-tax calculation engine for salaried individuals in India.
Read the official statutory rules below carefully:

=== OFFICIAL STATUTORY RULES ===
{rule_text}
=== END RULES ===

Taxpayer input details:
{json.dumps(inp, indent=2)}

Task:
Calculate the exact income tax liability for the taxpayer under the '{regime}' regime.
Follow all statutory rules strictly:
1. Standard deduction (Section 16(ia)).
2. Exemption/deductions applicable (HRA under 10(13A), 80C, 80CCD(1B), 80D, Section 24(b) home loan interest for old regime only).
3. Section 288A: Taxable income must be rounded to the nearest multiple of 10.
4. Calculate tax using the appropriate slab rates for the regime and taxpayer age.
5. Apply Section 87A rebate and marginal relief if applicable.
6. Apply Surcharge and surcharge marginal relief if applicable.
7. Add 4% Health & Education Cess.
8. Section 288B: Round the final total tax to the nearest rupee.

Output valid JSON ONLY with this exact structure:
{{
  "regime": "{regime}",
  "taxable_income": <integer rounded to nearest 10>,
  "total_tax": <integer rounded to nearest rupee>,
  "trace": [
    ["<Description of item>", <amount_change_number>, "<Statutory Clause>"],
    ...
  ]
}}
"""


def compute_tax(
    inp: dict,
    regime: str,
    rule_text_path: str = None,
    model_name: str = None,
    return_meta: bool = False,
) -> dict:
    """
    Computes tax by passing the full statutory text and user profile to an LLM at query time.
    """
    assert regime in ("old", "new"), f"Invalid regime: {regime}"
    rule_text = load_rule_text(rule_text_path)
    prompt = build_prompt(inp, regime, rule_text)

    models_to_try = [
        model_name or os.environ.get("GEMINI_MODEL"),
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-2.5-flash",
    ]

    last_error = None
    t0 = time.perf_counter()

    for m in models_to_try:
        if not m:
            continue
        try:
            model = genai.GenerativeModel(
                model_name=m,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.0,
                },
            )
            response = model.generate_content(prompt)
            latency = time.perf_counter() - t0
            raw_text = response.text.strip()
            data = json.loads(raw_text)

            prompt_tokens = getattr(
                response.usage_metadata, "prompt_token_count", 0
            )
            candidates_tokens = getattr(
                response.usage_metadata, "candidates_token_count", 0
            )
            cost_usd = (prompt_tokens * COST_PER_M_INPUT_TOKENS / 1e6) + (
                candidates_tokens * COST_PER_M_OUTPUT_TOKENS / 1e6
            )

            res = {
                "regime": regime,
                "taxable_income": int(data.get("taxable_income", 0)),
                "total_tax": int(data.get("total_tax", 0)),
                "trace": data.get("trace", []),
            }

            if return_meta:
                res["meta"] = {
                    "latency_sec": latency,
                    "prompt_tokens": prompt_tokens,
                    "candidates_tokens": candidates_tokens,
                    "cost_usd": cost_usd,
                    "model_used": m,
                }
            return res
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All LLM runtime attempts failed: {last_error}")


def compare_regimes(
    inp: dict,
    rule_text_path: str = None,
    model_name: str = None,
    return_meta: bool = False,
) -> dict:
    old_res = compute_tax(
        inp, "old", rule_text_path, model_name, return_meta=return_meta
    )
    new_res = compute_tax(
        inp, "new", rule_text_path, model_name, return_meta=return_meta
    )

    better = "new" if new_res["total_tax"] <= old_res["total_tax"] else "old"
    diff = abs(old_res["total_tax"] - new_res["total_tax"])

    out = {
        "old": old_res,
        "new": new_res,
        "recommended": better,
        "saving": diff,
    }

    if return_meta:
        out["meta"] = {
            "total_latency_sec": old_res["meta"]["latency_sec"]
            + new_res["meta"]["latency_sec"],
            "total_tokens": old_res["meta"]["prompt_tokens"]
            + old_res["meta"]["candidates_tokens"]
            + new_res["meta"]["prompt_tokens"]
            + new_res["meta"]["candidates_tokens"],
            "total_cost_usd": old_res["meta"]["cost_usd"]
            + new_res["meta"]["cost_usd"],
        }
    return out


if __name__ == "__main__":
    test_inp = {
        "gross_salary": 1275000,
        "basic": 600000,
        "hra_received": 240000,
        "rent_paid": 240000,
        "metro": True,
        "sec_80c": 150000,
    }
    print("Testing LLM Runtime on gross 12.75L...")
    result = compare_regimes(test_inp, return_meta=True)
    print(f"Old Tax: {result['old']['total_tax']}")
    print(f"New Tax: {result['new']['total_tax']}")
    print(f"Recommended: {result['recommended']} (saving {result['saving']})")
    print(f"Meta: {result['meta']}")
