"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { user as userApi, type DietaryRestriction } from "@/lib/api";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { X, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

const emptyStringToUndefined = z.preprocess((v) => (v === "" ? undefined : v), z.string().optional());
const emptyNumberToUndefined = (min: number, max: number) =>
  z.preprocess((v) => (v === "" || v === 0 ? undefined : v), z.coerce.number().min(min).max(max).optional());

const profileSchema = z.object({
  first_name: emptyStringToUndefined,
  last_name: emptyStringToUndefined,
  age: emptyNumberToUndefined(1, 120),
  gender: z.preprocess((v) => (v === "" ? undefined : v), z.enum(["male", "female", "other"]).optional()),
  activity_level: z.preprocess((v) => (v === "" ? undefined : v), z.enum(["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"]).optional()),
});

const GOAL_OPTIONS = [
  { value: "lose_fat", label: "Lose Fat" },
  { value: "build_muscle", label: "Build Muscle" },
  { value: "maintain", label: "Maintain" },
  { value: "improve_endurance", label: "Improve Endurance" },
  { value: "general_health", label: "General Health" },
];

const RESTRICTION_OPTIONS = [
  "vegetarian", "vegan", "no_pork", "no_beef", "no_eggs",
  "no_dairy", "nut_allergy", "gluten_free", "halal", "kosher", "other",
];

