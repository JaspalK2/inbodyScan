"use client";

import { useQuery } from "@tanstack/react-query";
import { analytics, type DeltaCard, type MetricHistory } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area,
} from "recharts";
import { TrendingUp, TrendingDown, Minus, ScanLine } from "lucide-react";
import Link from "next/link";

const METRIC_LABELS: Record<string, string> = {
  body_weight_kg: "Body Weight (kg)",
  body_fat_percentage: "Body Fat %",
  skeletal_muscle_mass_kg: "Muscle Mass (kg)",
  fat_free_mass_kg: "Fat-Free Mass (kg)",
  body_mass_index: "BMI",
  visceral_fat_level: "Visceral Fat",
  basal_metabolic_rate_kcal: "BMR (kcal)",
  total_body_water_l: "Total Body Water (L)",
};

function DeltaCardWidget({ card }: { card: DeltaCard }) {
  const label = METRIC_LABELS[card.metric_key] ?? card.metric_key;
  const isPositive = (card.delta ?? 0) > 0;
  const isNeutral = card.delta === null || card.delta === 0;

  const Icon = isNeutral ? Minus : isPositive ? TrendingUp : TrendingDown;
  const colorClass = isNeutral
    ? "text-muted-foreground"
    : isPositive
    ? "text-green-400"
    : "text-red-400";

  return (
    <div className="glass-card-hover p-4">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-2xl font-bold text-foreground">
        {card.current_value?.toFixed(1) ?? "—"}
      </p>
      <div className={`flex items-center gap-1 mt-1 text-sm ${colorClass}`}>
        <Icon className="h-3.5 w-3.5" />
        {card.delta !== null ? (
          <>
            {card.delta > 0 ? "+" : ""}{card.delta.toFixed(1)}
            {card.delta_pct !== null && (
              <span className="text-xs opacity-70">({card.delta_pct > 0 ? "+" : ""}{card.delta_pct}%)</span>
            )}
          </>
        ) : (
          <span className="text-xs">No previous scan</span>
        )}
      </div>
    </div>
  );
}

function HistoryChart({ history }: { history: MetricHistory }) {
  const label = METRIC_LABELS[history.metric_key] ?? history.metric_key;
  const data = history.points.map(p => ({ date: p.scan_date, value: p.value }));

  return (
    <div className="glass-card p-4">
      <p className="text-sm font-medium text-foreground/80 mb-3">{label}</p>
      <ResponsiveContainer width="100%" height={120}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id={`grad-${history.metric_key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#A855F7" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#A855F7" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} width={35} />
          <Tooltip
            contentStyle={{ background: "rgba(13,17,23,0.9)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
            labelStyle={{ color: "#e5e7eb", fontSize: 11 }}
            itemStyle={{ color: "#A855F7", fontSize: 11 }}
          />
          <Area type="monotone" dataKey="value" stroke="#A855F7" strokeWidth={2} fill={`url(#grad-${history.metric_key})`} dot={{ fill: "#A855F7", r: 3 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function DashboardPage() {
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
    return <p className="text-destructive">Failed to load dashboard.</p>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Dashboard</h1>
        {data.latest_scan_date && (
          <p className="text-sm text-muted-foreground mt-1">
            Latest scan: {data.latest_scan_date}
            {data.previous_scan_date && ` · Previous: ${data.previous_scan_date}`}
          </p>
        )}
      </div>

      {data.deltas.length === 0 ? (
        <div className="glass-card p-12 text-center space-y-4">
          <ScanLine className="h-12 w-12 text-muted-foreground mx-auto opacity-40" />
          <p className="text-muted-foreground">No scans yet. Upload your first InBody scan to see your analytics.</p>
          <Link href="/scans" className="inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-medium bg-purple-600 hover:bg-purple-700 text-white transition-colors">
            Upload First Scan
          </Link>
        </div>
      ) : (
        <>
          <section>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
              Current vs Previous Scan
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {data.deltas.map(card => (
                <DeltaCardWidget key={card.metric_key} card={card} />
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
              Historical Trends
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
              {data.history.map(h => (
                <HistoryChart key={h.metric_key} history={h} />
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
