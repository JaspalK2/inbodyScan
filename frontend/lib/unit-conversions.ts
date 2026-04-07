export type UnitSymbol = "g" | "oz" | "lb" | "ml" | "piece" | "cup";

export interface UnitOption {
  symbol: UnitSymbol;
  label: string;
  toGrams: (qty: number, servingSizeG?: number) => number;
}

export const UNITS: UnitOption[] = [
  { symbol: "g",     label: "g",     toGrams: (qty) => qty },
  { symbol: "oz",    label: "oz",    toGrams: (qty) => qty * 28.3495 },
  { symbol: "lb",    label: "lb",    toGrams: (qty) => qty * 453.592 },
  { symbol: "ml",    label: "ml",    toGrams: (qty) => qty },
  { symbol: "cup",   label: "cup",   toGrams: (qty) => qty * 240 },
  { symbol: "piece", label: "piece", toGrams: (qty, servingSizeG) => qty * (servingSizeG ?? 100) },
];

/**
 * Convert a user-entered quantity to grams.
 * @param qty         The number the user typed (must be > 0).
 * @param symbol      The selected unit symbol.
 * @param servingSizeG  USDA serving size in grams — used only when symbol === "piece".
 */
export function convertToGrams(qty: number, symbol: UnitSymbol, servingSizeG?: number): number {
  const unit = UNITS.find((u) => u.symbol === symbol);
  if (!unit) return qty; // unknown unit — pass through as grams
  return unit.toGrams(qty, servingSizeG);
}
