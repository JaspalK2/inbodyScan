/**
 * Unit tests for the saveDayPlan control-flow logic (016-fix-save-day-plan-visibility).
 *
 * We test the pure logic as a standalone async function extracted from the component,
 * verifying state transitions without mounting the full React tree.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ---------------------------------------------------------------------------
// Minimal stub types
// ---------------------------------------------------------------------------
interface SaveState {
  savingDay: boolean;
  saveError: string | null;
  saveSuccess: boolean;
}

// ---------------------------------------------------------------------------
// Extracted control-flow function (mirrors DietDayRow.saveDayPlan logic)
// ---------------------------------------------------------------------------
async function saveDayPlan(opts: {
  nonEmptyMeals: unknown[];
  createDayPlan: () => Promise<void>;
  invalidateQueries: () => void;
  state: SaveState;
  setState: (patch: Partial<SaveState>) => void;
  successTimer: { current: ReturnType<typeof setTimeout> | null };
}) {
  const { nonEmptyMeals, createDayPlan, invalidateQueries, state, setState, successTimer } = opts;

  if (nonEmptyMeals.length === 0) {
    setState({ saveError: "No meals to save — add foods first." });
    return;
  }

  setState({ saveError: null, saveSuccess: false, savingDay: true });

  try {
    await createDayPlan();
    invalidateQueries();
    setState({ saveSuccess: true });
    if (successTimer.current) clearTimeout(successTimer.current);
    successTimer.current = setTimeout(() => setState({ saveSuccess: false }), 3000);
  } catch {
    setState({ saveError: "Failed to save — please try again." });
  } finally {
    setState({ savingDay: false });
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeState(): SaveState {
  return { savingDay: false, saveError: null, saveSuccess: false };
}

function makePatcher(state: SaveState) {
  return (patch: Partial<SaveState>) => Object.assign(state, patch);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("saveDayPlan control-flow", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("(a) empty meals guard — sets saveError, does NOT call createDayPlan", async () => {
    const state = makeState();
    const createDayPlan = vi.fn().mockResolvedValue(undefined);
    const invalidateQueries = vi.fn();
    const successTimer = { current: null };

    await saveDayPlan({
      nonEmptyMeals: [],
      createDayPlan,
      invalidateQueries,
      state,
      setState: makePatcher(state),
      successTimer,
    });

    expect(createDayPlan).not.toHaveBeenCalled();
    expect(invalidateQueries).not.toHaveBeenCalled();
    expect(state.saveError).toBe("No meals to save — add foods first.");
    expect(state.savingDay).toBe(false);
    expect(state.saveSuccess).toBe(false);
  });

  it("(b) successful save — calls invalidateQueries and sets saveSuccess", async () => {
    const state = makeState();
    const createDayPlan = vi.fn().mockResolvedValue(undefined);
    const invalidateQueries = vi.fn();
    const successTimer = { current: null };

    await saveDayPlan({
      nonEmptyMeals: [{ meal_name: "breakfast" }],
      createDayPlan,
      invalidateQueries,
      state,
      setState: makePatcher(state),
      successTimer,
    });

    expect(createDayPlan).toHaveBeenCalledOnce();
    expect(invalidateQueries).toHaveBeenCalledOnce();
    expect(state.saveSuccess).toBe(true);
    expect(state.saveError).toBeNull();
    expect(state.savingDay).toBe(false);
  });

  it("(c) failed save — sets saveError and clears savingDay", async () => {
    const state = makeState();
    const createDayPlan = vi.fn().mockRejectedValue(new Error("network error"));
    const invalidateQueries = vi.fn();
    const successTimer = { current: null };

    await saveDayPlan({
      nonEmptyMeals: [{ meal_name: "breakfast" }],
      createDayPlan,
      invalidateQueries,
      state,
      setState: makePatcher(state),
      successTimer,
    });

    expect(state.saveError).toBe("Failed to save — please try again.");
    expect(state.saveSuccess).toBe(false);
    expect(state.savingDay).toBe(false);
    expect(invalidateQueries).not.toHaveBeenCalled();
  });

  it("(d) success message clears after 3 seconds via fake timers", async () => {
    const state = makeState();
    const createDayPlan = vi.fn().mockResolvedValue(undefined);
    const invalidateQueries = vi.fn();
    const successTimer = { current: null };

    await saveDayPlan({
      nonEmptyMeals: [{ meal_name: "breakfast" }],
      createDayPlan,
      invalidateQueries,
      state,
      setState: makePatcher(state),
      successTimer,
    });

    expect(state.saveSuccess).toBe(true);

    vi.advanceTimersByTime(3000);

    expect(state.saveSuccess).toBe(false);
  });
});
