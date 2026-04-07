"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { analytics } from "@/lib/api";
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle } from "lucide-react";

const CHART_COLORS = ["#A855F7", "#06B6D4", "#EC4899", "#F59E0B", "#10B981", "#3B82F6", "#F97316", "#8B5CF6"];

const METRIC_LABELS: Record<string, string> = {
  body_weight_kg: "Body Weight (kg)",
  body_fat_percentage: "Body Fat %",
  skeletal_muscle_mass_kg: "Muscle Mass (kg)",
  fat_free_mass_kg: "Fat-Free Mass (kg)",
  body_mass_index: "BMI",
  visceral_fat_level: "Visceral Fat Level",
  basal_metabolic_rate_kcal: "BMR (kcal)",
  total_body_water_l: "Total Body Water (L)",
};

const PRIMARY_METRICS = ["body_weight_kg", "body_fat_percentage", "skeletal_muscle_mass_kg", "body_mass_index"];

// Improvement direction: true = higher is better, false = lower is better
const IMPROVEMENT_DIRECTION: Record<string, boolean> = {
  body_weight_kg: false,
  body_fat_percentage: false,
  skeletal_muscle_mass_kg: true,
  fat_free_mass_kg: true,
  body_mass_index: false,
  visceral_fat_level: false,
  basal_metabolic_rate_kcal: true,
  total_body_water_l: true,
};

function getBodyFatCategory(pct: number): { label: string; color: string } {
  if (pct < 10) return { label: "Very Lean", color: "text-blue-400" };
  if (pct < 18) return { label: "Athletic", color: "text-green-400" };
  if (pct < 25) return { label: "Healthy", color: "text-green-300" };
  if (pct < 30) return { label: "Above Average", color: "text-amber-400" };
  return { label: "High Body Fat", color: "text-red-400" };
}

