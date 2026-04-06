# Quickstart: Workout & Diet UX Fixes (009)

## What's changing

Seven targeted fixes across two surfaces:

| # | Fix | Surface |
|---|-----|---------|
| 1 | Token expiry — silent refresh on recommendations page | `frontend/lib/api.ts` |
| 2 | Workout plan: 1-week only (no more 4-week plans) | `recommendation-service/prompt_builder.py` |
| 3 | Workout plan: score floor ≥ 90 at generation | `recommendation-service/recommendation_service.py` |
| 4 | Workout plan: real-time score delta vs. original | `frontend/.../recommendations/page.tsx` |
| 5 | Macro bars: visual update bug fix (Tailwind class) | `frontend/.../recommendations/page.tsx` |
| 6 | Day planner: condensed collapsible day cards + simplified labels | `frontend/.../recommendations/page.tsx` |
| 7 | Day planner: remove individual meal save; compact meal selector | `frontend/.../recommendations/page.tsx` + new `MealSelectorWidget` |

## Key files

```
services/recommendation-service/src/services/prompt_builder.py
services/recommendation-service/src/services/recommendation_service.py
frontend/lib/api.ts
frontend/app/(app)/recommendations/page.tsx
frontend/components/MealSelectorWidget.tsx  ← new
```

## No database changes

No migrations required. `WorkoutRecommendation` continues to store `structured_plan` as JSON. The shape changes from `{ weeks: [...] }` to `{ days: [...] }` for new generations; old plans render via a legacy fallback.

## Testing checklist (local)

- [ ] Navigate to recommendations with expired token → no error, page loads
- [ ] Generate a new workout plan → shows 1 week, score ≥ 90
- [ ] Edit an exercise in the workout plan → score delta appears immediately (e.g., "−1.2 pts from original")
- [ ] Open manual planner, add a meal → macro bars visually move
- [ ] Open day planner → each day is a collapsed card; labels show "Breakfast" not "Day Planner — breakfast"
- [ ] Open day planner meal selector → compact box appears; expands to show Saved Days + Saved Meals sections
- [ ] Confirm no "Save Meal" button exists on individual meal slots in the day planner
