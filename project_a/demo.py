"""Live demo: type plain English, get tax result with full trace."""
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from project_a.parser import parse_user_query
from project_a.impl_rules import compute_tax, load_rules, compare_regimes

RULES = load_rules()

def run(query: str):
    print(f"\nINPUT : {query}")
    print("-" * 60)

    parsed = parse_user_query(query)

    if "clarifying_question" in parsed:
        print(f"SYSTEM: {parsed['clarifying_question']}")
        return

    print("PARSED:")
    print(json.dumps(parsed, indent=2))
    print("-" * 60)

    result = compare_regimes(parsed, RULES)

    for regime in ("old", "new"):
        r = result[regime]
        print(f"\n{regime.upper()} REGIME  →  Tax = ₹{r['total_tax']:,}")
        for label, amt, clause in r["trace"]:
            if amt != 0:
                sign = "+" if amt > 0 else ""
                print(f"  {label:<40} {sign}{amt:>12,}   [{clause}]")

    rec = result["recommended"].upper()
    saving = result["saving"]
    print(f"\nRECOMMENDATION: {rec} regime saves ₹{saving:,}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run(" ".join(sys.argv[1:]))
    else:
        print("Type your query (or press Ctrl+C to exit):")
        while True:
            try:
                q = input("\n> ")
                if q.strip():
                    run(q)
            except KeyboardInterrupt:
                break