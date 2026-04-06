# Research: Fix Save Diet Day Plan Visibility (016)

## Decision 1: Error handling in async event handlers (React)

- **Decision**: Use `try/catch/finally` with local React state for error display — not `useMutation` (which would require refactoring the existing `async function`)
- **Rationale**: The `saveDayPlan` function is a plain async function, not a mutation. Converting it to `useMutation` is a larger refactor. Adding `catch` to the existing try block is the minimal, safe change.
- **Alternatives**: `useMutation` from TanStack Query (rejected — larger refactor, no material benefit for a single function); `window.alert()` (already present, rejected — blocking UX)

## Decision 2: TanStack Query cache invalidation scope

- **Decision**: `qc.invalidateQueries({ queryKey: ["day-plans"] })` is sufficient — no need to invalidate by exact match or use `refetchQueries`
- **Rationale**: All three components (`DietDayRow`, `FoodMealsTab`, `DayPlannerTab`) call `useQueryClient()` from the same `QueryClientProvider` in the Next.js App Router layout. TanStack Query v5 invalidation with a partial key `["day-plans"]` marks all queries whose key starts with `["day-plans"]` as stale and refetches active ones. This is the correct behaviour.
- **Research finding**: The bug is NOT in the invalidation logic — it is in the missing `catch` block that prevents the invalidation from ever running on error.

## Decision 3: Success feedback duration

- **Decision**: 3-second auto-dismiss via `setTimeout(() => setSaveSuccess(false), 3000)`
- **Rationale**: Standard auto-dismiss duration for transient success messages in web apps. Short enough not to clutter the UI; long enough to be noticed.
- **Note**: The `setTimeout` return value should be stored in a `useRef` and cleared on component unmount to prevent state updates on unmounted components.

## Decision 4: Inline vs toast notification

- **Decision**: Inline state (`saveError`, `saveSuccess`) displayed directly below the "Save day" button row
- **Rationale**: No toast library is present in the frontend (`package.json` has no sonner, react-hot-toast, etc.). Inline state is consistent with other error/loading patterns in the same file (e.g. `savingMeal` in FoodMealsTab, `savingDay` in DietDayRow).
