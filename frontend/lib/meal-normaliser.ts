/**
 * normaliseMeal — maps both the old LLM diet plan schema and the new
 * algorithmic engine schema to a single internal shape used by DietDayRow.
 *
 * Old LLM schema:
 *   { meal: "breakfast", foods: ["Oats 80g", ...], calories: 400, protein_g: 15, ... }
 *
 * New algorithmic schema:
 *   { meal_name: "Breakfast", items: [{food_name:"Oats",grams:93.1,...}],
 *     meal_totals: { calories: 550, protein_g: 20, ... } }
 */

export interface NormalisedMeal {
  mealLabel: string;
  mealSlot: string;
  foods: string[];
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  _mf: { c: number; p: number; cb: number; f: number }[];
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normaliseMeal(meal: any): NormalisedMeal {
  // Meal label — new engine uses meal_name (capitalised), old uses meal (lowercase)
  let mealLabel: string;
  if (meal.meal_name) {
    mealLabel = meal.meal_name as string;
  } else if (meal.meal) {
    const s = meal.meal as string;
    mealLabel = s.charAt(0).toUpperCase() + s.slice(1);
  } else {
    mealLabel = "Meal";
  }

  // Meal slot — lowercase string used for day-plan save
  const mealSlot: string = meal.meal
    ? (meal.meal as string)
    : (meal.meal_name as string ?? "").toLowerCase();

  // Food strings — old format: string[]; new format: items[]{food_name, grams}
  let foods: string[];
  if (Array.isArray(meal.foods) && meal.foods.length > 0) {
    foods = meal.foods as string[];
  } else if (Array.isArray(meal.items) && meal.items.length > 0) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    foods = (meal.items as any[]).map((item: any) => `${item.food_name} ${item.grams}g`);
  } else {
    foods = [];
  }

  // Macros — old format: flat fields; new format: nested meal_totals object
  const totals = meal.meal_totals ?? {};
  const calories  = meal.calories   ?? totals.calories   ?? 0;
  const protein_g = meal.protein_g  ?? totals.protein_g  ?? 0;
  const carbs_g   = meal.carbs_g    ?? totals.carbs_g    ?? 0;
  const fat_g     = meal.fat_g      ?? totals.fat_g      ?? 0;
  const fiber_g   = meal.fiber_g    ?? totals.fiber_g    ?? 0;

  return {
    mealLabel,
    mealSlot,
    foods,
    calories,
    protein_g,
    carbs_g,
    fat_g,
    fiber_g,
    _mf: meal._mf ?? [],
  };
}
