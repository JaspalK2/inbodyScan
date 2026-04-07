# Tasks: Food Log Quantity Unit Selector

**Input**: Design documents from `/specs/021-quantity-unit-selector/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Per constitution Principle IV, test tasks are MANDATORY for this project.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1 = food log entry, US2 = custom meal builder)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the unit conversion utility that both user stories depend on.

- [ ] T001 Create `frontend/lib/unit-conversions.ts` exporting `UNITS` array and `convertToGrams(qty, symbol, servingSizeG?)` function with conversion factors: g=1, oz=28.3495, lb=453.592, ml=1, cup=240, piece=servingSizeG??100
- [ ] T002 Write unit tests for `convertToGrams` in `frontend/lib/unit-conversions.test.ts` covering all 6 units including piece with and without servingSizeG

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend schema and schema changes that both user stories depend on.

- [ ] T003 Add `entered_quantity: Mapped[float | None]` and `entered_unit: Mapped[str | None]` nullable columns to `DailyFoodLogEntry` in `services/recommendation-service/src/models/food_log.py`
- [ ] T004 [P] Add `entered_quantity: Mapped[float | None]` and `entered_unit: Mapped[str | None]` nullable columns to `CustomMealItem` in `services/recommendation-service/src/models/custom_meal.py`
- [ ] T005 Add optional `entered_quantity: float | None = None` and `entered_unit: str | None = None` fields to `FoodLogEntryIn` and `FoodLogEntryOut` Pydantic models in `services/recommendation-service/src/schemas/recommendation.py`
- [ ] T006 [P] Add optional `entered_quantity: float | None = None` and `entered_unit: str | None = None` fields to `MealItemIn` and `MealItemOut` Pydantic models in `services/recommendation-service/src/schemas/recommendation.py`
- [ ] T007 Extend `FoodLogEntryIn` and `MealItem` TypeScript interfaces in `frontend/lib/api.ts` to add `entered_quantity?: number | null` and `entered_unit?: string | null` optional fields

---

## Phase 3: User Story 1 — Unit Selector on Food Log Entry

**Story goal**: Users can select a unit (g/oz/lb/ml/piece/cup) when adding a food item to their daily food log. The system converts to grams and stores both the original value+unit and the gram-equivalent.

**Independent test**: Search for "chicken breast", change unit to "oz", enter 6, add to log. Food log shows "Chicken Breast — 6 oz (170 g)" with macros correctly scaled.

- [ ] T008 [US1] In `frontend/app/(app)/recommendations/page.tsx` locate the food search result add-row component (where quantity input and "Add to Today" button appear for each food result) and add a unit `<select>` element immediately after the quantity `<input>`, populated from `UNITS` in `unit-conversions.ts`, defaulting to "g"
- [ ] T009 [US1] In the same add-row handler in `frontend/app/(app)/recommendations/page.tsx`, call `convertToGrams(qty, unit, food.serving_size ?? undefined)` before constructing the log entry, set `quantity_g` to the result, and include `entered_quantity` and `entered_unit` in the entry payload sent to `createLogMutation`
- [ ] T010 [US1] Update the food log entry display in `frontend/app/(app)/recommendations/page.tsx` so that each logged entry shows `{entered_quantity} {entered_unit} ({quantity_g}g)` when `entered_unit` is present and not "g"; otherwise show `{quantity_g}g` as before
- [ ] T011 [US1] Add inline validation in the add-row in `frontend/app/(app)/recommendations/page.tsx` that prevents submission and shows an error message when quantity ≤ 0

---

## Phase 4: User Story 2 — Unit Selector on Custom Meal Builder

**Story goal**: Users building a custom meal can specify ingredient quantities in any of the 6 supported units. The meal item is saved with the gram-equivalent and the original entered value+unit.

**Independent test**: In Build a Meal, add "apple", change unit to "piece", enter 2, save meal. Saved meal item shows 364 g (2 × 182 g USDA serving) or 200 g fallback, with entered_unit="piece" stored.

- [ ] T012 [US2] In `frontend/app/(app)/recommendations/page.tsx` locate the custom meal item row (where each pending meal item shows food_name, quantity input, and remove button) and add the same unit `<select>` element from `unit-conversions.ts`, defaulting to "g"
- [ ] T013 [US2] In the meal save handler in `frontend/app/(app)/recommendations/page.tsx`, call `convertToGrams(qty, unit, food.serving_size ?? undefined)` for each item, set `quantity_g` to the result, and include `entered_quantity` and `entered_unit` in the `MealItemIn` payload
- [ ] T014 [US2] Update `SavedMealCard` in `frontend/app/(app)/recommendations/page.tsx` so that each item in the expanded meal detail shows `{entered_quantity} {entered_unit} ({quantity_g}g)` when `entered_unit` is present and not "g"

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T015 Style the unit `<select>` element in `frontend/app/(app)/recommendations/page.tsx` to match existing Tailwind dark-theme inputs: `bg-white/10 border border-white/10 rounded text-xs text-foreground` — consistent with the quantity input adjacent to it
- [ ] T016 Verify existing food log entries (no `entered_unit`) display correctly as `{quantity_g}g` without broken "(null g)" or "(undefined)" text in `frontend/app/(app)/recommendations/page.tsx`
- [ ] T017 Smoke-test all 7 quickstart scenarios from `specs/021-quantity-unit-selector/quickstart.md` on the Vercel preview deployment and confirm all pass before merging to main

---

## Dependencies

```
T001 (unit-conversions.ts) → T002 (tests)
T003, T004 (DB models) → T005, T006 (schemas) → T007 (TS interfaces)
T007, T001 → T008, T009, T010, T011 (US1)
T007, T001 → T012, T013, T014 (US2)
T008–T014 → T015, T016 (polish)
T015, T016 → T017 (smoke test)
```

## Parallel Execution Opportunities

**Phase 2**: T003 and T004 are parallel (different model files); T005/T006 can follow immediately after their respective model tasks.

**Phase 3 + Phase 4**: T008–T011 (US1) and T012–T014 (US2) are independent of each other and can be worked in parallel once Phase 2 is complete.

## Implementation Strategy

**MVP**: Complete Phase 1 + Phase 2 + Phase 3 (US1 only) — delivers the core food log unit selector. US2 (custom meal builder) is a straightforward extension using the same utility.

**Total tasks**: 17
**US1 tasks**: 4 (T008–T011)
**US2 tasks**: 3 (T012–T014)
**Shared/foundational**: 7 (T001–T007)
**Polish**: 3 (T015–T017)
