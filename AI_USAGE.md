# AI Usage Note

## Tools Used and Purpose
- **Google Antigravity & Gemini API (`gemini-3.1-flash-lite`, `gemini-3.8-flash`)**:
  - Used to build the plain-language parser (`project_a/parser.py`) for entity extraction and ambiguity detection.
  - Used as the query-time evaluation baseline (`project_a/impl_llm_runtime.py`) to benchmark LLM accuracy on statutory calculations.
  - Used for rule compilation experiments (`project_a/impl_llm_compiled.py`) translating raw legal text into structured JSON specifications.
- **Python / pytest / uv**:
  - Test suite orchestration (457 automated test assertions), test case generation, and timing benchmarks.

---

## Where the AI Was Wrong and How We Caught It

### Incident: Silent Arithmetic Hallucination on Income Tax Slabs
During the evaluation of the query-time LLM (`impl_llm_runtime.py`) on a taxpayer with **₹12,75,000 gross salary** under the New Tax Regime (FY 2024-25):
- **Statutory Truth**:
  - Gross: ₹12,75,000
  - Standard Deduction: ₹75,000 → Net Taxable: ₹12,00,000
  - Slabs: 0-3L @ 0% (₹0), 3-7L @ 5% (₹20,000), 7-10L @ 10% (₹30,000), 10-12L @ 15% (₹30,000)
  - Tax before cess: ₹80,000; Cess (4%): ₹3,200
  - **Ground Truth Total Tax**: **₹83,200** (verified against the official Income Tax Department calculator).

- **What the AI Outputted**:
  - In the reasoning `trace`, Gemini correctly computed:
    - `["Slab 3L-7L (5%)", 20000, "S1"]`
    - `["Slab 7L-10L (10%)", 30000, "S1"]`
    - `["Slab 10L-12L (15%)", 30000, "S1"]`
    - `["Tax before Cess", 80000, "Calculation"]`
    - `["Cess (4%)", 3200, "S11"]`
    - `["Total Tax Payable", 83200, "Calculation"]`
  - **HOWEVER**, in the final JSON payload field `"total_tax"`, the model returned:
    ```json
    "total_tax": 93600
    ```
    The model hallucinated an additional ₹10,400 in the final integer field!

- **How We Caught It**:
  - Our automated test suite (`project_a/tests/test_suite.py` and `project_a/tests/oracle.py`) executes an independent, fraction-based ground-truth oracle.
  - The assertion `assert res["total_tax"] == expected` failed immediately.
  - This empirical failure provided decisive proof that LLMs should **never** be entrusted with multi-tier tax arithmetic at runtime, directly justifying our hybrid architecture choice.
