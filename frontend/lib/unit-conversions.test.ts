import { convertToGrams, UNITS } from "./unit-conversions";

describe("UNITS array", () => {
  it("has exactly 6 units", () => {
    expect(UNITS).toHaveLength(6);
  });

  it("first unit is grams and is identity", () => {
    expect(UNITS[0].symbol).toBe("g");
    expect(UNITS[0].toGrams(150)).toBe(150);
  });
});

describe("convertToGrams", () => {
  it("g → grams (identity)", () => {
    expect(convertToGrams(100, "g")).toBe(100);
  });

  it("oz → grams", () => {
    expect(convertToGrams(8, "oz")).toBeCloseTo(226.796, 2);
  });

  it("lb → grams", () => {
    expect(convertToGrams(0.5, "lb")).toBeCloseTo(226.796, 2);
  });

  it("ml → grams (water-density 1:1)", () => {
    expect(convertToGrams(355, "ml")).toBe(355);
  });

  it("cup → grams (240 g/cup)", () => {
    expect(convertToGrams(2, "cup")).toBe(480);
  });

  it("piece → falls back to 100 g when no servingSizeG", () => {
    expect(convertToGrams(1, "piece")).toBe(100);
    expect(convertToGrams(3, "piece")).toBe(300);
  });

  it("piece → uses USDA servingSizeG when provided", () => {
    expect(convertToGrams(1, "piece", 182)).toBe(182);
    expect(convertToGrams(2, "piece", 182)).toBe(364);
  });

  it("unknown unit falls through as grams", () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    expect(convertToGrams(50, "tsp" as any)).toBe(50);
  });
});
