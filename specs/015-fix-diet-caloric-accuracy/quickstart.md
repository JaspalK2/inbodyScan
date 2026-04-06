# Quickstart: Fix Diet Plan Caloric Accuracy (015)

## Fast validation

```bash
cd services/recommendation-service
python3.13 -c "
import sys
sys.path.insert(0, 'src')
from services.diet_engine import generate_diet_plan
from dataclasses import dataclass

@dataclass
class M:
    calories: float = 2200
    protein_g: float = 165
    carbs_g: float = 248
    fat_g: float = 73

failures = []
for target_cal in [1200, 1800, 2200, 3000, 4000]:
    m = M(calories=target_cal, protein_g=target_cal*0.075,
          carbs_g=target_cal*0.1125, fat_g=target_cal*0.0333)
    plan = generate_diet_plan(m, [], 'general_health')
    for day in plan['days']:
        cal = day['day_totals']['calories']
        dev = abs(cal - target_cal) / target_cal * 100
        if dev > 5.0:
            failures.append(f'target={target_cal} day={day[\"day\"]} dev={dev:.1f}%')

if failures:
    print('FAIL:', failures)
    sys.exit(1)
print('All caloric targets within ±5% ✓')
"
```

## Scenarios

### Scenario 1 — Happy path: 2200 kcal plan within ±5%
1. Run the fast validation above with target_cal=2200
2. **Expected**: All 7 days show deviation ≤ 5.0%

### Scenario 2 — Low caloric target (1200 kcal)
1. Run with target_cal=1200
2. **Expected**: All 7 days within ±5% — no items below 20g

### Scenario 3 — High caloric target (4000 kcal)
1. Run with target_cal=4000
2. **Expected**: All 7 days within ±5% — no items above 600g

### Scenario 4 — Vegetarian restriction
```bash
plan = generate_diet_plan(m, ["vegetarian"], "general_health")
# Expected: still within ±5% despite restricted food set
```

## Unit test runner

```bash
cd services/recommendation-service
python3.13 -m pytest tests/test_diet_engine.py -v
```
