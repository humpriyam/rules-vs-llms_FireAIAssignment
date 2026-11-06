"""Builds project_a/data/cases.json: threshold cases + seeded random profiles."""
import json, os, random
from project_a.tests.oracle import oracle

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "cases.json")
THRESHOLDS = [250000, 300000, 500000, 700000, 1000000, 1200000, 1500000,
              5000000, 10000000, 20000000, 50000000]
OFFSETS = [-10, -1, 0, 1, 10]


def build():
    rng = random.Random(2026)
    cases = []
    for t in THRESHOLDS:
        for off in OFFSETS:
            for age in (30, 65):
                if age == 65 and t not in (250000, 300000, 500000, 1000000):
                    continue
                cases.append(("threshold", {"gross_salary": t + 75000 + off, "age": age}))
    for gross in (20000, 50000, 75000, 0):
        cases.append(("tiny_salary", {"gross_salary": gross}))
    cases += [
        ("cap_80c", {"gross_salary": 2000000, "sec_80c": 150001}),
        ("cap_80d_senior_self", {"gross_salary": 2000000, "age": 62, "sec_80d_self": 50001}),
        ("cap_80d_parents_senior", {"gross_salary": 2000000, "sec_80d_parents": 50001, "parents_senior": True}),
        ("cap_home_loan", {"gross_salary": 2000000, "home_loan_interest": 200001}),
        ("hra_nonmetro", {"gross_salary": 1200000, "basic": 500000, "hra_received": 250000, "rent_paid": 240000}),
        ("hra_rent_below_10pct", {"gross_salary": 1200000, "basic": 500000, "hra_received": 250000, "rent_paid": 40000, "metro": True}),
    ]
    while len(cases) < 215:
        gross = int(10 ** rng.uniform(5.3, 7.5) // 100 * 100)
        basic = int(gross * rng.uniform(0.3, 0.5) // 100 * 100)
        inp = {
            "gross_salary": gross, "age": rng.choice([28, 35, 45, 62, 68, 82]),
            "basic": basic, "da": rng.choice([0, 0, basic // 10]),
            "hra_received": int(basic * rng.uniform(0.2, 0.5)),
            "rent_paid": rng.choice([0, int(gross * rng.uniform(0.1, 0.6))]),
            "metro": rng.random() < 0.5,
            "sec_80c": rng.choice([0, 50000, 150000, 200000]),
            "sec_80ccd_1b": rng.choice([0, 50000, 80000]),
            "sec_80d_self": rng.choice([0, 15000, 25000, 40000, 60000]),
            "sec_80d_parents": rng.choice([0, 20000, 25000, 45000, 60000]),
            "parents_senior": rng.random() < 0.5,
            "home_loan_interest": rng.choice([0, 100000, 200000, 300000]),
        }
        cases.append(("random_profile", inp))
    out = []
    for i, (cat, inp) in enumerate(cases):
        out.append({"id": f"c{i:03d}_{cat}", "category": cat, "input": inp,
                    "expected_old": oracle(inp, "old"), "expected_new": oracle(inp, "new")})
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {len(out)} cases to {os.path.normpath(OUT)}")


if __name__ == "__main__":
    build()