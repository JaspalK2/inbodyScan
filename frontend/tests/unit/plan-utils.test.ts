/**
 * Unit tests for plan-utils.ts — computeMacroTotals and hasInvalidSets.
 *
 * Run with: npx ts-node --esm tests/unit/plan-utils.test.ts
 * Or add jest/vitest and import normally.
 *
 * These are assertion-based tests that can be run standalone without a test framework.
 */

import { computeMacroTotals, hasInvalidSets } from "../../lib/plan-utils";

// --- computeMacroTotals ---

const SAMPLE_DAYS = [
  {
    meals: [
      { protein_g: 30, carbs_g: 50, fat_g: 10 },
      { protein_g: 20, carbs_g: 40, fat_g: 5 },
    ],
  },
  {
    meals: [
      { protein_g: 40, carbs_g: 60, fat_g: 15 },
      { protein_g: 0, carbs_g: 0, fat_g: 0 }, // zero values excluded
    ],
  },
];

function assert(condition: boolean, message: string) {
  if (!condition) throw new Error(`FAIL: ${message}`);
  console.log(`PASS: ${message}`);
}

// Test 1: correct aggregation
const totals = computeMacroTotals(SAMPLE_DAYS);
assert(totals.total_protein_g === 90, `protein total should be 90, got ${totals.total_protein_g}`);
assert(totals.total_carbs_g === 150,  `carbs total should be 150, got ${totals.total_carbs_g}`);
assert(totals.total_fat_g === 30,     `fat total should be 30, got ${totals.total_fat_g}`);
const expectedCal = 90 * 4 + 150 * 4 + 30 * 9;
assert(totals.total_calories === expectedCal, `calories should be ${expectedCal}, got ${totals.total_calories}`);

// Test 2: empty days
const emptyTotals = computeMacroTotals([]);
assert(emptyTotals.total_protein_g === 0, "empty days should give 0 protein");
assert(emptyTotals.total_calories === 0, "empty days should give 0 calories");

// Test 3: zero-value meals excluded
const zeroTotals = computeMacroTotals([{ meals: [{ protein_g: 0, carbs_g: 0, fat_g: 0 }] }]);
assert(zeroTotals.total_protein_g === 0, "zero-value meals excluded from totals");

// --- hasInvalidSets ---

// Test 4: valid plan (all sets >= 1)
const validPlan = {
  weeks: [
    { days: [{ exercises: [{ sets: 4 }, { sets: 3 }] }] },
  ],
};
assert(!hasInvalidSets(validPlan), "valid plan should not have invalid sets");

// Test 5: plan with sets = 0
const invalidPlan = {
  weeks: [
    { days: [{ exercises: [{ sets: 0 }] }] },
  ],
};
assert(hasInvalidSets(invalidPlan), "plan with sets=0 should be invalid");

// Test 6: plan with sets as string "0"
const invalidPlanStr = {
  weeks: [
    { days: [{ exercises: [{ sets: "0" }] }] },
  ],
};
assert(hasInvalidSets(invalidPlanStr), "plan with sets='0' should be invalid");

// Test 7: empty plan (no weeks)
const emptyPlan = { weeks: [] };
assert(!hasInvalidSets(emptyPlan), "empty plan should not be invalid");

console.log("\nAll plan-utils unit tests passed ✓");
