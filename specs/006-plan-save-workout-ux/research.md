# Research: Plan Save Flow and Workout UX Fixes (006)

## Decision 1: Batching Sequential Mutations on "Save Day"

**Decision**: Execute mutations sequentially in a single `async` function passed to `useMutation.mutationFn`. First call `createDayPlan`, then call `createMeal` N times (once per non-empty slot) using `Promise.all` for the meal saves (they are independent). If any meal save fails, report partial failure via toast but do not roll back the day plan — day plan is the primary record.

**Rationale**: TanStack Query v5 `useMutation` wraps a plain async function; calling multiple service functions sequentially within it is the canonical approach. `Promise.all` for independent meal saves maximises throughput. Partial failure is acceptable because meals are derived from the day plan and can be recreated.

**Alternatives considered**: Separate `useMutation` calls chained via `onSuccess` — rejected because it creates fragile callback chains that are hard to reason about and don't support partial failure reporting cleanly.

---

## Decision 2: Live Score Debounce Pattern

**Decision**: Use a `useRef` for the debounce timer and a `useEffect` that watches the plan/days state. When state changes, clear the previous timer and set a new 300ms timer that calls the score endpoint. Score is stored in local component state (`useState`). This is already implemented in the workout editor for generated plans; the same pattern is extended to the split builder.

**Rationale**: `useRef` + `useEffect` debounce is the canonical React 18 pattern for debounced side effects. It avoids creating new closures on every render and plays well with concurrent rendering since the effect cleanup handles timer cancellation.

**Alternatives considered**: `useDeferredValue` — not appropriate here because we need a time-based delay (API call), not a priority-based one.

---

## Decision 3: Immutable Exercise Addition Pattern

**Decision**: Use nested `.map` to produce a new `weeks` array:
```
newWeeks = plan.weeks.map((w, wi) =>
  wi !== targetWeekIdx ? w : {
    ...w,
    days: w.days.map((d, di) =>
      di !== targetDayIdx ? d : {
        ...d,
        exercises: [...d.exercises, newExercise]
      }
    )
  }
)
```
This is O(W×D) where W = weeks (4) and D = days (7) — effectively O(1) for this dataset size.

**Rationale**: Immutable updates with `.map` and spread are the standard React state mutation pattern and are already used in the existing `WorkoutPlanCard` edit handlers. Consistent with existing code; no new patterns introduced.

**Alternatives considered**: Immer `produce` — adds a dependency; overkill for a 4-week × 7-day structure.

---

## Decision 4: "Day Planner — [Slot]" Meal Naming

**Decision**: When saving a generated diet day, create custom meals with names in the format `"Day Planner — {slot}"` where `{slot}` is capitalised (e.g., `"Day Planner — Breakfast"`). The em-dash (—) is used as separator to make the prefix visually distinct and unlikely to conflict with user-chosen names.

**Rationale**: The em-dash is unambiguous, renders well in all browsers, and is unlikely to appear in user-typed meal names. The prefix format is consistent across all slots and easily parseable for filtering if needed in future.

**Alternatives considered**: Square brackets `[Day Planner] Breakfast` — less readable; parentheses — could conflict with brand names in user meals.

---

## Decision 5: Removing Day Plans from Food & Meals Saved Tab (Reverting 005 Addition)

**Decision**: Remove the "Day Plans" section from the Food & Meals → Saved Meals sub-tab that was added in feature 005. That section was premature — per the 006 spec, the Saved Meals tab should show only individual custom meals (including those auto-saved from day plans), not whole-day plan records. Day plans stay exclusively in the Day Planner tab.

**Rationale**: Clean separation of concerns. The two tabs serve different user intents: "I want to use a single meal" (Food & Meals) vs "I want to plan my whole day" (Day Planner). Mixing them caused the original confusion described in the feature request.

**Alternatives considered**: Keep both sections visible in Food & Meals — rejected because it duplicates data and confuses users about where to find things.

---

## License Compliance Check

All changes in this feature are:
- Pure frontend UI changes (React/Next.js — MIT)
- No new npm packages required
- No new backend endpoints required
- No new Python packages required

**Constitution Principle III gate**: PASS — no new dependencies.
