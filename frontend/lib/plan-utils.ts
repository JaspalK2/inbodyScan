/**
 * Pure utility functions for plan editing — extracted for testability.
 * Used by WorkoutPlanCard and DietPlanCard in the recommendations page.
 */

export interface MacroTotals {
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  total_calories: number;
}

interface PlanMeal {
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  calories?: number;
}

interface PlanDay {
  meals?: PlanMeal[];
}

/**
 * Compute aggregate macro totals from a diet plan's days array.
 * Zero-value or missing fields are excluded from the sum.
 * Calories are computed from macros: protein*4 + carbs*4 + fat*9.
 */
export function computeMacroTotals(days: PlanDay[]): MacroTotals {
  let total_protein_g = 0;
  let total_carbs_g = 0;
  let total_fat_g = 0;

  for (const day of days) {
    for (const meal of day.meals ?? []) {
      if ((meal.protein_g ?? 0) > 0) total_protein_g += meal.protein_g!;
      if ((meal.carbs_g ?? 0) > 0)   total_carbs_g   += meal.carbs_g!;
      if ((meal.fat_g ?? 0) > 0)     total_fat_g     += meal.fat_g!;
    }
  }

  const total_calories = total_protein_g * 4 + total_carbs_g * 4 + total_fat_g * 9;
  return { total_protein_g, total_carbs_g, total_fat_g, total_calories };
}

/**
 * Returns true if any exercise in the generated workout plan has sets < 1.
 * Used to block saving with an invalid plan.
 */
export function hasInvalidSets(plan: { weeks?: { days?: { exercises?: { sets?: number | string }[] }[] }[] }): boolean {
  for (const week of plan.weeks ?? []) {
    for (const day of week.days ?? []) {
      for (const ex of day.exercises ?? []) {
        if ((parseInt(String(ex.sets ?? "0")) || 0) < 1) return true;
      }
    }
  }
  return false;
}
