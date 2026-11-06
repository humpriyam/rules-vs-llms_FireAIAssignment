"""Independent reference oracle for FY 2024-25. Does NOT read the rules JSON."""
import math
from fractions import Fraction as F

NEW_STEPS = [(300000, 5), (700000, 5), (1000000, 5), (1200000, 5), (1500000, 10)]
OLD_STEPS = {
    "below_60": [(250000, 5), (500000, 15), (1000000, 10)],
    "60_to_79": [(300000, 5), (500000, 15), (1000000, 10)],
    "80_plus": [(500000, 20), (1000000, 10)],
}
SUR = [(5_000_000, 10), (10_000_000, 15), (20_000_000, 25), (50_000_000, 37)]


def _tax(t, steps):
    return sum(F(p, 100) * max(0, t - th) for th, p in steps)


def _sur_rate(t, regime):
    r = 0
    for th, p in SUR:
        if t > th:
            r = p
    return min(r, 25) if regime == "new" else r


def oracle(inp, regime):
    gross = inp["gross_salary"]
    age = inp.get("age", 30)
    inc = F(gross - min(75000 if regime == "new" else 50000, gross))
    if regime == "old":
        hra, rent = inp.get("hra_received", 0), inp.get("rent_paid", 0)
        if hra > 0 and rent > 0:
            sal = inp.get("basic", 0) + inp.get("da", 0)
            pct = 50 if inp.get("metro") else 40
            inc -= max(F(0), min(F(hra), rent - F(sal, 10), F(pct * sal, 100)))
        inc -= min(inp.get("home_loan_interest", 0), 200000)
        inc -= min(inp.get("sec_80c", 0), 150000)
        inc -= min(inp.get("sec_80ccd_1b", 0), 50000)
        inc -= min(inp.get("sec_80d_self", 0), 50000 if age >= 60 else 25000)
        inc -= min(inp.get("sec_80d_parents", 0), 50000 if inp.get("parents_senior") else 25000)
    inc = max(F(0), inc)
    taxable = math.floor((inc + 5) / 10) * 10
    steps = NEW_STEPS if regime == "new" else OLD_STEPS[
        "80_plus" if age >= 80 else "60_to_79" if age >= 60 else "below_60"]
    tax = _tax(taxable, steps)
    if regime == "new":
        tax = F(0) if taxable <= 700000 else min(tax, F(taxable - 700000))
    elif taxable <= 500000:
        tax -= min(tax, F(12500))
    sur = F(0)
    rate = _sur_rate(taxable, regime)
    if rate and tax > 0:
        sur = tax * rate / 100
        thr = max(th for th, p in SUR if taxable > th and (regime == "old" or p <= 25))
        cap = _tax(thr, steps) * (100 + _sur_rate(thr, regime)) / 100 + (taxable - thr)
        if tax + sur > cap:
            sur = max(F(0), cap - tax)
    total = (tax + sur) * 104 / 100
    return math.floor(total + F(1, 2))