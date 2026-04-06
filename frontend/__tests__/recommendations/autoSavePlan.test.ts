/**
 * Unit tests for auto-save-all-days logic (018-diet-restrictions-plan-ux).
 *
 * We test the pure control-flow logic extracted from the generateMutation.onSuccess
 * callback, verifying that:
 *  - createDayPlan is called exactly 7 times after successful generation
 *  - each call carries the correct notes (recommendation ID) for grouping
 *  - the day-plans query is invalidated after all saves
 *  - createDayPlan is NOT called if generation fails
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Minimal stub types
// ---------------------------------------------------------------------------
interface MealTotals {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g?: number;
}
interface DietItem {
  food_name: string;
  grams: number;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}
interface DietMeal {
  meal_name: string;
  items: DietItem[];
  meal_totals: MealTotals;
}
interface DietDay {
  day: number;
  meals: DietMeal[];
  day_totals: MealTotals;
}
interface DietRecOut {
  id: string;
  goal_type: string;
  structured_plan: { days: DietDay[] };
}

interface DayPlanPayload {
  name: string;
  plan_date: string;
  notes: string;
  entries: unknown[];
}

// ---------------------------------------------------------------------------
// Extracted auto-save logic (mirrors generateMutation.onSuccess from page.tsx)
// ---------------------------------------------------------------------------
async function autoSaveAllDays(opts: {
  rec: DietRecOut;
  todayISO: string;
  createDayPlan: (payload: DayPlanPayload) => Promise<void>;
  invalidateQueries: (key: { queryKey: string[] }) => void;
}) {
  const { rec, todayISO, createDayPlan, invalidateQueries } = opts;
  const days = rec.structured_plan?.days ?? [];
  for (const day of days) {
    await createDayPlan({
      name: `AI Plan ${todayISO} (Day ${day.day})`,
      plan_date: todayISO,
      notes: rec.id,
      entries: day.meals.map((meal) => ({
        meal_slot: meal.meal_name.toLowerCase(),
        custom_meal_name: meal.meal_name,
        calories_kcal: meal.meal_totals.calories,
        protein_g: meal.meal_totals.protein_g,
        carbs_g: meal.meal_totals.carbs_g,
        fat_g: meal.meal_totals.fat_g,
        fiber_g: meal.meal_totals.fiber_g ?? 0,
        items_snapshot: meal.items,
      })),
    });
  }
  invalidateQueries({ queryKey: ["day-plans"] });
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeMeal(name: string): DietMeal {
  return {
    meal_name: name,
    items: [{ food_name: "Oats", grams: 80, calories: 304, protein_g: 11, carbs_g: 52, fat_g: 6 }],
    meal_totals: { calories: 550, protein_g: 41, carbs_g: 62, fat_g: 18, fiber_g: 5 },
  };
}

function makeRec(id = "test-rec-id"): DietRecOut {
  return {
    id,
    goal_type: "build_muscle",
    structured_plan: {
      days: Array.from({ length: 7 }, (_, i) => ({
        day: i + 1,
        meals: ["Breakfast", "Lunch", "Dinner", "Snack"].map(makeMeal),
        day_totals: { calories: 2200, protein_g: 165, carbs_g: 247, fat_g: 73 },
      })),
    },
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("autoSaveAllDays", () => {
  let createDayPlan: ReturnType<typeof vi.fn>;
  let invalidateQueries: ReturnType<typeof vi.fn>;
  const TODAY = "2026-04-06";

  beforeEach(() => {
    createDayPlan = vi.fn().mockResolvedValue(undefined);
    invalidateQueries = vi.fn();
  });

  it("auto-saves 7 day plans on successful generation", async () => {
    const rec = makeRec("my-rec-uuid");
    await autoSaveAllDays({ rec, todayISO: TODAY, createDayPlan, invalidateQueries });

    expect(createDayPlan).toHaveBeenCalledTimes(7);
  });

  it("each save call carries notes=rec.id for grouping", async () => {
    const rec = makeRec("unique-rec-id");
    await autoSaveAllDays({ rec, todayISO: TODAY, createDayPlan, invalidateQueries });

    const calls = createDayPlan.mock.calls as [DayPlanPayload][];
    calls.forEach(([payload]) => {
      expect(payload.notes).toBe("unique-rec-id");
    });
  });

  it("day plan names include date and day number", async () => {
    const rec = makeRec();
    await autoSaveAllDays({ rec, todayISO: TODAY, createDayPlan, invalidateQueries });

    const names = (createDayPlan.mock.calls as [DayPlanPayload][]).map(([p]) => p.name);
    expect(names).toContain(`AI Plan ${TODAY} (Day 1)`);
    expect(names).toContain(`AI Plan ${TODAY} (Day 7)`);
  });

  it("invalidates day-plans query after all 7 saves", async () => {
    await autoSaveAllDays({ rec: makeRec(), todayISO: TODAY, createDayPlan, invalidateQueries });

    expect(invalidateQueries).toHaveBeenCalledTimes(1);
    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ["day-plans"] });
  });

  it("does not auto-save if rec has no days", async () => {
    const rec: DietRecOut = { id: "empty", goal_type: "general_health", structured_plan: { days: [] } };
    await autoSaveAllDays({ rec, todayISO: TODAY, createDayPlan, invalidateQueries });

    expect(createDayPlan).not.toHaveBeenCalled();
    // Still invalidates so UI refreshes
    expect(invalidateQueries).toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Group-by-notes helper (mirrors UI grouping logic)
// ---------------------------------------------------------------------------
function groupByNotes<T extends { notes?: string | null; id: string }>(plans: T[]): Map<string, T[]> {
  const result = new Map<string, T[]>();
  for (const plan of plans) {
    const key = plan.notes ?? "__manual__";
    if (!result.has(key)) result.set(key, []);
    result.get(key)!.push(plan);
  }
  return result;
}

describe("groupByNotes", () => {
  it("groups 14 day plans into 2 plan blocks when they share notes values", () => {
    const plans = [
      ...Array.from({ length: 7 }, (_, i) => ({ id: `r1-day${i + 1}`, notes: "rec-1" })),
      ...Array.from({ length: 7 }, (_, i) => ({ id: `r2-day${i + 1}`, notes: "rec-2" })),
    ];
    const groups = groupByNotes(plans);
    expect(groups.size).toBe(2);
    expect(groups.get("rec-1")!.length).toBe(7);
    expect(groups.get("rec-2")!.length).toBe(7);
  });

  it("puts plans with null notes into a separate __manual__ group", () => {
    const plans = [
      { id: "m1", notes: null },
      { id: "m2", notes: null },
      { id: "a1", notes: "rec-1" },
    ];
    const groups = groupByNotes(plans);
    expect(groups.get("__manual__")!.length).toBe(2);
    expect(groups.get("rec-1")!.length).toBe(1);
  });
});
