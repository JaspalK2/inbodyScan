"use client";

import { useQuery } from "@tanstack/react-query";
import { analytics } from "@/lib/api";
import {
  LineChart, Line, BarChart, Bar, RadialBarChart, RadialBar, Legend,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const CHART_COLORS = ["#A855F7", "#06B6D4", "#EC4899", "#F59E0B", "#10B981"];

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

  if (error || !data || data.history.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold gradient-text">Analytics</h1>
        <div className="glass-card p-12 text-center">
          <p className="text-muted-foreground">Upload at least one scan to view analytics.</p>
        </div>
      </div>
    );
  }

  // Body composition donut data (latest scan)
  const bodyCompMetrics = ["body_fat_percentage", "skeletal_muscle_mass_kg", "total_body_water_l"];
  const latestDelta = data.deltas.reduce<Record<string, number | null>>((acc, d) => {
    acc[d.metric_key] = d.current_value;
    return acc;
  }, {});

  const donutData = bodyCompMetrics
    .filter(k => latestDelta[k] !== null && latestDelta[k] !== undefined)
    .map((k, i) => ({
      name: METRIC_LABELS[k] ?? k,
      value: latestDelta[k] as number,
      fill: CHART_COLORS[i % CHART_COLORS.length],
    }));

  // Segmental bar data (latest scan)
  const segmentalKeys = [
    "segmental_lean_right_arm_kg", "segmental_lean_left_arm_kg",
    "segmental_lean_trunk_kg", "segmental_lean_right_leg_kg", "segmental_lean_left_leg_kg",
  ];
  const segmentalData = segmentalKeys
    .filter(k => latestDelta[k] !== undefined)
    .map(k => ({
      region: k.replace("segmental_lean_", "").replace(/_/g, " "),
      lean: latestDelta[k] ?? 0,
    }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">Visual breakdown of your body composition over time</p>
      </div>

      {/* Line charts — historical trends */}
      <section className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {data.history.slice(0, 4).map((h, i) => (
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
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={CHART_COLORS[i % CHART_COLORS.length]}
                  strokeWidth={2}
                  dot={{ fill: CHART_COLORS[i % CHART_COLORS.length], r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ))}
      </section>

      {/* Segmental bar chart */}
      {segmentalData.length > 0 && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-medium text-foreground/80 mb-4">Segmental Lean Mass (kg)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={segmentalData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="region" tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} width={35} />
              <Tooltip
                contentStyle={{ background: "rgba(13,17,23,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                labelStyle={{ color: "#e5e7eb", fontSize: 11 }}
              />
              <Bar dataKey="lean" radius={[4, 4, 0, 0]}>
                {segmentalData.map((_, idx) => (
                  <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Body composition radial */}
      {donutData.length > 0 && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-medium text-foreground/80 mb-4">Body Composition (Latest Scan)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <RadialBarChart innerRadius="30%" outerRadius="90%" data={donutData}>
              <RadialBar dataKey="value" label={{ position: "insideStart", fill: "#e5e7eb", fontSize: 10 }} />
              <Legend iconType="circle" iconSize={10} formatter={(v) => <span style={{ color: "#9ca3af", fontSize: 11 }}>{v}</span>} />
              <Tooltip
                contentStyle={{ background: "rgba(13,17,23,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                labelStyle={{ color: "#e5e7eb", fontSize: 11 }}
              />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
