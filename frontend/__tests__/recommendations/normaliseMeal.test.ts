import { describe, it, expect } from "vitest";
import { normaliseMeal } from "../../lib/meal-normaliser";

describe("normaliseMeal", () => {
  // (a) Old LLM schema
  it("maps old LLM schema correctly", () => {
    const meal = {
      meal: "breakfast",
      foods: ["Oats 80g", "Banana 120g"],
      calories: 400,
      protein_g: 15,
      carbs_g: 70,
      fat_g: 8,
      fiber_g: 6,
    };
    const nm = normaliseMeal(meal);
    expect(nm.mealLabel).toBe("Breakfast");
    expect(nm.mealSlot).toBe("breakfast");
    expect(nm.foods).toEqual(["Oats 80g", "Banana 120g"]);
    expect(nm.calories).toBe(400);
    expect(nm.protein_g).toBe(15);
    expect(nm.carbs_g).toBe(70);
    expect(nm.fat_g).toBe(8);
    expect(nm.fiber_g).toBe(6);
  });

  // (b) New algorithmic schema
  it("maps new algorithmic schema correctly", () => {
    const meal = {
      meal_name: "Breakfast",
      items: [
        { food_name: "Oats, rolled, dry", grams: 93.1 },
        { food_name: "Chicken breast", grams: 45.2 },
      ],
      meal_totals: {
        calories: 550,
        protein_g: 20,
        carbs_g: 80,
        fat_g: 10,
        fiber_g: 9,
      },
    };
    const nm = normaliseMeal(meal);
    expect(nm.mealLabel).toBe("Breakfast");
    expect(nm.mealSlot).toBe("breakfast");
    expect(nm.foods).toEqual(["Oats, rolled, dry 93.1g", "Chicken breast 45.2g"]);
    expect(nm.calories).toBe(550);
    expect(nm.protein_g).toBe(20);
    expect(nm.carbs_g).toBe(80);
    expect(nm.fat_g).toBe(10);
    expect(nm.fiber_g).toBe(9);
  });

  // (c) Empty / missing schema
  it("handles empty object without crashing", () => {
    const nm = normaliseMeal({});
    expect(nm.mealLabel).toBe("Meal");
    expect(nm.mealSlot).toBe("");
    expect(nm.foods).toEqual([]);
    expect(nm.calories).toBe(0);
    expect(nm.protein_g).toBe(0);
    expect(nm.carbs_g).toBe(0);
    expect(nm.fat_g).toBe(0);
    expect(nm.fiber_g).toBe(0);
    expect(nm._mf).toEqual([]);
  });

  // (d) meal.meal present AND meal.items present — prefers meal field for slot, foods over items
  it("prefers meal.foods over meal.items when both present", () => {
    const meal = {
      meal: "lunch",
      foods: ["Rice 180g"],
      items: [{ food_name: "Should not appear", grams: 100 }],
      calories: 620,
      protein_g: 48,
      carbs_g: 72,
      fat_g: 14,
    };
    const nm = normaliseMeal(meal);
    expect(nm.mealSlot).toBe("lunch");
    expect(nm.foods).toEqual(["Rice 180g"]);
    expect(nm.calories).toBe(620);
  });

  // Capitalisation of all common meal names
  it.each([
    ["breakfast", "Breakfast"],
    ["lunch", "Lunch"],
    ["dinner", "Dinner"],
    ["snack", "Snack"],
  ])("capitalises '%s' to '%s'", (input, expected) => {
    const nm = normaliseMeal({ meal: input, foods: [] });
    expect(nm.mealLabel).toBe(expected);
  });

  // _mf passthrough
  it("passes through existing _mf array", () => {
    const mf = [{ c: 100, p: 10, cb: 20, f: 5 }];
    const nm = normaliseMeal({ meal: "snack", _mf: mf });
    expect(nm._mf).toEqual(mf);
  });

  // Flat macro fields take precedence over meal_totals
  it("prefers flat macro fields over meal_totals when both present", () => {
    const meal = {
      meal_name: "Lunch",
      calories: 700,
      protein_g: 50,
      meal_totals: { calories: 999, protein_g: 999 },
    };
    const nm = normaliseMeal(meal);
    expect(nm.calories).toBe(700);
    expect(nm.protein_g).toBe(50);
  });
});
