"""Hand-verified cases. Expected values were computed by hand, not by the code."""
import pytest
from project_a.impl_rules import compute_tax, load_rules

R = load_rules()

CASES = [
    # (name, input, regime, expected_total_tax)

    # Gross 12L - 50k std - 1.5L 80C = 10L taxable.
    # Tax = 12,500 + 1,00,000 = 1,12,500; cess 4,500 -> 1,17,000
    ("old_80c_only", {"gross_salary": 1200000, "sec_80c": 150000}, "old", 117000),

    # Gross 15L - 50k - 1.5L - 50k - 25k - 2L = 10,25,000 taxable.
    # Tax = 12,500 + 1,00,000 + 30% of 25,000 (7,500) = 1,20,000; cess 4,800 -> 1,24,800
    ("old_all_deductions",
     {"gross_salary": 1500000, "sec_80c": 150000, "sec_80ccd_1b": 50000,
      "sec_80d_self": 25000, "home_loan_interest": 200000}, "old", 124800),

    # Age 65, gross 8L - 50k = 7,50,000 taxable (senior slabs).
    # Tax = 5% of 2L (10,000) + 20% of 2.5L (50,000) = 60,000; cess 2,400 -> 62,400
    ("old_senior_65", {"gross_salary": 800000, "age": 65}, "old", 62400),

    # HRA: basic 6L, HRA 3L, rent 3L, metro.
    # (a) 3,00,000 (b) 3,00,000 - 60,000 = 2,40,000 (c) 50% of 6L = 3,00,000 -> exemption 2,40,000
    # Taxable = 12L - 50k - 2.4L = 9,10,000.
    # Tax = 12,500 + 20% of 4,10,000 (82,000) = 94,500; cess 3,780 -> 98,280
    ("old_hra_metro",
     {"gross_salary": 1200000, "basic": 600000, "hra_received": 300000,
      "rent_paid": 300000, "metro": True}, "old", 98280),

    # Old regime has no marginal relief: taxable 5,10,000 loses the rebate completely.
    # Tax = 12,500 + 20% of 10,000 (2,000) = 14,500; cess 580 -> 15,080
    ("old_87a_cliff", {"gross_salary": 560000}, "old", 15080),

    # New regime, taxable exactly 60L (gross 60,75,000).
    # Tax = 20,000 + 30,000 + 30,000 + 60,000 + 30% of 45L (13,50,000) = 14,90,000
    # Surcharge 10% = 1,49,000 (no marginal relief needed); cess 4% of 16,39,000 = 65,560
    # Total = 17,04,560
    ("new_surcharge_10pct", {"gross_salary": 6075000}, "new", 1704560),

    # New regime, taxable 50,10,000 (gross 50,85,000): marginal relief applies.
    # Tax = 1,40,000 + 30% of 35,10,000 (10,53,000) = 11,93,000
    # Tax at 50L = 11,90,000, so total tax + surcharge is capped at 11,90,000 + 10,000 = 12,00,000
    # Surcharge = 7,000; cess 4% of 12,00,000 = 48,000 -> 12,48,000
    ("new_surcharge_marginal_relief", {"gross_salary": 5085000}, "new", 1248000),

    # New regime 87A: gross 7,75,000 -> taxable 7,00,000 -> full rebate -> 0
    ("new_87a_exact_limit", {"gross_salary": 775000}, "new", 0),
]


@pytest.mark.parametrize("name,inp,regime,expected", CASES, ids=[c[0] for c in CASES])
def test_hand_verified(name, inp, regime, expected):
    assert compute_tax(inp, regime, R)["total_tax"] == expected