export default function ProfilePage() {
  const qc = useQueryClient();
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [goalError, setGoalError] = useState<string | null>(null);
  const [restrictionError, setRestrictionError] = useState<string | null>(null);

  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: userApi.getProfile });
  const { data: goal } = useQuery({ queryKey: ["goal"], queryFn: userApi.getGoal });
  const { data: restrictions } = useQuery({ queryKey: ["restrictions"], queryFn: userApi.getDietaryRestrictions });

  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm({
    resolver: zodResolver(profileSchema),
  });

  useEffect(() => {
    if (profile) {
      reset({
        first_name: profile.first_name ?? "",
        last_name: profile.last_name ?? "",
        age: profile.age ?? undefined,
        gender: (profile.gender as "male" | "female" | "other") ?? undefined,
        activity_level: (profile.activity_level as "sedentary" | "lightly_active" | "moderately_active" | "very_active" | "extra_active") ?? undefined,
      });
    }
  }, [profile, reset]);

  const updateProfile = useMutation({
    mutationFn: (data: object) => userApi.updateProfile(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profile"] });
      setSaved(true);
      setSaveError(null);
      setTimeout(() => setSaved(false), 2000);
    },
    onError: () => setSaveError("Failed to save profile. Please try again."),
  });

  const setGoal = useMutation({
    mutationFn: (g: string) => userApi.setGoal(g),
    onMutate: async (goalType) => {
      await qc.cancelQueries({ queryKey: ["goal"] });
      const previous = qc.getQueryData(["goal"]);
      qc.setQueryData(["goal"], (old: { id: string; user_id: string; goal_type: string } | undefined) =>
        old ? { ...old, goal_type: goalType } : { id: "optimistic", user_id: "", goal_type: goalType }
      );
      setGoalError(null);
      return { previous };
    },
    onError: (_err, _vars, ctx) => {
      qc.setQueryData(["goal"], ctx?.previous);
      setGoalError("Failed to save goal. Please try again.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["goal"] }),
  });

  const addRestriction = useMutation({
    mutationFn: (r: string) => userApi.addRestriction(r),
    onMutate: async (restrictionType) => {
      await qc.cancelQueries({ queryKey: ["restrictions"] });
      const previous = qc.getQueryData(["restrictions"]);
      qc.setQueryData(["restrictions"], (old: DietaryRestriction[] | undefined) => [
        ...(old ?? []),
        { id: "optimistic-" + Date.now(), user_id: "", restriction_type: restrictionType, notes: null },
      ]);
      setRestrictionError(null);
      return { previous };
    },
    onError: (_err, _vars, ctx) => {
      qc.setQueryData(["restrictions"], ctx?.previous);
      setRestrictionError("Failed to update dietary restriction. Please try again.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["restrictions"] }),
  });

  const removeRestriction = useMutation({
    mutationFn: (id: string) => userApi.removeRestriction(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["restrictions"] });
      const previous = qc.getQueryData(["restrictions"]);
      qc.setQueryData(["restrictions"], (old: DietaryRestriction[] | undefined) =>
        (old ?? []).filter((r) => r.id !== id)
      );
      setRestrictionError(null);
      return { previous };
    },
    onError: (_err, _vars, ctx) => {
      qc.setQueryData(["restrictions"], ctx?.previous);
      setRestrictionError("Failed to remove dietary restriction. Please try again.");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["restrictions"] }),
  });

  const activeRestrictionTypes = (restrictions ?? []).map(r => r.restriction_type);

  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Profile</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your personal details, goals and dietary preferences</p>
      </div>

      {/* Personal Info */}
      <form onSubmit={handleSubmit(d => updateProfile.mutate(d))} className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-foreground">Personal Information</h2>
        <div className="grid grid-cols-2 gap-4">
          {[
            { id: "first_name", label: "First Name" },
            { id: "last_name", label: "Last Name" },
            { id: "age", label: "Age", type: "number" },
          ].map(f => (
            <div key={f.id} className="space-y-1.5">
              <Label htmlFor={f.id} className="text-foreground/80">{f.label}</Label>
              <Input
                id={f.id}
                type={f.type ?? "text"}
                {...register(f.id as keyof z.infer<typeof profileSchema>)}
                className="bg-white/5 border-white/10 text-foreground"
              />
            </div>
          ))}

          <div className="space-y-1.5">
            <Label className="text-foreground/80">Gender</Label>
            <select
              {...register("gender")}
              className="w-full rounded-md bg-white/5 border border-white/10 text-foreground px-3 py-2 text-sm"
            >
              <option value="">Select…</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="space-y-1.5 col-span-2">
            <Label className="text-foreground/80">Activity Level</Label>
            <select
              {...register("activity_level")}
              className="w-full rounded-md bg-white/5 border border-white/10 text-foreground px-3 py-2 text-sm"
            >
              <option value="">Select…</option>
              <option value="sedentary">Sedentary (little or no exercise)</option>
              <option value="lightly_active">Lightly Active (1–3 days/week)</option>
              <option value="moderately_active">Moderately Active (3–5 days/week)</option>
              <option value="very_active">Very Active (6–7 days/week)</option>
              <option value="extra_active">Extra Active (intense daily exercise)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={isSubmitting} className="btn-primary-glass">
            {isSubmitting ? "Saving…" : "Save Profile"}
          </Button>
          {saved && <span className="text-sm text-green-400">Saved!</span>}
          {saveError && <span className="text-sm text-red-400">{saveError}</span>}
        </div>
      </form>

      {/* Health Goal */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-foreground">Health Goal</h2>
          {setGoal.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />}
        </div>
        <div className="flex flex-wrap gap-2">
          {GOAL_OPTIONS.map(g => (
            <button
              key={g.value}
              onClick={() => setGoal.mutate(g.value)}
              disabled={setGoal.isPending}
              className={`rounded-full px-4 py-1.5 text-sm border transition-all disabled:opacity-70 ${
                goal?.goal_type === g.value
                  ? "bg-purple-500/20 border-purple-500/50 text-purple-300"
                  : "border-white/10 text-muted-foreground hover:border-white/30 hover:text-foreground"
              }`}
            >
              {g.label}
            </button>
          ))}
        </div>
        {goalError && <p className="text-xs text-red-400">{goalError}</p>}
      </div>

      {/* Dietary Restrictions */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-foreground">Dietary Restrictions</h2>
          {(addRestriction.isPending || removeRestriction.isPending) && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />}
        </div>
        <div className="flex flex-wrap gap-2">
          {RESTRICTION_OPTIONS.map(r => {
            const active = activeRestrictionTypes.includes(r);
            const record = (restrictions ?? []).find(x => x.restriction_type === r);
            return (
              <button
                key={r}
                onClick={() => active && record
                  ? removeRestriction.mutate(record.id)
                  : addRestriction.mutate(r)
                }
                className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs border transition-all ${
                  active
                    ? "bg-cyan-500/20 border-cyan-500/50 text-cyan-300"
                    : "border-white/10 text-muted-foreground hover:border-white/30 hover:text-foreground"
                }`}
              >
                {r.replace(/_/g, " ")}
                {active && <X className="h-3 w-3" />}
              </button>
            );
          })}
        </div>
        {restrictionError && <p className="text-xs text-red-400">{restrictionError}</p>}
      </div>
    </div>
  );
}
