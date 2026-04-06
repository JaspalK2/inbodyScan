"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { CustomMealOut, DayPlanOut } from "@/lib/api";

interface MealSelectorWidgetProps {
  value: string | null;
  onChange: (id: string | null) => void;
  savedMeals: CustomMealOut[];
  savedDays: DayPlanOut[];
}

export function MealSelectorWidget({ value, onChange, savedMeals, savedDays }: MealSelectorWidgetProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const selectedMeal = savedMeals.find((m) => m.id === value);
  const selectedFromDay = !selectedMeal
    ? savedDays.flatMap((d) => d.entries).find((e) => e.custom_meal_id === value)
    : null;
  const displayName = selectedMeal?.name ?? selectedFromDay?.custom_meal_name ?? "— select a meal —";

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      {/* Collapsed trigger */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between bg-white/10 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-foreground hover:bg-white/15 transition-colors"
      >
        <span className={value ? "text-foreground" : "text-muted-foreground"}>{displayName}</span>
        {open ? <ChevronUp className="h-3 w-3 text-muted-foreground shrink-0" /> : <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />}
      </button>

      {/* Expanded panel */}
      {open && (
        <div className="absolute z-50 top-full mt-1 left-0 right-0 rounded-lg bg-[#1a1a2e] border border-white/10 shadow-xl max-h-56 overflow-y-auto">
          {/* Clear option */}
          <button
            type="button"
            className="w-full text-left px-3 py-1.5 text-xs text-muted-foreground hover:bg-white/10 border-b border-white/5"
            onMouseDown={() => { onChange(null); setOpen(false); }}
          >
            — none —
          </button>

          {/* Saved Days section */}
          {savedDays.length > 0 && (
            <>
              <p className="px-3 py-1 text-xs font-semibold text-cyan-400 bg-white/5 sticky top-0">Saved Days</p>
              {savedDays.map((plan) =>
                plan.entries.filter((e) => e.custom_meal_id).map((entry) => (
                  <button
                    key={entry.id ?? `${plan.id}-${entry.meal_slot}`}
                    type="button"
                    className="w-full text-left px-3 py-1.5 text-xs text-foreground hover:bg-white/10"
                    onMouseDown={() => { onChange(entry.custom_meal_id ?? null); setOpen(false); }}
                  >
                    <span className="font-medium">{entry.custom_meal_name ?? entry.meal_slot}</span>
                    <span className="text-muted-foreground ml-1">· {plan.name}</span>
                  </button>
                ))
              )}
            </>
          )}

          {/* Saved Meals section */}
          {savedMeals.length > 0 && (
            <>
              <p className="px-3 py-1 text-xs font-semibold text-purple-400 bg-white/5 sticky top-0">Saved Meals</p>
              {savedMeals.map((meal) => (
                <button
                  key={meal.id}
                  type="button"
                  className="w-full text-left px-3 py-1.5 text-xs text-foreground hover:bg-white/10"
                  onMouseDown={() => { onChange(meal.id); setOpen(false); }}
                >
                  {meal.name}
                </button>
              ))}
            </>
          )}

          {savedDays.length === 0 && savedMeals.length === 0 && (
            <p className="px-3 py-3 text-xs text-muted-foreground text-center">No saved days or meals yet</p>
          )}
        </div>
      )}
    </div>
  );
}
