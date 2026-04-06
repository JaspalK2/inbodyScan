# Quickstart: Algorithmic Plan Engine

**Feature**: `013-algorithmic-plan-engine`

## Integration Scenarios

### Scenario 1: Workout Plan Generation (no LLM running)

**Setup**: Recommendation service running with no `GROQ_API_KEY` or `GOOGLE_API_KEY` set.

**Steps**:
1. POST `/api/recommendations/workout/generate` with body:
   ```json
   {
     "scan_id": "test-scan-id",
     "metrics": { "weight": 82.0, "body_fat_percentage": 24.0, "fat_free_mass": 62.3 },
     "goal_type": "muscle_gain"
   }
   ```
2. Expect HTTP 201 with a `structured_plan` containing 7 days.
3. Verify `days` contains exactly 5 training days and 2 rest days.
4. Verify all major muscle groups appear across the training days.
5. Verify `plan_explanation` contains "24" (body fat%) and "muscle".

**Pass criteria**: Response in <2s, all muscle groups covered, `plan_explanation` populated.

---

### Scenario 2: Diet Plan Generation (macro targets matched)

**Steps**:
1. POST `/api/recommendations/diet/generate` with:
   ```json
   {
     "scan_id": "test-scan-id",
     "metrics": { "weight": 82.0, "body_fat_percentage": 24.0 },
     "goal_type": "muscle_gain",
     "dietary_restrictions": [],
     "age": 28, "height_cm": 178.0, "gender": "male",
     "activity_level": "moderately_active"
   }
   ```
2. Expect HTTP 201.
3. For each day in `structured_plan.days`, sum the meal macros.
4. Verify the sum is within ±5% of `structured_plan.daily_targets.calories`.
5. Verify `day_totals` matches the computed sum exactly.

**Pass criteria**: 7 days generated, macro accuracy ±5%, day_totals correct.

---

### Scenario 3: Vegetarian Diet Restriction

**Steps**:
1. POST `/api/recommendations/diet/generate` with `"dietary_restrictions": ["vegetarian"]`
2. Inspect every food string in every meal across all 7 days.
3. Verify no food contains: chicken, beef, pork, lamb, turkey, fish, tuna, salmon, shrimp.

**Pass criteria**: Zero meat/fish items in any meal.

---

### Scenario 4: Food Database Refresh

**Steps**:
1. POST `/api/recommendations/food-db/refresh`
2. Expect HTTP 200 with `foods_fetched` > 0.
3. GET `/api/recommendations/food-db/status`
4. Verify `last_updated` timestamp is recent and `food_count` > 0.

**Pass criteria**: Refresh completes, status endpoint reflects updated timestamp.

---

### Scenario 5: High Body Fat — Cardio Emphasis

**Steps**:
1. POST workout generate with `"body_fat_percentage": 32.0, "goal_type": "lose_fat"`
2. Count days in `structured_plan.days` where `focus` contains "Cardio" or `is_rest` is false with a cardio exercise.
3. Verify at least 2 cardio sessions are present.
4. Verify `plan_explanation` mentions body fat or fat loss.

**Pass criteria**: ≥2 cardio sessions, explanation references body composition.
