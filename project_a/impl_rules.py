"""Implementation (a): hand-coded rules engine.

All numbers are read from the rules JSON. Every line of the result carries a clause.
"""
import json
import os

RULES_PATH = os.path.join(os.path.dirname(__file__), "rules", "fy2024_25.json")


def load_rules(path=RULES_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def round_half_up(x):
    return int(x + 0.5)


def round_10(x):
    """Section 288A: taxable income rounded to nearest multiple of 10 (5 rounds up)."""
    return int((x + 5) // 10 * 10)


def slab_tax(income, slabs):
    tax, prev = 0.0, 0
    for s in slabs:
        upto = s["upto"]
        top = income if upto is None else min(income, upto)
        if top > prev:
            tax += (top - prev) * s["rate"]
        if upto is None or income <= upto:
            break
        prev = upto
    return round(tax, 2)


def surcharge_rate(income, rules, regime):
    rate = 0.0
    for b in rules["surcharge"]["brackets"]:
        if b.get("old_regime_only") and regime != "old":
            continue
        if income > b["above"]:
            rate = b["rate"]
    if regime == "new":
        rate = min(rate, rules["new_regime"]["surcharge_cap_rate"])
    return rate


def hra_exemption(inp, rules):
    h = rules["hra"]
    hra = inp.get("hra_received", 0)
    rent = inp.get("rent_paid", 0)
    if hra <= 0 or rent <= 0:
        return 0
    salary = inp.get("basic", 0) + inp.get("da", 0)
    pct = h["metro_pct"] if inp.get("metro", False) else h["non_metro_pct"]
    a = hra
    b = rent - h["rent_minus_pct_of_salary"] * salary
    c = pct * salary
    return max(0, round(min(a, b, c), 2))


def compute_tax(inp, regime, rules):
    """inp keys (annual rupees): gross_salary, age, basic, da, hra_received, rent_paid,
    metro(bool), sec_80c, sec_80ccd_1b, sec_80d_self, sec_80d_parents,
    parents_senior(bool), home_loan_interest."""
    assert regime in ("old", "new")
    trace = []
    gross = inp["gross_salary"]
    age = inp.get("age", 30)
    trace.append(("Gross salary", gross, "Input"))

    if regime == "new":
        sd = rules["new_regime"]["standard_deduction"]
        slabs = rules["new_regime"]["slabs"]
        rebate_rule = rules["new_regime"]["rebate_87A"]
    else:
        sd = rules["old_regime"]["standard_deduction"]
        key = "80_plus" if age >= 80 else ("60_to_79" if age >= 60 else "below_60")
        slabs = rules["old_regime"]["slabs_by_age"][key]
        rebate_rule = rules["old_regime"]["rebate_87A"]

    std = min(sd["value"], gross)
    trace.append(("Standard deduction", -std, sd["clause"]))
    income = gross - std

    if regime == "old":
        hra_ex = hra_exemption(inp, rules)
        if hra_ex:
            trace.append(("HRA exemption", -hra_ex, rules["hra"]["clause"]))
        income -= hra_ex

        d = rules["deductions_old_regime_only"]
        hp = min(inp.get("home_loan_interest", 0), d["home_loan_interest_self_occupied"]["limit"])
        if hp:
            trace.append(("Home loan interest", -hp, d["home_loan_interest_self_occupied"]["clause"]))
        income -= hp

        c80 = min(inp.get("sec_80c", 0), d["80C"]["limit"])
        nps = min(inp.get("sec_80ccd_1b", 0), d["80CCD_1B"]["limit"])
        self_cap = d["80D"]["self_family"]["senior" if age >= 60 else "normal"]
        par_cap = d["80D"]["parents"]["senior" if inp.get("parents_senior") else "normal"]
        d80_self = min(inp.get("sec_80d_self", 0), self_cap)
        d80_par = min(inp.get("sec_80d_parents", 0), par_cap)
        for label, amt, cl in [("80C", c80, d["80C"]["clause"]),
                               ("80CCD(1B)", nps, d["80CCD_1B"]["clause"]),
                               ("80D self/family", d80_self, d["80D"]["clause"]),
                               ("80D parents", d80_par, d["80D"]["clause"])]:
            if amt:
                trace.append((label, -amt, cl))
            income -= amt

    taxable = round_10(max(0, income))
    trace.append(("Taxable income (rounded to 10)", taxable, "Section 288A"))

    tax = slab_tax(taxable, slabs)
    trace.append(("Tax on slabs", tax, "Slab clause for regime"))

    rebate = 0.0
    if taxable <= rebate_rule["income_limit"]:
        rebate = min(tax, rebate_rule["max_rebate"])
        if rebate:
            trace.append(("Rebate 87A", -rebate, rebate_rule["clause"]))
    elif rebate_rule.get("marginal_relief"):
        excess = taxable - rebate_rule["income_limit"]
        if tax > excess:
            rebate = tax - excess
            trace.append(("Rebate 87A marginal relief", -rebate, rebate_rule["clause"]))
    tax_after = tax - rebate

    sur = 0.0
    rate = surcharge_rate(taxable, rules, regime)
    if rate > 0 and tax_after > 0:
        sur = tax_after * rate
        # marginal relief: find threshold of the applicable bracket
        thr = max(b["above"] for b in rules["surcharge"]["brackets"]
                  if not (b.get("old_regime_only") and regime != "old") and taxable > b["above"])
        # for the new regime capped at 25%, brackets above 2Cr share the same rate
        tax_thr = slab_tax(thr, slabs)
        sur_thr = tax_thr * surcharge_rate(thr, rules, regime)
        cap = tax_thr + sur_thr + (taxable - thr)
        if tax_after + sur > cap:
            sur = max(0.0, cap - tax_after)
        trace.append(("Surcharge (after marginal relief)", round(sur, 2), rules["surcharge"]["clause"]))

    cess = (tax_after + sur) * rules["cess"]["rate"]
    trace.append(("Cess 4%", round(cess, 2), rules["cess"]["clause"]))

    total = round_half_up(tax_after + sur + cess)
    trace.append(("TOTAL TAX (rounded to rupee)", total, "Section 288B"))
    return {"regime": regime, "taxable_income": taxable, "total_tax": total, "trace": trace}


def compare_regimes(inp, rules=None):
    rules = rules or load_rules()
    old = compute_tax(inp, "old", rules)
    new = compute_tax(inp, "new", rules)
    better = "new" if new["total_tax"] <= old["total_tax"] else "old"
    return {"old": old, "new": new, "recommended": better,
            "saving": abs(old["total_tax"] - new["total_tax"])}


if __name__ == "__main__":
    r = load_rules()
    cases = [
        ("New, taxable 12L", {"gross_salary": 1275000}, "new", 83200),
        ("New, 87A full rebate", {"gross_salary": 775000}, "new", 0),
        ("New, marginal relief", {"gross_salary": 785000}, "new", 10400),
        ("Old, 87A full rebate", {"gross_salary": 550000}, "old", 0),
    ]
    for name, inp, regime, expected in cases:
        got = compute_tax(inp, regime, r)["total_tax"]
        print(f"{'PASS' if got == expected else 'FAIL'}  {name}: got {got}, expected {expected}")
