"""Values taken from the Income Tax Department's official calculator (AY 2025-26,
salaried, below 60). Input to the calculator was TAXABLE income, so we add the
standard deduction back to get the gross salary our engine expects."""
import pytest
from project_a.impl_rules import compute_tax, load_rules

R = load_rules()
STD = {"new": 75000, "old": 50000}

# (taxable_income, regime, official_tax)
OFFICIAL = [
    (500000, "new", 0), (510000, "new", 0), (700000, "new", 0),
    (1000000, "new", 52000), (1200000, "new", 83200), (1275000, "new", 98800),
    (5010000, "new", 1248000), (6000000, "new", 1704560),
    (500000, "old", 0), (510000, "old", 15080), (700000, "old", 54600),
    (710000, "old", 56680), (1000000, "old", 117000), (1200000, "old", 179400),
    (1275000, "old", 202800), (5010000, "old", 1375400), (6000000, "old", 1844700),
]


@pytest.mark.parametrize("taxable,regime,official", OFFICIAL)
def test_matches_official_calculator(taxable, regime, official):
    gross = taxable + STD[regime]
    assert compute_tax({"gross_salary": gross}, regime, R)["total_tax"] == official


def test_documented_disagreement_87a_marginal_relief():
    """Official calculator shows 21,840 for taxable 7,10,000 (new regime), i.e. no
    87A marginal relief. The statute (Section 87A with marginal relief) gives
    10,400, which is what our engine follows. Recorded as a known disagreement."""
    OFFICIAL_CALCULATOR_VALUE = 21840
    gross = 710000 + STD["new"]
    engine = compute_tax({"gross_salary": gross}, "new", R)["total_tax"]
    assert engine == 10400
    assert engine != OFFICIAL_CALCULATOR_VALUE

def test_documented_disagreement_rounding_and_cliff():
    """Calculator vs engine at the edges (AY 2025-26, salaried, below 60).
    Calculator: new regime 7,00,001 -> 20,800 (no rebate, no marginal relief);
                old regime 6,99,999 -> 54,598 (taxable apparently rounded down to 6,99,990).
    Engine follows Section 288A (nearest Rs 10) and Section 87A as understood:
                new regime 7,00,001 -> 0; old regime 6,99,999 -> 54,600."""
    new_edge = compute_tax({"gross_salary": 700001 + STD["new"]}, "new", R)["total_tax"]
    old_edge = compute_tax({"gross_salary": 699999 + STD["old"]}, "old", R)["total_tax"]
    assert new_edge == 0 and new_edge != 20800
    assert old_edge == 54600 and old_edge != 54598