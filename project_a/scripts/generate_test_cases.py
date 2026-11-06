# Create this as project_a/scripts/generate_test_cases.py and run it
import csv
import itertools

# We want permutations of these variables
incomes = [
    250000, 300000, 450000, 500000, 510000, # Old regime rebate edges
    700000, 710000, 720000, 750000, # New regime rebate edges (Marginal relief area)
    1000000, 1500000, 2000000,
    5000000, 5050000, 5100000, # Surcharge 10% edges
    10000000, 10100000, # Surcharge 15% edges 
    20000000, 20100000, # Surcharge 25% edges
    50000000, 50100000 # Surcharge 37% (Old only) edges
]
ages = [30, 65, 85] # Normal, Senior, Super Senior
sec_80c = [0, 50000, 150000]
sec_80d = [0, 25000, 50000, 100000] # None, Self, Self+Parents, Senior Self+Senior Parents
home_loan_interest = [0, 200000]

cases = []
case_id = 1

for inc, age, c, d, hli in itertools.product(incomes, ages, sec_80c, sec_80d, home_loan_interest):
    # To keep the size manageable, we prune combinations that aren't useful 
    # (e.g., maxing out deductions on 2.5L income doesn't teach us anything new)
    if inc < 500000 and (c > 0 or d > 0 or hli > 0): continue
    
    cases.append({
        "case_id": f"tc_{case_id:03d}",
        "gross_salary": inc,
        "age": age,
        "sec_80c": c,
        "sec_80d_total": d,
        "home_loan_interest": hli,
        # We leave the tax expected empty for now, as you need to calculate these 
        # using either the official tool (for 30) or your future hand-coded script
        "expected_tax_old": "",
        "expected_tax_new": ""
    })
    case_id += 1

with open('project_a/data/test_cases.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=cases[0].keys())
    writer.writeheader()
    writer.writerows(cases)

print(f"Generated {len(cases)} test cases.")