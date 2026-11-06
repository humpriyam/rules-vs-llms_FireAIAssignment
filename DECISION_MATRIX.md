# Decision Matrix: Rules vs LLMs vs Hybrid

| Component / Subsystem | Architectural Choice | Justification & Empirical Measurement |
| :--- | :---: | :--- |
| **User Input Parsing & Normalization** (`project_a/parser.py`) | **LLM** | Handles natural language, Hinglish syntax (*"Mera gross 12L hai aur rent 20k per month Bangalore mein"*), and entity extraction with schema validation. Successfully detects missing information (e.g. loan without interest) and triggers clarifying questions rather than guessing. |
| **Tax Calculation Core (Slabs, Deductions, Cess)** (`project_a/impl_rules.py`) | **Rule Engine** | **100.0% rupee-exact accuracy** (215/215 tests pass) vs **34.5%** for LLM. Execution latency is **0.02 ms** vs **2,200 ms** (100,000x faster). Runtime cost is **$0.00** vs **$0.396 / 1k requests**. Zero risk of arithmetic drift. |
| **Statute Update Pipeline** (`project_a/impl_llm_compiled.py`) | **Hybrid (LLM Compiler + Human-in-the-loop)** | LLM drafts structured JSON rule ASTs from raw gazette text in **3.5 seconds**, cutting schema development time by 80%. Human tax-engineer review eliminates silent hallucination errors before production deployment. |
| **Auditability & Traceability** | **Rule Engine** | Every line item in the calculation trace is deterministically tied to statutory clauses (`Section 16(ia)`, `Section 10(13A)`, `Section 87A`, `Section 288A`, `Section 288B`). LLMs at runtime invent generic labels like *"Calculation"* or omit subsection numbers. |
