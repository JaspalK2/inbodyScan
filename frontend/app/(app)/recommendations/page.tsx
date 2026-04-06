"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  recommendations, scans, user as userApi,
  type MacroTargets, type FoodResult, type CustomMealOut,
  type MealItem, type DayPlanOut, type WorkoutSplitOut,
  type WorkoutScore, type DietRecommendation, type WorkoutRecommendation,
  type SplitDay, type Exercise, type FoodLogEntryOut, type ExerciseSearchResult,
} from "@/lib/api";
import { normaliseMeal, type NormalisedMeal } from "@/lib/meal-normaliser";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { MealSelectorWidget } from "@/components/MealSelectorWidget";
import {
  Utensils, Dumbbell, ChevronDown, ChevronUp, Loader2,
  Search, Plus, Trash2, Save, Edit3, X, Calendar, Target, BookmarkPlus,
} from "lucide-react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmt(n: number | null | undefined, dec = 1) {
  if (n == null) return "—";
  return n.toFixed(dec);
}

function scaleMacros(item: MealItem, qty: number) {
  const scale = qty / 100;
  return {
    calories_kcal: (item.calories_kcal ?? 0) * scale,
    protein_g: (item.protein_g ?? 0) * scale,
    carbs_g: (item.carbs_g ?? 0) * scale,
    fat_g: (item.fat_g ?? 0) * scale,
    fiber_g: (item.fiber_g ?? 0) * scale,
  };
}

function sumMacros(items: MealItem[]) {
  return items.reduce(
    (acc, item) => {
      const s = scaleMacros(item, item.quantity_g ?? 100);
      return {
        calories_kcal: acc.calories_kcal + s.calories_kcal,
        protein_g: acc.protein_g + s.protein_g,
        carbs_g: acc.carbs_g + s.carbs_g,
        fat_g: acc.fat_g + s.fat_g,
        fiber_g: acc.fiber_g + s.fiber_g,
      };
    },
    { calories_kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 }
  );
}

// ─── Macro Progress Bar ───────────────────────────────────────────────────────

const MACRO_COLOR_MAP: Record<string, string> = {
  purple: "#a855f7",
  cyan:   "#06b6d4",
  amber:  "#f59e0b",
  pink:   "#ec4899",
  green:  "#22c55e",
  red:    "#ef4444",
};

function MacroBar({
  label, value, target, unit = "g", color = "purple",
}: { label: string; value: number; target: number; unit?: string; color?: string }) {
  const pct = target > 0 ? Math.min((value / target) * 100, 140) : 0;
  const isOver = pct > 120;
  const isNear = pct > 100;
  const barBg = isOver ? MACRO_COLOR_MAP.red : isNear ? MACRO_COLOR_MAP.amber : (MACRO_COLOR_MAP[color] ?? "#6b7280");
  const textColor = isOver ? "text-red-400" : isNear ? "text-amber-400" : "text-foreground";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className={textColor}>{fmt(value, 0)}/{fmt(target, 0)}{unit}</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: barBg }} />
      </div>
    </div>
  );
}

// ─── Client-side Workout Scorer ──────────────────────────────────────────────
// Dimension weights mirror workout_scorer.py — keep in sync if backend changes.

const WORKOUT_SCORING_WEIGHTS = { coverage: 25, volume: 30, balance: 20, cardio: 15, frequency: 10 };

const _MUSCLE_KW: Record<string, string[]> = {
  "bench press": ["chest","shoulders","triceps"], "bench": ["chest","shoulders","triceps"],
  "push-up": ["chest","shoulders","triceps"], "pushup": ["chest","shoulders","triceps"],
  "incline press": ["chest","shoulders"], "decline press": ["chest"], "dumbbell fly": ["chest"], "cable fly": ["chest"], "pec": ["chest"], "chest": ["chest"],
  "pull-up": ["back","biceps"], "pullup": ["back","biceps"], "chin-up": ["back","biceps"], "chinup": ["back","biceps"],
  "row": ["back","biceps"], "deadlift": ["back","glutes","hamstrings"], "lat pulldown": ["back","biceps"],
  "seated cable row": ["back","biceps"], "t-bar": ["back"], "back": ["back"], "rhomboid": ["back"], "trap": ["back"], "shrug": ["back"],
  "overhead press": ["shoulders","triceps"], "shoulder press": ["shoulders","triceps"], "ohp": ["shoulders","triceps"],
  "lateral raise": ["shoulders"], "front raise": ["shoulders"], "face pull": ["shoulders","back"],
  "arnold press": ["shoulders"], "shoulder": ["shoulders"], "delt": ["shoulders"],
  "curl": ["biceps"], "bicep": ["biceps"], "hammer curl": ["biceps"], "preacher": ["biceps"],
  "tricep": ["triceps"], "skull crusher": ["triceps"], "skullcrusher": ["triceps"], "triceps pushdown": ["triceps"],
  "close grip": ["triceps","chest"], "dip": ["triceps","chest"],
  "squat": ["quads","glutes","hamstrings"], "leg press": ["quads","glutes"], "lunge": ["quads","glutes","hamstrings"],
  "leg extension": ["quads"], "quad": ["quads"], "leg curl": ["hamstrings"],
  "romanian deadlift": ["hamstrings","glutes"], "rdl": ["hamstrings","glutes"], "hamstring": ["hamstrings"],
  "calf raise": ["calves"], "calf": ["calves"], "glute": ["glutes"], "hip thrust": ["glutes","hamstrings"],
  "step-up": ["quads","glutes"], "leg": ["quads"],
  "plank": ["core"], "crunch": ["core"], "ab": ["core"], "sit-up": ["core"], "situp": ["core"],
  "russian twist": ["core"], "hanging leg raise": ["core"], "cable crunch": ["core"], "oblique": ["core"], "core": ["core"],
  "run": ["cardio"], "running": ["cardio"], "jog": ["cardio"], "treadmill": ["cardio"],
  "cycling": ["cardio"], "bike": ["cardio"], "row machine": ["cardio","back"], "elliptical": ["cardio"],
  "hiit": ["cardio"], "jump rope": ["cardio","calves"], "stair": ["cardio","quads","glutes"],
  "swim": ["cardio"], "sprint": ["cardio"], "cardio": ["cardio"],
};
const _GROUP_ROLLUP: Record<string, string> = {
  chest:"chest", back:"back", shoulders:"shoulders", biceps:"arms", triceps:"arms",
  quads:"legs", hamstrings:"legs", glutes:"legs", calves:"legs", core:"core", cardio:"cardio",
};
const _MAJOR_GROUPS = ["chest","back","shoulders","arms","legs","core","cardio"];
const _MIN_SETS: Record<string, number> = { chest:10, back:10, shoulders:8, arms:8, legs:10, core:6, cardio:3 };
const _TGT_SETS: Record<string, number> = { chest:16, back:16, shoulders:12, arms:12, legs:16, core:10, cardio:5 };

function _getMajors(name: string): string[] {
  const lower = name.toLowerCase();
  const found = new Set<string>();
  for (const [kw, muscles] of Object.entries(_MUSCLE_KW)) {
    if (lower.includes(kw)) muscles.forEach((m) => { const maj = _GROUP_ROLLUP[m]; if (maj) found.add(maj); });
  }
  return [...found];
}

function computeWorkoutScore(plan: Record<string, unknown>): number {
  // Support both new {days:[...]} and legacy {weeks:[{days:[...]}]} formats
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const days: any[] = (plan.days as any[]) ?? (plan.weeks as any[])?.[0]?.days ?? [];
  const weekly: Record<string, number> = Object.fromEntries(_MAJOR_GROUPS.map((g) => [g, 0]));
  let trainingDays = 0;

  for (const day of days) {
    if (day.is_rest) continue;
    trainingDays++;
    const exercises = day.exercises ?? [];
    for (const ex of exercises) {
      const name = ex.name ?? ex.exercise_name ?? "";
      const sets = parseInt(String(ex.sets ?? 3)) || 3;
      _getMajors(name).forEach((g) => { weekly[g] = (weekly[g] ?? 0) + sets; });
    }
  }
  void trainingDays;

  // Coverage (25 pts)
  const covered = _MAJOR_GROUPS.filter((g) => (weekly[g] ?? 0) > 0);
  const coverageScore = Math.round((covered.length / _MAJOR_GROUPS.length) * 25);

  // Volume (30 pts)
  let volumePts = 0;
  for (const g of _MAJOR_GROUPS) {
    const s = weekly[g] ?? 0;
    const tgt = _TGT_SETS[g]; const min = _MIN_SETS[g];
    const share = 30 / _MAJOR_GROUPS.length;
    if (s === 0) { /* 0 */ }
    else if (s >= tgt) volumePts += share;
    else if (s >= min) volumePts += ((s - min) / (tgt - min)) * share * 0.75 + share * 0.25;
    else volumePts += (s / min) * share * 0.25;
  }
  const volumeScore = Math.round(volumePts);

  // Balance (20 pts)
  const push = (weekly.chest ?? 0) + (weekly.shoulders ?? 0) + Math.floor((weekly.arms ?? 0) / 2);
  const pull = (weekly.back ?? 0) + Math.floor((weekly.arms ?? 0) / 2);
  const balanceScore = push + pull === 0 ? 0 : Math.round((Math.min(push, pull) / Math.max(push, pull)) * 20);

  // Cardio (15 pts)
  const cardioScore = Math.min(Math.round(((weekly.cardio ?? 0) / _TGT_SETS.cardio) * 15), 15);

  // Frequency (10 pts)
  const totalDays = days.length || 7;
  const restDays = days.filter((d) => d.is_rest).length;
  const restRatio = restDays / totalDays;
  const freqScore = restRatio >= 0.25 && restRatio <= 0.43 ? 10 : restRatio < 0.25 ? 5 : 7;

  return coverageScore + volumeScore + balanceScore + cardioScore + freqScore;
}

// ─── Macro Pie Chart ─────────────────────────────────────────────────────────

const PIE_COLORS = {
  protein: { base: "#a855f7", overflow: "#ef4444" },
  carbs:   { base: "#06b6d4", overflow: "#ef4444" },
  fat:     { base: "#f59e0b", overflow: "#ef4444" },
};