function DeltaCard({ metricKey, currentValue, delta, deltaPct }: {
  metricKey: string; currentValue: number | null; delta: number | null; deltaPct: number | null;
}) {
  const label = METRIC_LABELS[metricKey] ?? metricKey;
  const higherIsBetter = IMPROVEMENT_DIRECTION[metricKey] ?? true;
  const isImprovement = delta !== null && delta !== 0 && ((delta > 0) === higherIsBetter);
  const isNeutral = delta === null || delta === 0;
  const Icon = isNeutral ? Minus : (delta ?? 0) > 0 ? TrendingUp : TrendingDown;
  const colorClass = isNeutral ? "text-muted-foreground" : isImprovement ? "text-green-400" : "text-red-400";

  return (
    <div className="glass-card p-4">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-2xl font-bold text-foreground">{currentValue?.toFixed(1) ?? "—"}</p>
      <div className={`flex items-center gap-1 mt-1 text-sm ${colorClass}`}>
        <Icon className="h-3.5 w-3.5" />
        {delta !== null ? (
          <>
            {delta > 0 ? "+" : ""}{delta.toFixed(1)}
            {deltaPct !== null && (
              <span className="text-xs opacity-70 ml-1">({deltaPct > 0 ? "+" : ""}{deltaPct}%)</span>
            )}
          </>
        ) : (
          <span className="text-xs">No previous scan</span>
        )}
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: analytics.dashboard,
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold gradient-text">Analytics</h1>
        <div className="glass-card p-12 text-center space-y-4">
          <p className="text-muted-foreground">Could not load analytics data.</p>
        </div>
      </div>
    );
  }

  // 0 scans
  if (data.history.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold gradient-text">Analytics</h1>
        <div className="glass-card p-12 text-center space-y-4">
          <p className="text-lg text-foreground/80">No scan data yet</p>
          <p className="text-sm text-muted-foreground">Upload your first InBody scan to see detailed body composition analytics.</p>
          <Link href="/scans" className="inline-block mt-2 px-5 py-2 rounded-lg btn-primary-glass text-sm">
            Upload a Scan
          </Link>
        </div>
      </div>
    );
  }

  const deltaMap = data.deltas.reduce<Record<string, typeof data.deltas[0]>>((acc, d) => {
    acc[d.metric_key] = d;
    return acc;
  }, {});

  const latestValues = data.deltas.reduce<Record<string, number | null>>((acc, d) => {
    acc[d.metric_key] = d.current_value;
    return acc;
  }, {});

  const scanCount = data.history[0]?.points.length ?? 0;
  const hasMultipleScans = scanCount >= 2;

  // Body fat summary
  const bodyFatPct = latestValues["body_fat_percentage"];
  const smmKg = latestValues["skeletal_muscle_mass_kg"];
  const bodyFatCategory = bodyFatPct !== null && bodyFatPct !== undefined ? getBodyFatCategory(bodyFatPct) : null;

  // Muscle balance
  const leftArm = latestValues["segmental_lean_left_arm_kg"];
  const rightArm = latestValues["segmental_lean_right_arm_kg"];
  const leftLeg = latestValues["segmental_lean_left_leg_kg"];
  const rightLeg = latestValues["segmental_lean_right_leg_kg"];
  const hasSegmental = leftArm != null && rightArm != null && leftLeg != null && rightLeg != null;

  function balanceInfo(left: number, right: number, label: string) {
    const max = Math.max(left, right);
    const pct = max > 0 ? Math.abs(left - right) / max * 100 : 0;
    const dominant = left > right ? "Left" : right > left ? "Right" : "Balanced";
    return { pct, imbalanced: pct > 10, dominant, label, left, right };
  }

  const armBalance = hasSegmental ? balanceInfo(leftArm!, rightArm!, "Arms") : null;
  const legBalance = hasSegmental ? balanceInfo(leftLeg!, rightLeg!, "Legs") : null;
  const hasImbalance = armBalance?.imbalanced || legBalance?.imbalanced;

  // Segmental bar data
  const segmentalKeys = [
    "segmental_lean_right_arm_kg", "segmental_lean_left_arm_kg",
    "segmental_lean_trunk_kg", "segmental_lean_right_leg_kg", "segmental_lean_left_leg_kg",
  ];
  const segmentalLabels: Record<string, string> = {
    segmental_lean_right_arm_kg: "R Arm",
    segmental_lean_left_arm_kg: "L Arm",
    segmental_lean_trunk_kg: "Trunk",
    segmental_lean_right_leg_kg: "R Leg",
    segmental_lean_left_leg_kg: "L Leg",
  };
  const segmentalData = segmentalKeys
    .filter(k => latestValues[k] != null)
    .map(k => ({ region: segmentalLabels[k] ?? k, lean: latestValues[k] ?? 0, key: k }));

  // Split history into primary and secondary
  const primaryHistory = data.history.filter(h => PRIMARY_METRICS.includes(h.metric_key));
  const secondaryHistory = data.history.filter(h => !PRIMARY_METRICS.includes(h.metric_key) && !h.metric_key.startsWith("segmental"));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {hasMultipleScans ? `${scanCount} scans · Progress tracking active` : "1 scan · Upload another to track progress"}
        </p>
      </div>

      {/* Delta cards row */}
      {hasMultipleScans && (
        <section>
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Change Since Last Scan</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {PRIMARY_METRICS.map(key => {
              const d = deltaMap[key];
              if (!d) return null;
              return (
                <DeltaCard
                  key={key}
                  metricKey={key}
                  currentValue={d.current_value}
                  delta={d.delta}
                  deltaPct={d.delta_pct}
                />
              );
            })}
          </div>
        </section>
      )}

      {/* Body composition summary card */}
      {(bodyFatCategory || smmKg != null) && (
        <section className="glass-card p-5 border border-purple-500/20">
          <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-purple-400" />
            Body Composition Summary
          </h2>
          <div className="space-y-2 text-sm">
            {bodyFatCategory && bodyFatPct != null && (
              <p className="text-foreground/80">
                Your body fat percentage is <span className="font-semibold">{bodyFatPct.toFixed(1)}%</span>{" "}
                — classified as{" "}
                <span className={`font-semibold ${bodyFatCategory.color}`}>{bodyFatCategory.label}</span>.
              </p>
            )}
            {smmKg != null && (
              <p className="text-foreground/80">
                Skeletal muscle mass: <span className="font-semibold">{smmKg.toFixed(1)} kg</span>.
                {bodyFatPct != null && bodyFatPct < 18 && " Your muscle-to-fat ratio is excellent."}
                {bodyFatPct != null && bodyFatPct >= 25 && " Consider a strength training program to improve your muscle-to-fat ratio."}
              </p>
            )}
            {!hasMultipleScans && (
              <p className="text-muted-foreground text-xs mt-2">
                Upload a second scan to unlock progress tracking and trend analysis.
              </p>
            )}
          </div>
        </section>
      )}

      {/* Muscle balance section */}
      {hasSegmental && (
        <section>
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Muscle Balance Analysis
          </h2>
          <div className="glass-card p-5 space-y-4">
            {hasImbalance && (
              <div className="flex items-start gap-2 rounded-lg bg-amber-500/10 border border-amber-500/30 px-3 py-2 text-sm text-amber-300">
                <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                <span>Muscle imbalance detected. Targeted unilateral exercises can help correct this over time.</span>
              </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[armBalance, legBalance].filter(Boolean).map(b => b && (
                <div key={b.label} className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{b.label}</span>
                    {b.imbalanced && (
                      <span className="text-amber-400 font-medium">{b.dominant} side dominant · {b.pct.toFixed(1)}% difference</span>
                    )}
                    {!b.imbalanced && <span className="text-green-400">Balanced</span>}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="w-12 text-right text-foreground/60">Left</span>
                      <div className="flex-1 bg-white/10 rounded-full h-2">
                        <div className="bg-cyan-500 h-2 rounded-full" style={{ width: `${Math.min((b.left / (b.left + b.right)) * 100 * 2, 100)}%` }} />
                      </div>
                      <span className="w-12 text-foreground/80">{b.left.toFixed(2)} kg</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="w-12 text-right text-foreground/60">Right</span>
                      <div className="flex-1 bg-white/10 rounded-full h-2">
                        <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${Math.min((b.right / (b.left + b.right)) * 100 * 2, 100)}%` }} />
                      </div>
                      <span className="w-12 text-foreground/80">{b.right.toFixed(2)} kg</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Primary trend charts */}
      {hasMultipleScans && primaryHistory.length > 0 && (
        <section>
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Key Metric Trends</h2>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {primaryHistory.map((h, i) => (
              <div key={h.metric_key} className="glass-card p-5">
                <h3 className="text-sm font-medium text-foreground/80 mb-4">{METRIC_LABELS[h.metric_key] ?? h.metric_key}</h3>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={h.points.map(p => ({ date: p.scan_date, value: p.value }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} width={40} />
                    <Tooltip
                      contentStyle={{ background: "rgba(13,17,23,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                      labelStyle={{ color: "#e5e7eb", fontSize: 11 }}
                      itemStyle={{ color: CHART_COLORS[i % CHART_COLORS.length], fontSize: 11 }}
                    />
                    <Line type="monotone" dataKey="value" stroke={CHART_COLORS[i % CHART_COLORS.length]} strokeWidth={2}
                      dot={{ fill: CHART_COLORS[i % CHART_COLORS.length], r: 4 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Segmental bar chart */}
      {segmentalData.length > 0 && (
        <section>
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Segmental Lean Mass (kg)</h2>
          <div className="glass-card p-5">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={segmentalData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="region" tick={{ fontSize: 11, fill: "#6b7280" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} width={35} />
                <Tooltip
                  contentStyle={{ background: "rgba(13,17,23,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  labelStyle={{ color: "#e5e7eb", fontSize: 11 }}
                />
                <Bar dataKey="lean" radius={[4, 4, 0, 0]} name="Lean Mass (kg)">
                  {segmentalData.map((_, idx) => (
                    <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* Secondary metrics */}
      {hasMultipleScans && secondaryHistory.length > 0 && (
        <section>
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Additional Metrics</h2>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {secondaryHistory.map((h, i) => (
              <div key={h.metric_key} className="glass-card p-5">
                <h3 className="text-sm font-medium text-foreground/80 mb-4">{METRIC_LABELS[h.metric_key] ?? h.metric_key}</h3>
                <ResponsiveContainer width="100%" height={160}>
                  <LineChart data={h.points.map(p => ({ date: p.scan_date, value: p.value }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} width={40} />
                    <Tooltip
                      contentStyle={{ background: "rgba(13,17,23,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                      labelStyle={{ color: "#e5e7eb", fontSize: 11 }}
                      itemStyle={{ color: CHART_COLORS[(i + 4) % CHART_COLORS.length], fontSize: 11 }}
                    />
                    <Line type="monotone" dataKey="value" stroke={CHART_COLORS[(i + 4) % CHART_COLORS.length]} strokeWidth={2}
                      dot={{ fill: CHART_COLORS[(i + 4) % CHART_COLORS.length], r: 3 }} activeDot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Prompt to upload more scans if only 1 */}
      {!hasMultipleScans && (
        <div className="glass-card p-6 border border-purple-500/20 text-center space-y-2">
          <p className="text-sm text-foreground/80">Upload a second scan to unlock trend charts and progress tracking.</p>
          <Link href="/scans" className="inline-block mt-2 px-4 py-1.5 rounded-lg btn-primary-glass text-sm">
            Upload Another Scan
          </Link>
        </div>
      )}
    </div>
  );
}
