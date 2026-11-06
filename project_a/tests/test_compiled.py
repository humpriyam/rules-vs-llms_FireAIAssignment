import json
import os
import pytest
from project_a.impl_llm_compiled import compute_tax, load_compiled_rules

R = load_compiled_rules()
PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cases.json")
CASES = json.load(open(PATH, encoding="utf-8"))


@pytest.mark.parametrize("c", CASES, ids=[c["id"] for c in CASES])
def test_compiled_rules_case(c):
    assert compute_tax(c["input"], "old", R)["total_tax"] == c["expected_old"]
    assert compute_tax(c["input"], "new", R)["total_tax"] == c["expected_new"]