function MacroPieChart({ entries, macros }: { entries: FoodLogEntryOut[]; macros: MacroTargets | null }) {
  const protein = entries.reduce((s, e) => s + (e.protein_g ?? 0), 0);
  const carbs   = entries.reduce((s, e) => s + (e.carbs_g ?? 0), 0);
  const fat     = entries.reduce((s, e) => s + (e.fat_g ?? 0), 0);
  const calories = entries.reduce((s, e) => s + (e.calories_kcal ?? 0), 0);

  if (!macros) {
    const data = [
      { name: "Protein", value: Math.max(protein, 0.01) },
      { name: "Carbs",   value: Math.max(carbs, 0.01) },
      { name: "Fat",     value: Math.max(fat, 0.01) },
    ];
    return (
      <div className="glass-card p-4 space-y-3">
        <p className="text-xs text-muted-foreground">Set up profile to see macro targets</p>
        <div className="flex items-center gap-4">
          <ResponsiveContainer width={140} height={140}>
            <PieChart>
              <Pie data={data} cx="50%" cy="50%" innerRadius={40} outerRadius={65} dataKey="value" strokeWidth={0}>
                <Cell fill={PIE_COLORS.protein.base} />
                <Cell fill={PIE_COLORS.carbs.base} />
                <Cell fill={PIE_COLORS.fat.base} />
              </Pie>
              <Tooltip formatter={(v, name) => [`${Number(v).toFixed(1)}g`, name as string]} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1 text-xs">
            <p className="text-purple-300">Protein: {protein.toFixed(1)}g</p>
            <p className="text-cyan-300">Carbs: {carbs.toFixed(1)}g</p>
            <p className="text-amber-300">Fat: {fat.toFixed(1)}g</p>
            <p className="text-muted-foreground">{calories.toFixed(0)} kcal total</p>
          </div>
        </div>
      </div>
    );
  }

  const proteinPct = macros.protein_g > 0 ? Math.min(protein / macros.protein_g, 1) : 0;
  const carbsPct   = macros.carbs_g   > 0 ? Math.min(carbs   / macros.carbs_g,   1) : 0;
  const fatPct     = macros.fat_g     > 0 ? Math.min(fat     / macros.fat_g,     1) : 0;

  const proteinOver = protein > macros.protein_g;
  const carbsOver   = carbs   > macros.carbs_g;
  const fatOver     = fat     > macros.fat_g;

  const data = [
    { name: "Protein", value: Math.max(proteinPct * 33.33, 0.01), over: proteinOver },
    { name: "Carbs",   value: Math.max(carbsPct   * 33.33, 0.01), over: carbsOver },
    { name: "Fat",     value: Math.max(fatPct     * 33.33, 0.01), over: fatOver },
    { name: "Empty",   value: Math.max(100 - proteinPct * 33.33 - carbsPct * 33.33 - fatPct * 33.33, 0), over: false },
  ].filter((d) => d.name === "Empty" ? d.value > 0.5 : true);

  return (
    <div className="glass-card p-4 space-y-3">
      <h3 className="text-sm font-semibold text-foreground">Today&apos;s Macros</h3>
      <div className="flex items-center gap-4">
        <ResponsiveContainer width={140} height={140}>
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={40} outerRadius={65} dataKey="value" strokeWidth={0}>
              {data.map((entry, i) => (
                <Cell key={i} fill={
                  entry.name === "Empty" ? "rgba(255,255,255,0.05)"
                    : entry.over ? PIE_COLORS[entry.name.toLowerCase() as keyof typeof PIE_COLORS]?.overflow
                    : PIE_COLORS[entry.name.toLowerCase() as keyof typeof PIE_COLORS]?.base
                } />
              ))}
            </Pie>
            <Tooltip formatter={(v, name) => {
              const n = name as string;
              if (n === "Empty") return null;
              const grams = Number(v) / 33.33 * (n === "Protein" ? macros.protein_g : n === "Carbs" ? macros.carbs_g : macros.fat_g);
              return [`${grams.toFixed(1)}g`, n];
            }} />
          </PieChart>
        </ResponsiveContainer>
        <div className="space-y-1.5 text-xs flex-1">
          <div className="flex justify-between">
            <span className={proteinOver ? "text-red-400" : "text-purple-300"}>Protein</span>
            <span className={proteinOver ? "text-red-400" : "text-muted-foreground"}>{protein.toFixed(1)}/{macros.protein_g.toFixed(0)}g{proteinOver ? " ⚠" : ""}</span>
          </div>
          <div className="flex justify-between">
            <span className={carbsOver ? "text-red-400" : "text-cyan-300"}>Carbs</span>
            <span className={carbsOver ? "text-red-400" : "text-muted-foreground"}>{carbs.toFixed(1)}/{macros.carbs_g.toFixed(0)}g{carbsOver ? " ⚠" : ""}</span>
          </div>
          <div className="flex justify-between">
            <span className={fatOver ? "text-red-400" : "text-amber-300"}>Fat</span>
            <span className={fatOver ? "text-red-400" : "text-muted-foreground"}>{fat.toFixed(1)}/{macros.fat_g.toFixed(0)}g{fatOver ? " ⚠" : ""}</span>
          </div>
          <div className="flex justify-between border-t border-white/10 pt-1">
            <span className="text-muted-foreground">Calories</span>
            <span className="text-foreground">{calories.toFixed(0)}/{macros.calories.toFixed(0)} kcal</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Tab nav ─────────────────────────────────────────────────────────────────

const TABS = ["Diet", "Food & Meals", "Day Planner", "Workout"] as const;
type Tab = typeof TABS[number];

function TabBar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  return (
    <div className="flex gap-1 rounded-xl bg-white/5 p-1 w-fit flex-wrap">
      {TABS.map((t) => (
        <button
          key={t}
          onClick={() => onChange(t)}
          className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            active === t ? "bg-purple-600 text-white" : "text-muted-foreground hover:text-foreground"
          }`}
        >
          {t}
        </button>
      ))}
    </div>
  );
}

// ─── Macro Stat Cards ─────────────────────────────────────────────────────────

function MacroStatCard({ label, value, unit, color }: { label: string; value: number; unit: string; color: string }) {
  return (
    <div className={`glass-card p-3 border border-${color}-500/20 text-center`}>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={`text-xl font-bold text-${color}-300`}>{value.toLocaleString()}</p>
      <p className="text-xs text-muted-foreground">{unit}</p>
    </div>
  );
}

// ─── Tab 1: Diet ─────────────────────────────────────────────────────────────

function DietTab() {
  const qc = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [editedPlan, setEditedPlan] = useState<any>(null);
  const [confirmOverwriteDiet, setConfirmOverwriteDiet] = useState(false);

  const { data: scanList } = useQuery({ queryKey: ["scans"], queryFn: scans.list });
  const { data: scanData } = useQuery({
    queryKey: ["scan", scanList?.[0]?.id],
    queryFn: () => scans.get(scanList![0].id),
    enabled: !!scanList?.[0],
  });
  const { data: goal } = useQuery({ queryKey: ["goal"], queryFn: userApi.getGoal });
  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: userApi.getProfile });
  const { data: restrictions } = useQuery({ queryKey: ["restrictions"], queryFn: userApi.getDietaryRestrictions });
  const { data: dietRecs } = useQuery({ queryKey: ["diet-recs"], queryFn: recommendations.listDiet });

  const metricsMap = Object.fromEntries((scanData?.metrics ?? []).map((m) => [m.metric_key, m.metric_value]));
  const goalType = goal?.goal_type ?? "general_health";

  const activityLevel = profile?.activity_level ?? "moderately_active";

  const { data: macros, isLoading: macrosLoading } = useQuery({
    queryKey: ["macros", goalType, activityLevel, scanList?.[0]?.id],
    queryFn: () => recommendations.calculateMacros({
      metrics: metricsMap, goal_type: goalType,
      age: profile?.age ?? undefined,
      height_cm: profile?.height_cm ?? undefined,
      gender: profile?.gender ?? undefined,
      activity_level: activityLevel,
    }),
    enabled: !!scanData,
  });

  const generateMutation = useMutation({
    mutationFn: () => recommendations.generateDiet({
      scan_id: scanList![0].id, metrics: metricsMap, goal_type: goalType,
      dietary_restrictions: (restrictions ?? []).map((r) => r.restriction_type),
      age: profile?.age ?? undefined, height_cm: profile?.height_cm ?? undefined,
      gender: profile?.gender ?? undefined,
      activity_level: profile?.activity_level ?? "moderately_active",
    }),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onSuccess: async (rec: any) => {
      qc.invalidateQueries({ queryKey: ["diet-recs"] });
      // Auto-save all 7 days so they appear in My Saved Meals grouped by rec ID
      const todayISO = new Date().toISOString().slice(0, 10);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const days: any[] = rec?.structured_plan?.days ?? [];
      for (const day of days) {
        try {
          await recommendations.createDayPlan({
            name: `AI Plan ${todayISO} (Day ${day.day})`,
            plan_date: todayISO,
            notes: rec.id,
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            entries: (day.meals as any[]).map((meal: any) => ({
              meal_slot: meal.meal_name?.toLowerCase() ?? "other",
              custom_meal_name: meal.meal_name ?? null,
              calories_kcal: meal.meal_totals?.calories ?? null,
              protein_g: meal.meal_totals?.protein_g ?? null,
              carbs_g: meal.meal_totals?.carbs_g ?? null,
              fat_g: meal.meal_totals?.fat_g ?? null,
              fiber_g: meal.meal_totals?.fiber_g ?? null,
              items_snapshot: meal.items ?? [],
            })),
          });
        } catch {
          // Non-fatal: individual day save failures don't block the UI
        }
      }
      qc.invalidateQueries({ queryKey: ["day-plans"] });
    },
  });

  const editMutation = useMutation({
    mutationFn: ({ id, plan }: { id: string; plan: Record<string, unknown> }) =>
      recommendations.editDietPlan(id, plan),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["diet-recs"] }); setEditingId(null); },
  });

  const deleteDietMutation = useMutation({
    mutationFn: (id: string) => recommendations.deleteDiet(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["diet-recs"] }),
  });

  const today = new Date().toISOString().slice(0, 10);
  const logMealMutation = useMutation({
    mutationFn: (meal: { meal?: string; recId?: string; calories?: number; protein_g?: number; carbs_g?: number; fat_g?: number }) => recommendations.createFoodLog({
      log_date: today,
      entries: [{
        food_name: meal.meal ?? "Diet plan meal",
        source: "diet_plan",
        source_ref_id: meal.recId,
        quantity_g: 100,
        calories_kcal: meal.calories ?? null,
        protein_g: meal.protein_g ?? null,
        carbs_g: meal.carbs_g ?? null,
        fat_g: meal.fat_g ?? null,
        fiber_g: null,
      }],
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["food-log", today] }),
  });

  if (!scanList?.[0]) {
    return <div className="glass-card p-12 text-center text-muted-foreground">Upload a scan first to generate recommendations.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Macro Targets */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h2 className="text-sm font-semibold text-foreground">Daily Macro Targets</h2>
          <span className="text-xs text-muted-foreground">Activity: {activityLevel.replace(/_/g, " ")}</span>
        </div>
        {macrosLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Calculating…</div>
        ) : macros ? (
          <>
            <div className="grid grid-cols-5 gap-2">
              <MacroStatCard label="Calories" value={macros.calories} unit="kcal" color="purple" />
              <MacroStatCard label="Protein" value={macros.protein_g} unit="g" color="cyan" />
              <MacroStatCard label="Carbs" value={macros.carbs_g} unit="g" color="amber" />
              <MacroStatCard label="Fat" value={macros.fat_g} unit="g" color="pink" />
              <MacroStatCard label="Fiber" value={macros.fiber_g} unit="g" color="green" />
            </div>
            <p className="text-xs text-muted-foreground">
              BMR: {macros.bmr.toLocaleString()} kcal · TDEE: {macros.tdee.toLocaleString()} kcal · Goal adjustment: {macros.goal_adjustment_kcal > 0 ? "+" : ""}{macros.goal_adjustment_kcal} kcal · {macros.protein_ratio}
            </p>
            <p className="text-xs text-muted-foreground italic">{macros.notes}</p>
          </>
        ) : null}
      </div>

      {/* Generate */}
      <div className="glass-card p-4 space-y-3">
        {generateMutation.error && (
          <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-4 py-2 text-sm text-destructive flex items-center justify-between gap-2">
            <span>{"Service is currently busy — please try again in a few moments."}</span>
            <Button size="sm" variant="ghost" className="h-7 text-xs shrink-0 text-destructive hover:text-destructive" onClick={() => generateMutation.mutate()}>Try Again</Button>
          </div>
        )}
        {confirmOverwriteDiet && (
          <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 px-4 py-3 text-sm text-amber-300 space-y-2">
            <p>This will replace your existing diet plan. Continue?</p>
            <div className="flex gap-2">
              <Button size="sm" className="h-7 text-xs btn-primary-glass" onClick={() => { setConfirmOverwriteDiet(false); generateMutation.mutate(); }}>Yes, replace</Button>
              <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setConfirmOverwriteDiet(false)}>Cancel</Button>
            </div>
          </div>
        )}
        {!confirmOverwriteDiet && (
          <Button onClick={() => { if ((dietRecs ?? []).length > 0) { setConfirmOverwriteDiet(true); } else { generateMutation.mutate(); } }} disabled={generateMutation.isPending} className="btn-primary-glass flex items-center gap-2">
            {generateMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" />Generating…</> : <><Utensils className="h-4 w-4" />Generate 7-Day Meal Plan</>}
          </Button>
        )}
        {generateMutation.isPending && <p className="text-xs text-muted-foreground animate-pulse">AI is building your plan (~15s)…</p>}
      </div>

      {/* Plans */}
      {(dietRecs ?? []).map((rec) => {
        const active = (rec.edited_plan ?? rec.structured_plan) as Record<string, unknown>;
        const isEditing = editingId === rec.id;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const plan = (isEditing ? editedPlan : active) as any;
        return (
          <DietPlanCard
            key={rec.id} rec={rec} plan={plan} macros={macros ?? null}
            isEditing={isEditing}
            onEdit={() => {
              const deepCopy = JSON.parse(JSON.stringify(active));
              // Initialise per-food macro splits so removal can subtract accurately
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              (deepCopy.days ?? []).forEach((d: any) => {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (d.meals ?? []).forEach((meal: any) => {
                  const n = Math.max((meal.foods ?? []).length, 1);
                  meal._mf = (meal.foods ?? []).map(() => ({
                    c: (meal.calories ?? 0) / n,
                    p: (meal.protein_g ?? 0) / n,
                    cb: (meal.carbs_g ?? 0) / n,
                    f: (meal.fat_g ?? 0) / n,
                  }));
                });
              });
              setEditingId(rec.id);
              setEditedPlan(deepCopy);
            }}
            onCancelEdit={() => setEditingId(null)}
            onSaveEdit={() => {
              // Strip internal tracking field before persisting
              const cleanPlan = JSON.parse(JSON.stringify(editedPlan));
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              (cleanPlan.days ?? []).forEach((d: any) => {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (d.meals ?? []).forEach((meal: any) => { delete meal._mf; });
              });
              editMutation.mutate({ id: rec.id, plan: cleanPlan });
            }}
            onPlanChange={setEditedPlan}
            saving={editMutation.isPending}
            onLogMeal={(meal) => logMealMutation.mutate(meal)}
            onDelete={() => {
              if (window.confirm("Delete this diet plan? This cannot be undone.")) {
                deleteDietMutation.mutate(rec.id);
              }
            }}
          />
        );
      })}
    </div>
  );
}

function DietPlanCard({
  rec, plan, macros, isEditing, onEdit, onCancelEdit, onSaveEdit, onPlanChange, saving, onLogMeal, onDelete,
}: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  rec: DietRecommendation; plan: any; macros: MacroTargets | null;
  isEditing: boolean;
  onEdit: () => void; onCancelEdit: () => void; onSaveEdit: () => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onPlanChange: (p: any) => void;
  saving: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onLogMeal: (meal: any) => void;
  onDelete?: () => void;
}) {
  const [open, setOpen] = useState(false);
  if (!plan) return null;
  return (
    <div className="glass-card overflow-hidden">
      <div className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors cursor-pointer" onClick={() => setOpen((o) => !o)}>
        <div className="flex items-center gap-3">
          <Utensils className="h-4 w-4 text-purple-400" />
          <div className="text-left">
            <p className="text-sm font-medium text-foreground">{rec.goal_type.replace(/_/g, " ")} plan</p>
            <p className="text-xs text-muted-foreground">{new Date(rec.created_at).toLocaleDateString()}{rec.edited_plan ? " · edited" : ""}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!isEditing && <Button size="sm" variant="ghost" className="h-7 px-2 text-xs text-purple-300" onClick={(e) => { e.stopPropagation(); onEdit(); }}><Edit3 className="h-3 w-3 mr-1" />Edit</Button>}
          {onDelete && <Button size="sm" variant="ghost" className="h-7 px-2 text-xs text-red-400 hover:text-red-300" onClick={(e) => { e.stopPropagation(); onDelete(); }}><Trash2 className="h-3 w-3" /></Button>}
          {open ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </div>
      {open && (
        <div className="px-4 pb-4 space-y-4">
          {plan.summary && <p className="text-sm text-muted-foreground">{plan.summary}</p>}
          {isEditing && (
            <div className="space-y-3">
              <div className="flex gap-2">
                <Button size="sm" className="btn-primary-glass h-7 text-xs" onClick={onSaveEdit} disabled={saving}>{saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3 mr-1" />}Save Changes</Button>
                <Button size="sm" variant="ghost" className="h-7 text-xs text-muted-foreground" onClick={onCancelEdit}><X className="h-3 w-3 mr-1" />Cancel</Button>
              </div>
              {/* Live macro totals from edited plan */}
              {(() => {
                type MealRow = { protein_g?: number; carbs_g?: number; fat_g?: number; meals?: MealRow[] };
                const allMeals = (plan?.days as MealRow[] ?? []).flatMap((d) => d.meals ?? []);
                const totalProtein = allMeals.reduce((s: number, m: MealRow) => s + (( m.protein_g ?? 0) > 0 ? (m.protein_g ?? 0) : 0), 0);
                const totalCarbs   = allMeals.reduce((s: number, m: MealRow) => s + ((m.carbs_g   ?? 0) > 0 ? (m.carbs_g   ?? 0) : 0), 0);
                const totalFat     = allMeals.reduce((s: number, m: MealRow) => s + ((m.fat_g     ?? 0) > 0 ? (m.fat_g     ?? 0) : 0), 0);
                const totalCal     = totalProtein * 4 + totalCarbs * 4 + totalFat * 9;
                const pieData = [
                  { name: "Protein", value: Math.max(totalProtein * 4, 0.01) },
                  { name: "Carbs",   value: Math.max(totalCarbs   * 4, 0.01) },
                  { name: "Fat",     value: Math.max(totalFat     * 9, 0.01) },
                ];
                return (
                  <div className="rounded-lg bg-white/5 p-3 space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">Live Macro Totals (avg/day)</p>
                    {totalCal < 1200 && <p className="text-xs text-amber-400">⚠ Daily calories below 1200 kcal — check your portions.</p>}
                    <div className="flex items-center gap-4">
                      <ResponsiveContainer width={100} height={100}>
                        <PieChart>
                          <Pie data={pieData} cx="50%" cy="50%" innerRadius={28} outerRadius={46} dataKey="value" strokeWidth={0}>
                            <Cell fill="#a855f7" />
                            <Cell fill="#06b6d4" />
                            <Cell fill="#f59e0b" />
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="space-y-1 text-xs">
                        <p className="text-purple-300">Protein: {totalProtein.toFixed(1)}g</p>
                        <p className="text-cyan-300">Carbs: {totalCarbs.toFixed(1)}g</p>
                        <p className="text-amber-300">Fat: {totalFat.toFixed(1)}g</p>
                        <p className="text-muted-foreground">{totalCal.toFixed(0)} kcal</p>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {(plan.days as any[])?.map((day: any, di: number) => (
            <DietDayRow key={di} day={day} dayIndex={di} macros={macros} isEditing={isEditing} recId={rec.id} onLogMeal={onLogMeal} onDayChange={(updated) => {
              const newPlan = { ...plan, days: plan.days.map((d: unknown, i: number) => i === di ? updated : d) };
              onPlanChange(newPlan);
            }} />
          ))}
        </div>
      )}
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function DietDayRow({ day, dayIndex, macros, isEditing, onDayChange, recId, onLogMeal }: { day: any; dayIndex: number; macros: MacroTargets | null; isEditing: boolean; onDayChange: (d: any) => void; recId: string; onLogMeal: (meal: any) => void }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  // Which meal index is showing the food search panel
  const [searchMealIdx, setSearchMealIdx] = useState<number | null>(null);
  const [searchQ, setSearchQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  // Quantity (grams) for food being added
  const [addQty, setAddQty] = useState(100);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [pendingFood, setPendingFood] = useState<any | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(searchQ), 300);
    return () => clearTimeout(t);
  }, [searchQ]);

  const { data: searchResults } = useQuery({
    queryKey: ["food-search-day", debouncedQ],
    queryFn: () => recommendations.searchFood(debouncedQ, 8),
    enabled: debouncedQ.length >= 2,
  });

  // Compute totals from meals — never trust AI-provided day_totals (FR-003, FR-004)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const totals = (day.meals as any[] ?? []).reduce(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (acc: Record<string, number>, m: any) => {
      const nm = normaliseMeal(m);
      return {
        calories:   acc.calories   + nm.calories,
        protein_g:  acc.protein_g  + nm.protein_g,
        carbs_g:    acc.carbs_g    + nm.carbs_g,
        fat_g:      acc.fat_g      + nm.fat_g,
        fiber_g:    acc.fiber_g    + nm.fiber_g,
      };
    },
    { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 }
  );
  const deviation = macros ? ((totals.calories ?? 0) - macros.calories) / macros.calories * 100 : 0;
  const devColor = Math.abs(deviation) <= 5 ? "text-green-400" : Math.abs(deviation) <= 15 ? "text-amber-400" : "text-red-400";

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function removeFood(mi: number, fi: number, meal: any) {
    const nm = normaliseMeal(meal);
    const removed = nm._mf[fi] ?? { c: 0, p: 0, cb: 0, f: 0 };
    const updated = {
      ...meal,
      foods: nm.foods.filter((_: string, i: number) => i !== fi),
      // clear items so future renders use foods string array
      items: undefined,
      _mf: nm._mf.filter((_: unknown, i: number) => i !== fi),
      calories: Math.max(0, nm.calories - removed.c),
      protein_g: Math.max(0, nm.protein_g - removed.p),
      carbs_g: Math.max(0, nm.carbs_g - removed.cb),
      fat_g: Math.max(0, nm.fat_g - removed.f),
      meal_totals: undefined,
    };
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onDayChange({ ...day, meals: day.meals.map((m: any, i: number) => i === mi ? updated : m) });
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function confirmAddFood(mi: number, meal: any, food: any, qty: number) {
    const ratio = qty / 100;
    const newMacros = {
      c: (food.calories_kcal ?? 0) * ratio,
      p: (food.protein_g ?? 0) * ratio,
      cb: (food.carbs_g ?? 0) * ratio,
      f: (food.fat_g ?? 0) * ratio,
    };
    const label = `${qty}g ${food.name}`;
    const updated = {
      ...meal,
      foods: [...(meal.foods ?? []), label],
      _mf: [...(meal._mf ?? []), newMacros],
      calories: (meal.calories ?? 0) + newMacros.c,
      protein_g: (meal.protein_g ?? 0) + newMacros.p,
      carbs_g: (meal.carbs_g ?? 0) + newMacros.cb,
      fat_g: (meal.fat_g ?? 0) + newMacros.f,
    };
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onDayChange({ ...day, meals: day.meals.map((m: any, i: number) => i === mi ? updated : m) });
    setPendingFood(null);
    setSearchMealIdx(null);
    setSearchQ("");
    setDebouncedQ("");
    setAddQty(100);
  }

  return (
    <div className="rounded-lg bg-white/5">
      <div className="w-full flex items-center justify-between px-3 py-2 cursor-pointer" onClick={() => setOpen((o) => !o)}>
        <span className="text-sm text-cyan-300 font-medium">Day {day.day}</span>
        <div className="flex items-center gap-3 text-xs">
          {macros && <span className={devColor}>{deviation > 0 ? "+" : ""}{deviation.toFixed(0)}% vs target</span>}
          <span className="text-muted-foreground">{fmt(totals.calories, 0)} kcal</span>
          {open ? <ChevronUp className="h-3 w-3 text-muted-foreground" /> : <ChevronDown className="h-3 w-3 text-muted-foreground" />}
        </div>
      </div>
      {open && (
        <div className="px-3 pb-3 space-y-2">
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {(day.meals as any[])?.map((meal: any, mi: number) => {
            const nm: NormalisedMeal = normaliseMeal(meal);
            return (
            <div key={mi} className="rounded bg-white/5 p-2">
              <p className="text-xs text-purple-300 font-medium mb-1">{nm.mealLabel}</p>
              {isEditing ? (
                <div className="space-y-2">
                  {/* Per-food-item editing */}
                  <div className="space-y-1">
                    {nm.foods.map((food: string, fi: number) => (
                      <div key={fi} className="flex gap-1 items-center">
                        <span className="flex-1 text-xs text-foreground bg-white/5 rounded px-2 py-1">{food}</span>
                        <button type="button" className="text-muted-foreground hover:text-red-400 px-1 text-xs shrink-0"
                          onClick={() => removeFood(mi, fi, meal)}>✕</button>
                      </div>
                    ))}
                  </div>
                  {/* Macro read-only display */}
                  <div className="flex gap-3 text-xs mt-1">
                    <span className="text-purple-300">{fmt(nm.calories, 0)} kcal</span>
                    <span className="text-cyan-300">P {fmt(nm.protein_g, 0)}g</span>
                    <span className="text-amber-300">C {fmt(nm.carbs_g, 0)}g</span>
                    <span className="text-pink-300">F {fmt(nm.fat_g, 0)}g</span>
                  </div>
                  {/* Food search */}
                  {searchMealIdx === mi ? (
                    <div className="space-y-1 pt-1 border-t border-white/10">
                      {pendingFood ? (
                        <div className="space-y-1">
                          <p className="text-xs text-foreground truncate">{pendingFood.name}</p>
                          <div className="flex gap-2 items-center">
                            <input type="number" min={1} className="w-20 bg-white/5 border border-white/10 rounded px-2 py-1 text-xs text-foreground"
                              value={addQty} onChange={(e) => setAddQty(Math.max(1, parseInt(e.target.value) || 1))} />
                            <span className="text-xs text-muted-foreground">g</span>
                            <button type="button" className="text-xs text-purple-400 hover:text-purple-300"
                              onClick={() => confirmAddFood(mi, meal, pendingFood, addQty)}>Add</button>
                            <button type="button" className="text-xs text-muted-foreground hover:text-foreground"
                              onClick={() => setPendingFood(null)}>Back</button>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            ≈ {fmt((pendingFood.calories_kcal ?? 0) * addQty / 100, 0)} kcal · P {fmt((pendingFood.protein_g ?? 0) * addQty / 100, 1)}g · C {fmt((pendingFood.carbs_g ?? 0) * addQty / 100, 1)}g · F {fmt((pendingFood.fat_g ?? 0) * addQty / 100, 1)}g
                          </p>
                        </div>
                      ) : (
                        <>
                          <input autoFocus type="text" placeholder="Search food database…"
                            className="w-full bg-white/5 border border-white/10 rounded px-2 py-1 text-xs text-foreground"
                            value={searchQ} onChange={(e) => setSearchQ(e.target.value)} />
                          {(searchResults ?? []).length > 0 && (
                            <div className="rounded border border-white/10 bg-background/80 max-h-40 overflow-y-auto">
                              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                              {(searchResults as any[]).map((f: any) => (
                                <button key={f.fdc_id} type="button"
                                  className="w-full text-left px-2 py-1.5 text-xs hover:bg-white/10 flex justify-between gap-2"
                                  onClick={() => { setPendingFood(f); setSearchQ(""); }}>
                                  <span className="truncate">{f.name}</span>
                                  <span className="text-muted-foreground shrink-0">{fmt(f.calories_kcal, 0)} kcal/100g</span>
                                </button>
                              ))}
                            </div>
                          )}
                          <button type="button" className="text-xs text-muted-foreground hover:text-foreground"
                            onClick={() => { setSearchMealIdx(null); setSearchQ(""); }}>Cancel</button>
                        </>
                      )}
                    </div>
                  ) : (
                    <button type="button" className="text-xs text-purple-400 hover:text-purple-300"
                      onClick={() => { setSearchMealIdx(mi); setPendingFood(null); setAddQty(100); }}>
                      + Search &amp; add food
                    </button>
                  )}
                </div>
              ) : (
                <>
                  <p className="text-xs text-muted-foreground">{nm.foods.join(", ")}</p>
                  <div className="flex items-center justify-between mt-1 flex-wrap gap-1">
                    <div className="flex gap-2 flex-wrap">
                      <span className="text-xs text-purple-300">{fmt(nm.calories, 0)} kcal</span>
                      <span className="text-xs text-cyan-300">P {fmt(nm.protein_g, 0)}g</span>
                      <span className="text-xs text-amber-300">C {fmt(nm.carbs_g, 0)}g</span>
                      <span className="text-xs text-pink-300">F {fmt(nm.fat_g, 0)}g</span>
                    </div>
                    <Button size="sm" variant="ghost" className="h-6 px-2 text-xs text-purple-400 hover:text-purple-300" onClick={() => onLogMeal({ ...meal, recId })}>
                      <BookmarkPlus className="h-3 w-3 mr-1" />Log
                    </Button>
                  </div>
                </>
              )}
            </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Tab 2: Food & Meals ─────────────────────────────────────────────────────

interface BuilderItem extends MealItem { _id: string }

function FoodMealsTab() {
  const qc = useQueryClient();
  const [subTab, setSubTab] = useState<"search" | "saved">("search");
  const [query, setQuery] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [addingFood, setAddingFood] = useState<FoodResult | null>(null);
  const [addQty, setAddQty] = useState(100);
  const [builderItems, setBuilderItems] = useState<BuilderItem[]>([]);
  const [mealName, setMealName] = useState("");
  const [savingMeal, setSavingMeal] = useState(false);
  const [logDate, setLogDate] = useState(() => new Date().toISOString().slice(0, 10));

  const { data: goal } = useQuery({ queryKey: ["goal"], queryFn: userApi.getGoal });
  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: userApi.getProfile });
  const { data: scanList } = useQuery({ queryKey: ["scans"], queryFn: scans.list });
  const { data: scanData } = useQuery({ queryKey: ["scan", scanList?.[0]?.id], queryFn: () => scans.get(scanList![0].id), enabled: !!scanList?.[0] });
  const metricsMap = Object.fromEntries((scanData?.metrics ?? []).map((m) => [m.metric_key, m.metric_value]));
  const { data: macros } = useQuery({
    queryKey: ["macros", goal?.goal_type ?? "general_health", profile?.activity_level ?? "moderately_active", scanList?.[0]?.id],
    queryFn: () => recommendations.calculateMacros({ metrics: metricsMap, goal_type: goal?.goal_type ?? "general_health", age: profile?.age ?? undefined, height_cm: profile?.height_cm ?? undefined, gender: profile?.gender ?? undefined, activity_level: profile?.activity_level ?? "moderately_active" }),
    enabled: !!scanData,
  });
  const { data: savedMeals } = useQuery({ queryKey: ["custom-meals"], queryFn: recommendations.listMeals });
  const { data: dayPlans } = useQuery({ queryKey: ["day-plans"], queryFn: recommendations.listDayPlans });
  const deleteDayPlanMutation = useMutation({
    mutationFn: (id: string) => recommendations.deleteDayPlan(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["day-plans"] }),
  });

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(query), 300);
    return () => clearTimeout(t);
  }, [query]);

  const { data: foodResults, isFetching: foodLoading } = useQuery({
    queryKey: ["food-search", debouncedQ],
    queryFn: () => recommendations.searchFood(debouncedQ),
    enabled: debouncedQ.length >= 2,
  });

  const createMealMutation = useMutation({
    mutationFn: () => recommendations.createMeal({ name: mealName, items: builderItems.map(({ _id, ...rest }) => rest) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["custom-meals"] }); setBuilderItems([]); setMealName(""); setSavingMeal(false); },
    onError: () => setSavingMeal(false),
  });

  const deleteMealMutation = useMutation({
    mutationFn: (id: string) => recommendations.deleteMeal(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["custom-meals"] }),
  });

  const { data: foodLogEntries = [] } = useQuery<FoodLogEntryOut[]>({
    queryKey: ["food-log", logDate],
    queryFn: () => recommendations.getFoodLog(logDate),
  });

  const { data: logDates = [] } = useQuery<string[]>({
    queryKey: ["food-log-dates"],
    queryFn: () => recommendations.getFoodLogDates(),
  });

  const createLogMutation = useMutation({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    mutationFn: (payload: any) => recommendations.createFoodLog(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["food-log", logDate] });
      qc.invalidateQueries({ queryKey: ["food-log-dates"] });
    },
  });

  const deleteLogMutation = useMutation({
    mutationFn: (id: string) => recommendations.deleteFoodLogEntry(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["food-log", logDate] });
      qc.invalidateQueries({ queryKey: ["food-log-dates"] });
    },
  });

  const builderTotals = sumMacros(builderItems);

  return (
    <div className="space-y-4">
      {/* Macro Pie Chart + Date Picker */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <MacroPieChart entries={foodLogEntries} macros={macros ?? null} />
        <div className="glass-card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">Food Log</h3>
            <div className="flex items-center gap-2">
              <input type="date" value={logDate} onChange={(e) => setLogDate(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-lg px-2 py-1 text-xs text-foreground" />
              {logDates.length > 0 && <span className="text-xs text-muted-foreground">{logDates.length} days logged</span>}
            </div>
          </div>
          {foodLogEntries.length === 0 ? (
            <p className="text-xs text-muted-foreground py-4 text-center">No foods logged for this date.</p>
          ) : (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {foodLogEntries.map((entry) => (
                <div key={entry.id} className="flex items-center justify-between gap-2 rounded bg-white/5 px-2 py-1.5">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-foreground truncate">{entry.food_name}{entry.brand ? ` · ${entry.brand}` : ""}</p>
                    <p className="text-xs text-muted-foreground">{entry.quantity_g}g · {(entry.calories_kcal ?? 0).toFixed(0)} kcal · P {(entry.protein_g ?? 0).toFixed(1)}g</p>
                  </div>
                  <button onClick={() => deleteLogMutation.mutate(entry.id)} className="text-muted-foreground hover:text-red-400 shrink-0">
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
          {foodLogEntries.length > 0 && (
            <div className="border-t border-white/10 pt-2 text-xs flex gap-3 flex-wrap text-muted-foreground">
              <span>Total: {foodLogEntries.reduce((s, e) => s + (e.calories_kcal ?? 0), 0).toFixed(0)} kcal</span>
              <span className="text-purple-300">P {foodLogEntries.reduce((s, e) => s + (e.protein_g ?? 0), 0).toFixed(1)}g</span>
              <span className="text-cyan-300">C {foodLogEntries.reduce((s, e) => s + (e.carbs_g ?? 0), 0).toFixed(1)}g</span>
              <span className="text-amber-300">F {foodLogEntries.reduce((s, e) => s + (e.fat_g ?? 0), 0).toFixed(1)}g</span>
            </div>
          )}
        </div>
      </div>

      {/* Sub-tabs */}
      <div className="flex gap-1 rounded-lg bg-white/5 p-1 w-fit">
        {(["search","saved"] as const).map((s) => (
          <button key={s} onClick={() => setSubTab(s)} className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${subTab === s ? "bg-purple-600 text-white" : "text-muted-foreground hover:text-foreground"}`}>
            {s === "search" ? "Search & Add" : "My Saved Meals"}
          </button>
        ))}
      </div>

      {subTab === "search" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Left: search */}
          <div className="lg:col-span-2 space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search USDA food database…" className="pl-9 bg-white/5 border-white/10 text-foreground" />
            </div>
            <p className="text-xs text-muted-foreground">Data from USDA FoodData Central (public domain)</p>
            {foodLoading && <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" />Searching…</div>}
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {(foodResults ?? []).map((food) => (
                <div key={food.fdc_id} className="glass-card p-3 space-y-1">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{food.name}</p>
                      {food.brand && <p className="text-xs text-muted-foreground truncate">{food.brand}</p>}
                    </div>
                    <Button size="sm" className="h-7 px-2 btn-primary-glass shrink-0" onClick={() => { setAddingFood(food); setAddQty(food.serving_size ?? 100); }}>
                      <Plus className="h-3 w-3 mr-1" />Add
                    </Button>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <Badge variant="outline" className="text-xs border-purple-500/30 text-purple-300">{fmt(food.calories_kcal, 0)} kcal</Badge>
                    <Badge variant="outline" className="text-xs border-cyan-500/30 text-cyan-300">P {fmt(food.protein_g)}g</Badge>
                    <Badge variant="outline" className="text-xs border-amber-500/30 text-amber-300">C {fmt(food.carbs_g)}g</Badge>
                    <Badge variant="outline" className="text-xs border-pink-500/30 text-pink-300">F {fmt(food.fat_g)}g</Badge>
                  </div>
                  {addingFood?.fdc_id === food.fdc_id && (
                    <div className="mt-2 p-3 rounded-lg bg-white/5 border border-white/10 space-y-2">
                      <div className="flex items-center gap-2">
                        <Label className="text-xs text-muted-foreground w-20">Quantity (g)</Label>
                        <Input type="number" value={addQty} onChange={(e) => setAddQty(Number(e.target.value))} className="h-7 w-24 bg-white/10 border-white/10 text-foreground text-xs" />
                      </div>
                      {(() => { const s = scaleMacros({ ...food, quantity_g: 100, food_name: food.name } as MealItem, addQty); return (
                        <div className="flex gap-2 text-xs flex-wrap">
                          <span className="text-purple-300">{fmt(s.calories_kcal, 0)} kcal</span>
                          <span className="text-cyan-300">P {fmt(s.protein_g)}g</span>
                          <span className="text-amber-300">C {fmt(s.carbs_g)}g</span>
                          <span className="text-pink-300">F {fmt(s.fat_g)}g</span>
                        </div>
                      ); })()}
                      <div className="flex gap-2 flex-wrap">
                        <Button size="sm" className="h-7 text-xs btn-primary-glass" onClick={() => {
                          setBuilderItems((prev) => [...prev, { _id: `${Date.now()}`, fdc_id: food.fdc_id, food_name: food.name, quantity_g: addQty, calories_kcal: food.calories_kcal, protein_g: food.protein_g, carbs_g: food.carbs_g, fat_g: food.fat_g, fiber_g: food.fiber_g }]);
                          setAddingFood(null);
                        }}>Add to Meal</Button>
                        <Button size="sm" variant="outline" className="h-7 text-xs border-purple-500/30 text-purple-300 hover:bg-purple-500/10" onClick={() => {
                          const s = scaleMacros({ ...food, quantity_g: 100, food_name: food.name } as MealItem, addQty);
                          createLogMutation.mutate({ log_date: logDate, entries: [{ fdc_id: food.fdc_id, food_name: food.name, brand: food.brand ?? null, source: "manual", quantity_g: addQty, calories_kcal: s.calories_kcal, protein_g: s.protein_g, carbs_g: s.carbs_g, fat_g: s.fat_g, fiber_g: s.fiber_g }] });
                          setAddingFood(null);
                        }}><BookmarkPlus className="h-3 w-3 mr-1" />Add to Today</Button>
                        <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setAddingFood(null)}>Cancel</Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Right: builder */}
          <div className="glass-card p-4 space-y-3 h-fit sticky top-4">
            <h3 className="text-sm font-semibold text-foreground">Current Meal</h3>
            {builderItems.length === 0 ? (
              <p className="text-xs text-muted-foreground">Add foods from the search results.</p>
            ) : (
              <>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {builderItems.map((item) => {
                    const s = scaleMacros(item, item.quantity_g);
                    return (
                      <div key={item._id} className="flex items-center justify-between gap-2 rounded bg-white/5 px-2 py-1">
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-foreground truncate">{item.food_name}</p>
                          <p className="text-xs text-muted-foreground">{item.quantity_g}g · {fmt(s.calories_kcal, 0)} kcal</p>
                        </div>
                        <button onClick={() => setBuilderItems((p) => p.filter((x) => x._id !== item._id))} className="text-muted-foreground hover:text-red-400"><X className="h-3 w-3" /></button>
                      </div>
                    );
                  })}
                </div>
                <div className="space-y-1.5 pt-1">
                  {macros && <>
                    <MacroBar label="Calories" value={builderTotals.calories_kcal} target={macros.calories} unit=" kcal" color="purple" />
                    <MacroBar label="Protein" value={builderTotals.protein_g} target={macros.protein_g} color="cyan" />
                    <MacroBar label="Carbs" value={builderTotals.carbs_g} target={macros.carbs_g} color="amber" />
                    <MacroBar label="Fat" value={builderTotals.fat_g} target={macros.fat_g} color="pink" />
                  </>}
                </div>
              </>
            )}
            {builderItems.length > 0 && (
              <div className="space-y-2 pt-1">
                <Input value={mealName} onChange={(e) => setMealName(e.target.value)} placeholder="Meal name (e.g. Post-Workout Shake)" className="h-8 bg-white/5 border-white/10 text-foreground text-xs" />
                <div className="flex gap-2">
                  <Button size="sm" className="btn-primary-glass h-7 text-xs flex-1" disabled={!mealName.trim() || createMealMutation.isPending} onClick={() => createMealMutation.mutate()}>
                    {createMealMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3 mr-1" />}Save Meal
                  </Button>
                  <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setBuilderItems([])}><Trash2 className="h-3 w-3" /></Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {subTab === "saved" && (() => {
        const allMeals = savedMeals ?? [];
        const dayPlannerMeals = allMeals.filter((m) => m.name.startsWith("Day Planner \u2014 "));
        const userMeals = allMeals.filter((m) => !m.name.startsWith("Day Planner \u2014 "));

        // Group day planner meals by day number extracted from description "Saved from Day N diet plan"
        const dayGroups: Record<number, typeof dayPlannerMeals> = {};
        dayPlannerMeals.forEach((m) => {
          const match = (m.description ?? "").match(/Saved from Day (\d+)/);
          const dayNum = match ? parseInt(match[1]) : 0;
          if (!dayGroups[dayNum]) dayGroups[dayNum] = [];
          dayGroups[dayNum].push(m);
        });
        const sortedDays = Object.keys(dayGroups).map(Number).sort((a, b) => a - b);

        const makeLogHandler = (meal: typeof allMeals[0]) => () => {
          const entries = meal.items.map((item) => ({
            food_name: item.food_name ?? meal.name,
            source: "saved_meal" as const,
            source_ref_id: meal.id,
            quantity_g: item.quantity_g ?? 100,
            calories_kcal: item.calories_kcal ?? null,
            protein_g: item.protein_g ?? null,
            carbs_g: item.carbs_g ?? null,
            fat_g: item.fat_g ?? null,
            fiber_g: item.fiber_g ?? null,
          }));
          createLogMutation.mutate({ log_date: logDate, entries });
        };

        if (allMeals.length === 0 && (dayPlans ?? []).length === 0) {
          return <p className="text-muted-foreground text-center py-8">No saved meals yet. Build a meal in the search tab or save a generated diet day.</p>;
        }

        return (
          <div className="space-y-4">
            {(dayPlans ?? []).length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-foreground">Generated AI Diet Plans</h3>
                <GeneratedPlansList dayPlans={dayPlans ?? []} onDeleteGroup={(ids) => {
                  const deleteAll = async () => {
                    for (const id of ids) {
                      await recommendations.deleteDayPlan(id);
                    }
                    qc.invalidateQueries({ queryKey: ["day-plans"] });
                  };
                  deleteAll();
                }} />
              </div>
            )}
            {dayPlannerMeals.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-foreground">Day Planner Meals</h3>
                {sortedDays.map((dayNum) => (
                  <div key={dayNum} className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground pl-1">{dayNum > 0 ? `Day ${dayNum}` : "Other"}</p>
                    {dayGroups[dayNum].map((meal) => <SavedMealCard key={meal.id} meal={meal} onDelete={() => deleteMealMutation.mutate(meal.id)} onLogToday={makeLogHandler(meal)} />)}
                  </div>
                ))}
              </div>
            )}
            {userMeals.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-foreground">My Meals</h3>
                {userMeals.map((meal) => <SavedMealCard key={meal.id} meal={meal} onDelete={() => deleteMealMutation.mutate(meal.id)} onLogToday={makeLogHandler(meal)} />)}
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
}

function SavedMealCard({ meal, onDelete, onLogToday }: { meal: CustomMealOut; onDelete: () => void; onLogToday: () => void }) {
  const [open, setOpen] = useState(false);
  const totals = sumMacros(meal.items.map((i) => ({ ...i, food_name: i.food_name ?? "", quantity_g: i.quantity_g ?? 100 })));
  return (
    <div className="glass-card overflow-hidden">
      <div role="button" tabIndex={0} className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors cursor-pointer" onClick={() => setOpen((o) => !o)} onKeyDown={(e) => e.key === "Enter" && setOpen((o) => !o)}>
        <div className="text-left">
          <p className="text-sm font-medium text-foreground">{meal.name}</p>
          <p className="text-xs text-muted-foreground">{meal.items.length} items · {fmt(totals.calories_kcal, 0)} kcal · P {fmt(totals.protein_g)}g · C {fmt(totals.carbs_g)}g · F {fmt(totals.fat_g)}g</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={(e) => { e.stopPropagation(); onLogToday(); }} className="text-purple-400 hover:text-purple-300 p-1" title="Add to Today"><BookmarkPlus className="h-3.5 w-3.5" /></button>
          <button onClick={(e) => { e.stopPropagation(); onDelete(); }} className="text-muted-foreground hover:text-red-400 p-1"><Trash2 className="h-3.5 w-3.5" /></button>
          {open ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </div>
      {open && (
        <div className="px-3 pb-3 space-y-1">
          {meal.items.map((item, i) => {
            const s = scaleMacros({ ...item, food_name: item.food_name ?? "", quantity_g: item.quantity_g ?? 100 }, item.quantity_g ?? 100);
            return (
              <div key={i} className="flex justify-between text-xs rounded bg-white/5 px-2 py-1">
                <span className="text-foreground">{item.food_name} <span className="text-muted-foreground">({item.quantity_g}g)</span></span>
                <span className="text-muted-foreground">{fmt(s.calories_kcal, 0)} kcal · P {fmt(s.protein_g)}g</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Tab 3: Day Planner ───────────────────────────────────────────────────────

const MEAL_SLOTS = ["breakfast", "lunch", "dinner", "snack"] as const;

function DayPlannerTab() {
  const qc = useQueryClient();
  const [planName, setPlanName] = useState("");
  const [planDate, setPlanDate] = useState("");
  const [slots, setSlots] = useState<Record<string, string | null>>({ breakfast: null, lunch: null, dinner: null, snack: null });

  const { data: savedMeals } = useQuery({ queryKey: ["custom-meals"], queryFn: recommendations.listMeals });
  const { data: dayPlans } = useQuery({ queryKey: ["day-plans"], queryFn: recommendations.listDayPlans });
  const { data: goal } = useQuery({ queryKey: ["goal"], queryFn: userApi.getGoal });
  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: userApi.getProfile });
  const { data: scanList } = useQuery({ queryKey: ["scans"], queryFn: scans.list });
  const { data: scanData } = useQuery({ queryKey: ["scan", scanList?.[0]?.id], queryFn: () => scans.get(scanList![0].id), enabled: !!scanList?.[0] });
  const metricsMap = Object.fromEntries((scanData?.metrics ?? []).map((m) => [m.metric_key, m.metric_value]));
  const { data: macros } = useQuery({
    queryKey: ["macros", goal?.goal_type ?? "general_health", "moderate", scanList?.[0]?.id],
    queryFn: () => recommendations.calculateMacros({ metrics: metricsMap, goal_type: goal?.goal_type ?? "general_health", age: profile?.age ?? undefined, height_cm: profile?.height_cm ?? undefined, gender: profile?.gender ?? undefined }),
    enabled: !!scanData,
  });

  const createMutation = useMutation({
    mutationFn: () => {
      const entries = MEAL_SLOTS.filter((s) => slots[s]).map((slot) => {
        const meal = savedMeals?.find((m) => m.id === slots[slot]);
        const totals = meal ? sumMacros(meal.items.map((i) => ({ ...i, food_name: i.food_name ?? "", quantity_g: i.quantity_g ?? 100 }))) : {};
        return {
          meal_slot: slot,
          custom_meal_id: slots[slot],
          custom_meal_name: meal?.name ?? null,
          calories_kcal: (totals as { calories_kcal?: number }).calories_kcal ?? null,
          protein_g: (totals as { protein_g?: number }).protein_g ?? null,
          carbs_g: (totals as { carbs_g?: number }).carbs_g ?? null,
          fat_g: (totals as { fat_g?: number }).fat_g ?? null,
          fiber_g: (totals as { fiber_g?: number }).fiber_g ?? null,
        };
      });
      return recommendations.createDayPlan({ name: planName, plan_date: planDate || undefined, entries });
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["day-plans"] }); setPlanName(""); setSlots({ breakfast: null, lunch: null, dinner: null, snack: null }); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => recommendations.deleteDayPlan(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["day-plans"] }),
  });

  const applyPlanMutation = useMutation({
    mutationFn: (plan: DayPlanOut) => {
      const today = new Date().toISOString().slice(0, 10);
      const entries = (plan.entries ?? []).flatMap((e) =>
        (e.items_snapshot ?? []).length > 0
          ? (e.items_snapshot!).map((item) => ({
              food_name: item.food_name,
              source: "day_plan" as const,
              source_ref_id: plan.id,
              quantity_g: item.quantity_g ?? 100,
              calories_kcal: item.calories_kcal ?? null,
              protein_g: item.protein_g ?? null,
              carbs_g: item.carbs_g ?? null,
              fat_g: item.fat_g ?? null,
              fiber_g: item.fiber_g ?? null,
            }))
          : [{
              food_name: e.custom_meal_name ?? e.meal_slot,
              source: "day_plan" as const,
              source_ref_id: plan.id,
              quantity_g: 100,
              calories_kcal: e.calories_kcal ?? null,
              protein_g: e.protein_g ?? null,
              carbs_g: e.carbs_g ?? null,
              fat_g: e.fat_g ?? null,
              fiber_g: e.fiber_g ?? null,
            }]
      );
      return recommendations.createFoodLog({ log_date: today, entries });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["food-log"] }),
  });

  // Running totals
  const planTotals = MEAL_SLOTS.reduce((acc, slot) => {
    const meal = savedMeals?.find((m) => m.id === slots[slot]);
    if (!meal) return acc;
    const t = sumMacros(meal.items.map((i) => ({ ...i, food_name: i.food_name ?? "", quantity_g: i.quantity_g ?? 100 })));
    return { calories_kcal: acc.calories_kcal + t.calories_kcal, protein_g: acc.protein_g + t.protein_g, carbs_g: acc.carbs_g + t.carbs_g, fat_g: acc.fat_g + t.fat_g, fiber_g: acc.fiber_g + t.fiber_g };
  }, { calories_kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 });

  return (
    <div className="space-y-6">
      <div className="glass-card p-5 space-y-4">
        <h2 className="text-sm font-semibold text-foreground">New Day Plan</h2>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Plan Name</Label>
            <Input value={planName} onChange={(e) => setPlanName(e.target.value)} placeholder="e.g. High Protein Monday" className="bg-white/5 border-white/10 text-foreground" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Date (optional)</Label>
            <Input type="date" value={planDate} onChange={(e) => setPlanDate(e.target.value)} className="bg-white/5 border-white/10 text-foreground" />
          </div>
        </div>
        <div className="space-y-3">
          {MEAL_SLOTS.map((slot) => {
            const meal = savedMeals?.find((m) => m.id === slots[slot]);
            const t = meal ? sumMacros(meal.items.map((i) => ({ ...i, food_name: i.food_name ?? "", quantity_g: i.quantity_g ?? 100 }))) : null;
            return (
              <div key={slot} className="rounded-lg bg-white/5 p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-xs text-purple-300">{slot.charAt(0).toUpperCase() + slot.slice(1)}</Label>
                  {slots[slot] && <button onClick={() => setSlots((p) => ({ ...p, [slot]: null }))} className="text-muted-foreground hover:text-red-400"><X className="h-3 w-3" /></button>}
                </div>
                <MealSelectorWidget
                  value={slots[slot]}
                  onChange={(id) => setSlots((p) => ({ ...p, [slot]: id }))}
                  savedMeals={savedMeals ?? []}
                  savedDays={dayPlans ?? []}
                />
                {t && <p className="text-xs text-muted-foreground">{fmt(t.calories_kcal, 0)} kcal · P {fmt(t.protein_g)}g · C {fmt(t.carbs_g)}g · F {fmt(t.fat_g)}g</p>}
              </div>
            );
          })}
        </div>
        {macros && (
          <div className="space-y-1.5 pt-1">
            <p className="text-xs text-muted-foreground font-medium">Daily totals vs targets</p>
            <MacroBar label="Calories" value={planTotals.calories_kcal} target={macros.calories} unit=" kcal" color="purple" />
            <MacroBar label="Protein" value={planTotals.protein_g} target={macros.protein_g} color="cyan" />
            <MacroBar label="Carbs" value={planTotals.carbs_g} target={macros.carbs_g} color="amber" />
            <MacroBar label="Fat" value={planTotals.fat_g} target={macros.fat_g} color="pink" />
          </div>
        )}
        <Button className="btn-primary-glass" disabled={!planName.trim() || createMutation.isPending} onClick={() => createMutation.mutate()}>
          {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Calendar className="h-4 w-4 mr-2" />}Save Day Plan
        </Button>
      </div>

      {(dayPlans ?? []).length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Saved Day Plans</h2>
          {(dayPlans ?? []).map((plan) => <DayPlanCard key={plan.id} plan={plan} onDelete={() => deleteMutation.mutate(plan.id)} onApply={() => applyPlanMutation.mutate(plan)} />)}
        </div>
      )}
    </div>
  );
}

function DayPlanCard({ plan, onDelete, onApply }: { plan: DayPlanOut; onDelete: () => void; onApply?: () => void }) {
  const [open, setOpen] = useState(false);
  const total = plan.entries.reduce((a, e) => ({ calories: a.calories + (e.calories_kcal ?? 0), protein: a.protein + (e.protein_g ?? 0) }), { calories: 0, protein: 0 });
  return (
    <div className="glass-card overflow-hidden">
      <div className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors cursor-pointer" onClick={() => setOpen((o) => !o)} role="button" tabIndex={0} onKeyDown={(e) => e.key === "Enter" && setOpen((o) => !o)}>
        <div className="text-left">
          <p className="text-sm font-medium text-foreground">{plan.name}</p>
          <p className="text-xs text-muted-foreground">{plan.plan_date ?? "No date"} · {fmt(total.calories, 0)} kcal · P {fmt(total.protein)}g</p>
        </div>
        <div className="flex items-center gap-2">
          {onApply && <button type="button" onClick={(e) => { e.stopPropagation(); onApply(); }} className="text-purple-400 hover:text-purple-300 p-1" title="Log to today"><BookmarkPlus className="h-3.5 w-3.5" /></button>}
          <button type="button" onClick={(e) => { e.stopPropagation(); onDelete(); }} className="text-muted-foreground hover:text-red-400 p-1"><Trash2 className="h-3.5 w-3.5" /></button>
          {open ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </div>
      {open && (
        <div className="px-3 pb-3 space-y-1">
          {plan.entries.map((e, i) => (
            <div key={i} className="flex justify-between text-xs rounded bg-white/5 px-2 py-1">
              <span className="capitalize text-purple-300">{e.meal_slot}</span>
              <span className="text-muted-foreground">{e.custom_meal_name ?? "—"}</span>
              <span className="text-muted-foreground">{fmt(e.calories_kcal, 0)} kcal</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Generated Plans List (grouped by recommendation ID) ─────────────────────

function GeneratedPlansList({ dayPlans, onDeleteGroup }: { dayPlans: DayPlanOut[]; onDeleteGroup: (ids: string[]) => void }) {
  // Group by notes (recommendation_id). Plans without notes go into "__manual__".
  const groups = new Map<string, DayPlanOut[]>();
  for (const plan of dayPlans) {
    const key = plan.notes ?? "__manual__";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(plan);
  }
  // Sort groups: AI plans (notes = rec UUID) newest first; manual group last
  const sortedKeys = Array.from(groups.keys()).sort((a, b) => {
    if (a === "__manual__") return 1;
    if (b === "__manual__") return -1;
    const aDate = groups.get(a)![0]?.created_at ?? "";
    const bDate = groups.get(b)![0]?.created_at ?? "";
    return bDate < aDate ? -1 : 1;
  });

  return (
    <div className="space-y-3">
      {sortedKeys.map((key) => {
        const plans = groups.get(key)!;
        // Sort days within the group by day number extracted from name
        const sorted = [...plans].sort((a, b) => {
          const da = parseInt(a.name.match(/\(Day (\d+)\)/)?.[1] ?? "0");
          const db = parseInt(b.name.match(/\(Day (\d+)\)/)?.[1] ?? "0");
          return da - db;
        });
        const label = key === "__manual__"
          ? "Manually saved plans"
          : (() => {
              const d = sorted[0]?.created_at ? new Date(sorted[0].created_at) : null;
              return d ? d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }) : "Generated plan";
            })();
        const totalCal = sorted.reduce((acc, p) => acc + p.entries.reduce((s, e) => s + (e.calories_kcal ?? 0), 0), 0) / Math.max(sorted.length, 1);
        return (
          <GeneratedPlanBlock
            key={key}
            label={label}
            days={sorted}
            totalCalPerDay={totalCal}
            onDelete={() => onDeleteGroup(plans.map((p) => p.id))}
          />
        );
      })}
    </div>
  );
}

function GeneratedPlanBlock({ label, days, totalCalPerDay, onDelete }: {
  label: string;
  days: DayPlanOut[];
  totalCalPerDay: number;
  onDelete: () => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="glass-card overflow-hidden">
      <div className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors cursor-pointer" role="button" tabIndex={0} onClick={() => setOpen((o) => !o)} onKeyDown={(e) => e.key === "Enter" && setOpen((o) => !o)}>
        <div className="text-left">
          <p className="text-sm font-medium text-foreground">{label}</p>
          <p className="text-xs text-muted-foreground">{days.length} days · ~{fmt(totalCalPerDay, 0)} kcal/day</p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={(e) => { e.stopPropagation(); onDelete(); }} className="text-muted-foreground hover:text-red-400 p-1" title="Delete plan"><Trash2 className="h-3.5 w-3.5" /></button>
          {open ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </div>
      {open && (
        <div className="border-t border-white/10">
          {days.map((plan) => <GeneratedDayRow key={plan.id} plan={plan} />)}
        </div>
      )}
    </div>
  );
}

function GeneratedDayRow({ plan }: { plan: DayPlanOut }) {
  const [open, setOpen] = useState(false);
  const dayNum = plan.name.match(/\(Day (\d+)\)/)?.[1] ?? "?";
  const dayTotals = plan.entries.reduce(
    (acc, e) => ({
      calories: acc.calories + (e.calories_kcal ?? 0),
      protein_g: acc.protein_g + (e.protein_g ?? 0),
      carbs_g: acc.carbs_g + (e.carbs_g ?? 0),
      fat_g: acc.fat_g + (e.fat_g ?? 0),
    }),
    { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 }
  );
  return (
    <div className="border-b border-white/5 last:border-b-0">
      <div className="flex items-center justify-between px-4 py-2 cursor-pointer hover:bg-white/5" role="button" tabIndex={0} onClick={() => setOpen((o) => !o)} onKeyDown={(e) => e.key === "Enter" && setOpen((o) => !o)}>
        <span className="text-sm text-cyan-300 font-medium">Day {dayNum}</span>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>{fmt(dayTotals.calories, 0)} kcal</span>
          <span>P {fmt(dayTotals.protein_g)}g</span>
          <span>C {fmt(dayTotals.carbs_g)}g</span>
          <span>F {fmt(dayTotals.fat_g)}g</span>
          {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </div>
      </div>
      {open && (
        <div className="px-4 pb-3 space-y-2">
          {plan.entries.map((entry, i) => (
            <GeneratedMealRow key={i} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}

function GeneratedMealRow({ entry }: { entry: DayPlanOut["entries"][number] }) {
  const [open, setOpen] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items: any[] = Array.isArray(entry.items_snapshot) ? entry.items_snapshot : [];
  return (
    <div className="rounded bg-white/5 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 cursor-pointer hover:bg-white/5" role="button" tabIndex={0} onClick={() => setOpen((o) => !o)} onKeyDown={(e) => e.key === "Enter" && setOpen((o) => !o)}>
        <span className="text-xs capitalize text-purple-300 font-medium">{entry.meal_slot}</span>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{fmt(entry.calories_kcal, 0)} kcal</span>
          <span>P {fmt(entry.protein_g)}g</span>
          <span>C {fmt(entry.carbs_g)}g</span>
          <span>F {fmt(entry.fat_g)}g</span>
          {items.length > 0 && (open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
        </div>
      </div>
      {open && items.length > 0 && (
        <div className="px-3 pb-2 space-y-1">
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {items.map((item: any, i: number) => (
            <div key={i} className="flex justify-between text-xs px-2 py-0.5 rounded bg-white/5">
              <span className="text-foreground">{item.food_name} <span className="text-muted-foreground">({fmt(item.grams, 0)}g)</span></span>
              <span className="text-muted-foreground">{fmt(item.calories, 0)} kcal · P {fmt(item.protein_g)}g</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Tab 4: Workout ───────────────────────────────────────────────────────────

const DAYS_OF_WEEK = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];

interface LocalDay { label: string; focus: string; isRest: boolean; exercises: { id: string; name: string; sets: string; reps: string; weight: string; rest: string; notes: string }[] }

function WorkoutTab() {
  const qc = useQueryClient();
  const [subTab, setSubTab] = useState<"split" | "ai">("split");
  const [splitName, setSplitName] = useState("");
  const [splitDesc, setSplitDesc] = useState("");
  const [days, setDays] = useState<LocalDay[]>([
    { label: "Monday", focus: "", isRest: false, exercises: [] },
    { label: "Tuesday", focus: "", isRest: false, exercises: [] },
    { label: "Wednesday", focus: "", isRest: true, exercises: [] },
    { label: "Thursday", focus: "", isRest: false, exercises: [] },
    { label: "Friday", focus: "", isRest: false, exercises: [] },
    { label: "Saturday", focus: "", isRest: false, exercises: [] },
    { label: "Sunday", focus: "", isRest: true, exercises: [] },
  ]);
  const [liveScore, setLiveScore] = useState<WorkoutScore | null>(null);
  const [editingWorkoutId, setEditingWorkoutId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [editedWorkout, setEditedWorkout] = useState<any>(null);
  const [confirmOverwriteWorkout, setConfirmOverwriteWorkout] = useState(false);
  const [deletingWorkoutId, setDeletingWorkoutId] = useState<string | null>(null);
  const scoreDebounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const { data: splits } = useQuery({ queryKey: ["splits"], queryFn: recommendations.listSplits });
  const { data: workoutRecs } = useQuery({ queryKey: ["workout-recs"], queryFn: recommendations.listWorkout });
  const { data: scanList } = useQuery({ queryKey: ["scans"], queryFn: scans.list });
  const { data: scanData } = useQuery({ queryKey: ["scan", scanList?.[0]?.id], queryFn: () => scans.get(scanList![0].id), enabled: !!scanList?.[0] });
  const { data: goal } = useQuery({ queryKey: ["goal"], queryFn: userApi.getGoal });
  const metricsMap = Object.fromEntries((scanData?.metrics ?? []).map((m) => [m.metric_key, m.metric_value]));

  const createSplitMutation = useMutation({
    mutationFn: () => recommendations.createSplit({
      name: splitName, description: splitDesc || undefined,
      days: days.map((d) => ({
        day_label: d.label, focus: d.focus || undefined, is_rest: d.isRest,
        exercises: d.isRest ? [] : d.exercises.map((e) => ({
          exercise_name: e.name, sets: parseInt(e.sets) || undefined,
          reps: e.reps || undefined, weight_kg: parseFloat(e.weight) || undefined,
          rest_seconds: parseInt(e.rest) || undefined, notes: e.notes || undefined,
        })),
      })),
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["splits"] }); setSplitName(""); setSplitDesc(""); },
  });

  const deleteSplitMutation = useMutation({
    mutationFn: (id: string) => recommendations.deleteSplit(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["splits"] }),
  });

  const generateWorkoutMutation = useMutation({
    mutationFn: () => recommendations.generateWorkout({ scan_id: scanList![0].id, metrics: metricsMap, goal_type: goal?.goal_type ?? "general_health" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workout-recs"] }),
  });

  const editWorkoutMutation = useMutation({
    mutationFn: ({ id, plan }: { id: string; plan: Record<string, unknown> }) => recommendations.editWorkoutPlan(id, plan),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["workout-recs"] }); setEditingWorkoutId(null); },
  });

  const deleteWorkoutMutation = useMutation({
    mutationFn: (id: string) => recommendations.deleteWorkout(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["workout-recs"] }); setDeletingWorkoutId(null); },
  });

  // Live score debounce
  useEffect(() => {
    clearTimeout(scoreDebounce.current);
    scoreDebounce.current = setTimeout(async () => {
      try {
        const score = await recommendations.scoreSplit({
          name: splitName || "preview",
          days: days.map((d) => ({
            day_label: d.label, focus: d.focus || undefined, is_rest: d.isRest,
            exercises: d.exercises.map((e) => ({ exercise_name: e.name, sets: parseInt(e.sets) || undefined, reps: e.reps || undefined })),
          })),
        });
        setLiveScore(score);
      } catch {}
    }, 700);
  }, [days, splitName]);

  const addExercise = (di: number) => setDays((prev) => prev.map((d, i) => i !== di ? d : { ...d, exercises: [...d.exercises, { id: `${Date.now()}`, name: "", sets: "3", reps: "8-12", weight: "", rest: "90", notes: "" }] }));
  const removeExercise = (di: number, eid: string) => setDays((prev) => prev.map((d, i) => i !== di ? d : { ...d, exercises: d.exercises.filter((e) => e.id !== eid) }));
  const updateExercise = (di: number, eid: string, field: string, val: string) => setDays((prev) => prev.map((d, i) => i !== di ? d : { ...d, exercises: d.exercises.map((e) => e.id !== eid ? e : { ...e, [field]: val }) }));
  const updateDay = (di: number, field: string, val: unknown) => setDays((prev) => prev.map((d, i) => i !== di ? d : { ...d, [field]: val }));

  return (
    <div className="space-y-4">
      <div className="flex gap-1 rounded-lg bg-white/5 p-1 w-fit">
        {(["split","ai"] as const).map((s) => (
          <button key={s} onClick={() => setSubTab(s)} className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${subTab === s ? "bg-purple-600 text-white" : "text-muted-foreground hover:text-foreground"}`}>
            {s === "split" ? "My Workout Split" : "AI Generated Plans"}
          </button>
        ))}
      </div>

      {subTab === "split" && (
        <div className="space-y-4">
          {/* Score preview */}
          {liveScore && (
            <div className="glass-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground">Split Quality Score</h3>
                <div className="flex items-center gap-2">
                  <span className={`text-2xl font-bold ${liveScore.overall >= 80 ? "text-green-400" : liveScore.overall >= 60 ? "text-cyan-400" : liveScore.overall >= 40 ? "text-amber-400" : "text-red-400"}`}>{liveScore.overall}</span>
                  <span className="text-sm text-muted-foreground">/ 100 · {liveScore.label}</span>
                </div>
              </div>
              <div className="grid grid-cols-5 gap-2 text-center">
                {[["Coverage",liveScore.coverage_score,25,"purple"],["Volume",liveScore.volume_score,30,"cyan"],["Balance",liveScore.balance_score,20,"amber"],["Cardio",liveScore.cardio_score,15,"pink"],["Frequency",liveScore.frequency_score,10,"green"]].map(([label, val, max, color]) => (
                  <div key={label as string} className={`rounded-lg bg-white/5 p-2 border border-${color}-500/20`}>
                    <p className="text-xs text-muted-foreground">{label as string}</p>
                    <p className={`text-sm font-bold text-${color}-300`}>{val as number}/{max as number}</p>
                  </div>
                ))}
              </div>
              {liveScore.missing_groups.length > 0 && (
                <div className="flex gap-1 flex-wrap">
                  {liveScore.missing_groups.map((g) => <Badge key={g} variant="outline" className="text-xs border-red-500/30 text-red-400">Missing: {g}</Badge>)}
                </div>
              )}
              <ul className="space-y-1">
                {liveScore.feedback.map((f, i) => <li key={i} className="text-xs text-muted-foreground flex gap-1.5"><span className="text-amber-400 shrink-0">·</span>{f}</li>)}
              </ul>
            </div>
          )}

          {/* Builder */}
          <div className="glass-card p-4 space-y-4">
            <h2 className="text-sm font-semibold text-foreground">Build Your Split</h2>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Split Name</Label>
                <Input value={splitName} onChange={(e) => setSplitName(e.target.value)} placeholder="e.g. PPL Split" className="bg-white/5 border-white/10 text-foreground" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Description (optional)</Label>
                <Input value={splitDesc} onChange={(e) => setSplitDesc(e.target.value)} placeholder="Notes about your split" className="bg-white/5 border-white/10 text-foreground" />
              </div>
            </div>
            {days.map((day, di) => (
              <div key={di} className="rounded-lg bg-white/5 p-3 space-y-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <select value={day.label} onChange={(e) => updateDay(di, "label", e.target.value)} className="bg-white/10 border border-white/10 rounded px-2 py-1 text-xs text-foreground">
                    {DAYS_OF_WEEK.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                  <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer">
                    <input type="checkbox" checked={day.isRest} onChange={(e) => updateDay(di, "isRest", e.target.checked)} className="rounded" />
                    Rest day
                  </label>
                  {!day.isRest && (
                    <Input value={day.focus} onChange={(e) => updateDay(di, "focus", e.target.value)} placeholder="Focus (e.g. Push, Legs)" className="h-7 flex-1 min-w-32 bg-white/10 border-white/10 text-foreground text-xs" />
                  )}
                </div>
                {!day.isRest && (
                  <div className="space-y-1.5">
                    {day.exercises.map((ex, exI) => (
                      <div key={ex.id} className="space-y-1">
                        {exI === 0 && (
                          <div className="grid grid-cols-12 gap-1">
                            <Label className="col-span-4 text-xs text-muted-foreground">Exercise</Label>
                            <Label className="col-span-1 text-xs text-muted-foreground">Sets</Label>
                            <Label className="col-span-2 text-xs text-muted-foreground">Reps</Label>
                            <Label className="col-span-2 text-xs text-muted-foreground">Weight (kg)</Label>
                            <Label className="col-span-2 text-xs text-muted-foreground">Rest (s)</Label>
                          </div>
                        )}
                        <div className="grid grid-cols-12 gap-1 items-center">
                          <Input value={ex.name} onChange={(e) => updateExercise(di, ex.id, "name", e.target.value)} placeholder="Search exercise…" className="col-span-4 h-7 bg-white/10 border-white/10 text-foreground text-xs" />
                          <Input value={ex.sets} onChange={(e) => updateExercise(di, ex.id, "sets", e.target.value)} placeholder="e.g. 3" className="col-span-1 h-7 bg-white/10 border-white/10 text-foreground text-xs" />
                          <Input value={ex.reps} onChange={(e) => updateExercise(di, ex.id, "reps", e.target.value)} placeholder="e.g. 8-12" className="col-span-2 h-7 bg-white/10 border-white/10 text-foreground text-xs" />
                          <Input value={ex.weight} onChange={(e) => updateExercise(di, ex.id, "weight", e.target.value)} placeholder="e.g. 60" className="col-span-2 h-7 bg-white/10 border-white/10 text-foreground text-xs" />
                          <Input value={ex.rest} onChange={(e) => updateExercise(di, ex.id, "rest", e.target.value)} placeholder="e.g. 60" className="col-span-2 h-7 bg-white/10 border-white/10 text-foreground text-xs" />
                          <button onClick={() => removeExercise(di, ex.id)} aria-label="Remove exercise" className="col-span-1 text-muted-foreground hover:text-red-400 flex justify-center"><X className="h-3.5 w-3.5" /></button>
                        </div>
                      </div>
                    ))}
                    <button onClick={() => addExercise(di)} className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 mt-1">
                      <Plus className="h-3 w-3" />Add exercise
                    </button>
                  </div>
                )}
              </div>
            ))}
            <Button className="btn-primary-glass" disabled={!splitName.trim() || createSplitMutation.isPending} onClick={() => createSplitMutation.mutate()}>
              {createSplitMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}Save Split
            </Button>
          </div>

          {/* Saved splits */}
          {(splits ?? []).length > 0 && (
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Saved Splits</h2>
              {(splits ?? []).map((split) => <SplitCard key={split.id} split={split} onDelete={() => deleteSplitMutation.mutate(split.id)} />)}
            </div>
          )}
        </div>
      )}

      {subTab === "ai" && (
        <div className="space-y-4">
          <div className="glass-card p-4 space-y-3">
            {generateWorkoutMutation.error && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-4 py-2 text-sm text-destructive flex items-center justify-between gap-2">
                <span>{"Service is currently busy — please try again in a few moments."}</span>
                <Button size="sm" variant="ghost" className="h-7 text-xs shrink-0 text-destructive hover:text-destructive" onClick={() => generateWorkoutMutation.mutate()}>Try Again</Button>
              </div>
            )}
            {confirmOverwriteWorkout && (
              <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 px-4 py-3 text-sm text-amber-300 space-y-2">
                <p>This will replace your existing workout plan. Continue?</p>
                <div className="flex gap-2">
                  <Button size="sm" className="h-7 text-xs btn-primary-glass" onClick={() => { setConfirmOverwriteWorkout(false); generateWorkoutMutation.mutate(); }}>Yes, replace</Button>
                  <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setConfirmOverwriteWorkout(false)}>Cancel</Button>
                </div>
              </div>
            )}
            {!confirmOverwriteWorkout && (
              <Button onClick={() => { if ((workoutRecs ?? []).length > 0) { setConfirmOverwriteWorkout(true); } else { generateWorkoutMutation.mutate(); } }} disabled={generateWorkoutMutation.isPending || !scanList?.[0]} className="flex items-center gap-2 border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/10" variant="outline">
                {generateWorkoutMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" />Generating…</> : <><Dumbbell className="h-4 w-4" />Generate Weekly Workout Plan</>}
              </Button>
            )}
            {generateWorkoutMutation.isPending && <p className="text-xs text-muted-foreground animate-pulse">Gemini AI is building your program (~10s)…</p>}
          </div>
          {(workoutRecs ?? []).length === 0 && !generateWorkoutMutation.isPending && (
            <p className="text-muted-foreground text-center py-8">No workout plans yet. Generate one above.</p>
          )}
          {(workoutRecs ?? []).map((rec) => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const active = (rec.edited_plan ?? rec.structured_plan) as any;
            const isEditing = editingWorkoutId === rec.id;
            const isDeleting = deletingWorkoutId === rec.id;
            const plan = isEditing ? editedWorkout : active;
            return (
              <div key={rec.id}>
                <WorkoutPlanCard rec={rec} plan={plan} isEditing={isEditing}
                  onEdit={() => { setEditingWorkoutId(rec.id); setEditedWorkout(JSON.parse(JSON.stringify(active))); }}
                  onCancelEdit={() => setEditingWorkoutId(null)}
                  onSaveEdit={() => {
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    const parsedPlan = JSON.parse(JSON.stringify(editedWorkout));
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    (parsedPlan?.days ?? parsedPlan?.weeks?.[0]?.days ?? []).forEach((d: any) => (d.exercises ?? []).forEach((ex: any) => { ex.sets = parseInt(String(ex.sets)) || undefined; }));
                    editWorkoutMutation.mutate({ id: rec.id, plan: parsedPlan });
                  }}
                  onPlanChange={setEditedWorkout} saving={editWorkoutMutation.isPending}
                  onDelete={() => setDeletingWorkoutId(rec.id)}
                />
                {isDeleting && (
                  <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-300 space-y-2 mt-1">
                    <p>Delete this workout plan? This cannot be undone.</p>
                    <div className="flex gap-2">
                      <Button size="sm" className="h-7 text-xs bg-red-500/20 border border-red-500/30 text-red-300 hover:bg-red-500/30" onClick={() => deleteWorkoutMutation.mutate(rec.id)} disabled={deleteWorkoutMutation.isPending}>
                        {deleteWorkoutMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : "Delete"}
                      </Button>
                      <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setDeletingWorkoutId(null)}>Cancel</Button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function SplitCard({ split, onDelete }: { split: WorkoutSplitOut; onDelete: () => void }) {
  const [open, setOpen] = useState(false);
  const score = split.score;
  const scoreColor = !score ? "text-muted-foreground" : score.overall >= 80 ? "text-green-400" : score.overall >= 60 ? "text-cyan-400" : score.overall >= 40 ? "text-amber-400" : "text-red-400";
  return (
    <div className="glass-card overflow-hidden">
      <button className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors" onClick={() => setOpen((o) => !o)}>
        <div className="text-left">
          <p className="text-sm font-medium text-foreground">{split.name}</p>
          {split.description && <p className="text-xs text-muted-foreground">{split.description}</p>}
        </div>
        <div className="flex items-center gap-2">
          {score && <span className={`text-lg font-bold ${scoreColor}`}>{score.overall}<span className="text-xs text-muted-foreground">/100</span></span>}
          <button onClick={(e) => { e.stopPropagation(); onDelete(); }} className="text-muted-foreground hover:text-red-400 p-1"><Trash2 className="h-3.5 w-3.5" /></button>
          {open ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </button>
      {open && score && (
        <div className="px-3 pb-3 space-y-3">
          <div className="grid grid-cols-5 gap-1 text-center">
            {[["Coverage",score.coverage_score,25,"purple"],["Volume",score.volume_score,30,"cyan"],["Balance",score.balance_score,20,"amber"],["Cardio",score.cardio_score,15,"pink"],["Freq",score.frequency_score,10,"green"]].map(([l,v,m,c]) => (
              <div key={l as string} className="rounded bg-white/5 p-1.5"><p className="text-xs text-muted-foreground">{l as string}</p><p className={`text-xs font-bold text-${c}-300`}>{v as number}/{m as number}</p></div>
            ))}
          </div>
          {score.feedback.map((f, i) => <p key={i} className="text-xs text-muted-foreground">· {f}</p>)}
          {split.days.map((d, di) => (
            <div key={di} className={`rounded bg-white/5 p-2 ${d.is_rest ? "opacity-50" : ""}`}>
              <p className="text-xs font-medium text-cyan-300">{d.day_label}{d.focus ? ` — ${d.focus}` : ""}{d.is_rest ? " (Rest)" : ""}</p>
              {d.exercises?.map((e, ei) => (
                <div key={ei} className="text-xs ml-2">
                  <p className="text-foreground">· {e.exercise_name}</p>
                  <p className="text-muted-foreground ml-2">
                    {e.sets != null ? `Sets: ${e.sets}` : "Sets: —"}
                    {e.reps ? ` · Reps: ${e.reps}` : " · Reps: —"}
                    {e.weight_kg ? ` · Weight: ${e.weight_kg} kg` : ""}
                    {e.rest_seconds ? ` · Rest: ${e.rest_seconds} s` : ""}
                  </p>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ExerciseTypeahead({ value, onChange }: { value: string; onChange: (name: string) => void }) {
  const [q, setQ] = useState(value);
  const [open, setOpen] = useState(false);
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const [results, setResults] = useState<ExerciseSearchResult[]>([]);

  useEffect(() => { setQ(value); }, [value]);

  const handleChange = (v: string) => {
    setQ(v);
    onChange(v);
    clearTimeout(debounce.current);
    if (v.trim().length < 2) { setResults([]); setOpen(false); return; }
    debounce.current = setTimeout(async () => {
      try {
        const res = await recommendations.searchExercises(v.trim(), 8);
        setResults(res);
        setOpen(res.length > 0);
      } catch { setResults([]); setOpen(false); }
    }, 300);
  };

  return (
    <div className="relative col-span-5">
      <Input
        value={q}
        onChange={(e) => handleChange(e.target.value)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder="Exercise name"
        className="h-7 bg-white/10 border-white/10 text-foreground text-xs w-full"
      />
      {open && (
        <div className="absolute z-50 top-full left-0 w-full max-h-40 overflow-y-auto rounded-lg bg-[#1a1a2e] border border-white/10 shadow-xl">
          {results.map((r) => (
            <button
              key={r.name}
              type="button"
              onMouseDown={() => { onChange(r.name); setQ(r.name); setOpen(false); }}
              className="w-full text-left px-2 py-1.5 hover:bg-white/10 text-xs text-foreground"
            >
              <span className="font-medium">{r.name}</span>
              <span className="text-muted-foreground ml-1">· {r.category}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function WorkoutPlanCard({
  rec, plan, isEditing, onEdit, onCancelEdit, onSaveEdit, onPlanChange, saving, onDelete,
}: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  rec: WorkoutRecommendation; plan: any; isEditing: boolean;
  onEdit: () => void; onCancelEdit: () => void; onSaveEdit: () => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onPlanChange: (p: any) => void; saving: boolean; onDelete?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [liveScore, setLiveScore] = useState<number | null>(null);
  const originalScoreRef = useRef<number | null>(null);
  const [setsError, setSetsError] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function getPlanDays(p: any): any[] {
    return p?.days ?? p?.weeks?.[0]?.days ?? [];
  }

  // Compute score client-side whenever plan changes
  useEffect(() => {
    if (!plan) return;
    const score = computeWorkoutScore(plan as Record<string, unknown>);
    setLiveScore(score);
    // Freeze original score on first load (don't overwrite once set)
    if (originalScoreRef.current === null) {
      originalScoreRef.current = score;
    }
  }, [plan]);

  // Validate sets ≥ 1 on every plan change in edit mode
  useEffect(() => {
    if (!isEditing) { setSetsError(null); return; }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const planDays = getPlanDays(plan);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const invalid = planDays.some((d: any) =>
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (d.exercises ?? []).some((e: any) => (parseInt(e.sets) || 0) < 1)
    );
    setSetsError(invalid ? "All exercises must have at least 1 set before saving." : null);
  }, [isEditing, plan]);

  if (!plan) return null;
  return (
    <div className="glass-card overflow-hidden">
      <div role="button" className="w-full flex items-center justify-between p-4 hover:bg-white/5 cursor-pointer" onClick={() => setOpen((o) => !o)}>
        <div className="flex items-center gap-3">
          <Dumbbell className="h-4 w-4 text-cyan-400" />
          <div className="text-left">
            <p className="text-sm font-medium text-foreground">{rec.goal_type.replace(/_/g," ")} program</p>
            <p className="text-xs text-muted-foreground">{new Date(rec.created_at).toLocaleDateString()}{rec.edited_plan ? " · edited" : ""}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {liveScore !== null && (() => {
            const delta = originalScoreRef.current !== null ? liveScore - originalScoreRef.current : 0;
            const scoreColor = liveScore >= 90 ? "text-green-400" : liveScore >= 70 ? "text-cyan-400" : liveScore >= 50 ? "text-amber-400" : "text-red-400";
            return (
              <div className="flex items-center gap-1">
                <span className={`text-sm font-bold ${scoreColor}`}>{liveScore}<span className="text-xs text-muted-foreground font-normal">/100</span></span>
                {isEditing && Math.abs(delta) >= 0.05 && (
                  <span className={`text-xs font-medium ${delta > 0 ? "text-green-400" : "text-red-400"}`}>
                    {delta > 0 ? "+" : ""}{delta.toFixed(1)} pts
                  </span>
                )}
              </div>
            );
          })()}
          {!isEditing && <Button size="sm" variant="ghost" className="h-7 px-2 text-xs text-cyan-300" onClick={(e) => { e.stopPropagation(); onEdit(); }}><Edit3 className="h-3 w-3 mr-1" />Edit</Button>}
          {!isEditing && onDelete && <Button size="sm" variant="ghost" className="h-7 px-2 text-xs text-red-400 hover:text-red-300" onClick={(e) => { e.stopPropagation(); onDelete(); }}><Trash2 className="h-3 w-3" /></Button>}
          {open ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </div>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          {(plan.plan_explanation || plan.summary) && (
            <div className="rounded-lg bg-white/5 border border-white/10 p-3 space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Why this plan?</p>
              <p className="text-sm text-foreground/80">{plan.plan_explanation ?? plan.summary}</p>
            </div>
          )}
          {/* Score card — shown in both view and edit mode */}
          {liveScore !== null && (() => {
            const delta = originalScoreRef.current !== null ? liveScore - originalScoreRef.current : 0;
            const scoreColor = liveScore >= 90 ? "text-green-400" : liveScore >= 70 ? "text-cyan-400" : liveScore >= 50 ? "text-amber-400" : "text-red-400";
            return (
              <div className="rounded-lg bg-white/5 p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground font-medium">{isEditing ? "Live Quality Score" : "Quality Score"}</p>
                  <div className="flex items-center gap-2">
                    <span className={`text-lg font-bold ${scoreColor}`}>{liveScore}<span className="text-xs text-muted-foreground font-normal">/100</span></span>
                    {isEditing && Math.abs(delta) >= 0.05 && (
                      <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${delta > 0 ? "text-green-400 bg-green-500/10" : "text-red-400 bg-red-500/10"}`}>
                        {delta > 0 ? "+" : ""}{delta.toFixed(1)} pts from original
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })()}
          {isEditing && (
            <>
              {setsError && <p className="text-xs text-red-400 rounded bg-red-500/10 px-3 py-2">{setsError}</p>}
              <div className="flex gap-2">
                <Button size="sm" className="btn-primary-glass h-7 text-xs" onClick={onSaveEdit} disabled={saving || !!setsError}>{saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3 mr-1" />}Save</Button>
                <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={onCancelEdit}><X className="h-3 w-3 mr-1" />Cancel</Button>
              </div>
            </>
          )}
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {getPlanDays(plan).map((d: any, di: number) => (
            <div key={di} className="rounded bg-white/5 p-2 space-y-1">
              <p className="text-xs text-purple-300">{d.focus ? `${d.day ?? `Day ${di + 1}`}: ${d.focus}` : `Day ${d.day ?? di + 1}`}{d.is_rest ? " (Rest)" : ""}</p>
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {(d.exercises as any[])?.map((ex: any, ei: number) => (
                isEditing ? (
                  <div key={ei} className="space-y-1">
                    <div className="grid grid-cols-12 gap-1 items-end">
                      <div className="col-span-5 space-y-0.5">
                        <Label className="text-xs text-muted-foreground">Exercise</Label>
                        <ExerciseTypeahead value={ex.name} onChange={(name) => {
                          const newDays = getPlanDays(plan).map((dd: unknown, dii: number) => dii !== di ? dd : { ...d, exercises: d.exercises.map((exc: unknown, eii: number) => eii !== ei ? exc : { ...ex, name }) });
                          onPlanChange({ ...plan, days: newDays, weeks: undefined });
                        }} />
                      </div>
                      <div className="col-span-2 space-y-0.5">
                        <Label className="text-xs text-muted-foreground">Sets</Label>
                        <Input value={String(ex.sets ?? "")} onChange={(e) => {
                          const newDays = getPlanDays(plan).map((dd: unknown, dii: number) => dii !== di ? dd : { ...d, exercises: d.exercises.map((exc: unknown, eii: number) => eii !== ei ? exc : { ...ex, sets: e.target.value }) });
                          onPlanChange({ ...plan, days: newDays, weeks: undefined });
                        }} placeholder="e.g. 3" className="h-7 bg-white/10 border-white/10 text-foreground text-xs" />
                      </div>
                      <div className="col-span-2 space-y-0.5">
                        <Label className="text-xs text-muted-foreground">Reps</Label>
                        <Input value={ex.reps ?? ""} onChange={(e) => {
                          const newDays = getPlanDays(plan).map((dd: unknown, dii: number) => dii !== di ? dd : { ...d, exercises: d.exercises.map((exc: unknown, eii: number) => eii !== ei ? exc : { ...ex, reps: e.target.value }) });
                          onPlanChange({ ...plan, days: newDays, weeks: undefined });
                        }} placeholder="e.g. 8-12" className="h-7 bg-white/10 border-white/10 text-foreground text-xs" />
                      </div>
                      <div className="col-span-2 space-y-0.5">
                        <Label className="text-xs text-muted-foreground">Rest (s)</Label>
                        <Input value={ex.rest_seconds ?? ""} onChange={(e) => {
                          const newDays = getPlanDays(plan).map((dd: unknown, dii: number) => dii !== di ? dd : { ...d, exercises: d.exercises.map((exc: unknown, eii: number) => eii !== ei ? exc : { ...ex, rest_seconds: parseInt(e.target.value) || ex.rest_seconds }) });
                          onPlanChange({ ...plan, days: newDays, weeks: undefined });
                        }} placeholder="e.g. 60" className="h-7 bg-white/10 border-white/10 text-foreground text-xs" />
                      </div>
                      <div className="col-span-1 flex items-end pb-0.5">
                        <button type="button" aria-label="Remove exercise" onClick={() => {
                          const newDays = getPlanDays(plan).map((dd: unknown, dii: number) => dii !== di ? dd : { ...d, exercises: d.exercises.filter((_: unknown, eii: number) => eii !== ei) });
                          onPlanChange({ ...plan, days: newDays, weeks: undefined });
                        }} className="text-muted-foreground hover:text-red-400 h-7 flex items-center">
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div key={ei} className="text-xs ml-2">
                    <p className="text-foreground">· {ex.name}</p>
                    <p className="text-muted-foreground ml-2">
                      {ex.sets != null ? `Sets: ${ex.sets}` : "Sets: —"}
                      {ex.reps ? ` · Reps: ${ex.reps}` : " · Reps: —"}
                      {ex.weight_kg ? ` · Weight: ${ex.weight_kg} kg` : ""}
                      {ex.rest_seconds ? ` · Rest: ${ex.rest_seconds} s` : ""}
                    </p>
                  </div>
                )
              ))}
              {isEditing && !d.is_rest && (
                <button type="button" onClick={() => {
                  const newEx = { name: "", sets: 3, reps: "8-12", weight_kg: null, rest_seconds: 60 };
                  const newDays = getPlanDays(plan).map((dd: unknown, dii: number) => dii !== di ? dd : { ...d, exercises: [...(d.exercises ?? []), newEx] });
                  onPlanChange({ ...plan, days: newDays, weeks: undefined });
                }} className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1 mt-1">
                  <Plus className="h-3 w-3" />Add exercise
                </button>
              )}
            </div>
          ))}
          {plan.progression_notes && <p className="text-xs text-muted-foreground italic">{plan.progression_notes}</p>}
        </div>
      )}
    </div>
  );
}

// ─── Root Page ────────────────────────────────────────────────────────────────

export default function RecommendationsPage() {
  const [tab, setTab] = useState<Tab>("Diet");
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Plans & Recommendations</h1>
        <p className="text-sm text-muted-foreground mt-1">AI-powered diet and workout plans, food tracker, and split builder</p>
      </div>
      <TabBar active={tab} onChange={setTab} />
      {tab === "Diet" && <DietTab />}
      {tab === "Food & Meals" && <FoodMealsTab />}
      {tab === "Day Planner" && <DayPlannerTab />}
      {tab === "Workout" && <WorkoutTab />}
    </div>
  );
}
