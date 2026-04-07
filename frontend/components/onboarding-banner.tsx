"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { user as userApi } from "@/lib/api";
import { X } from "lucide-react";

export function OnboardingBanner() {
  const { user } = useAuth();
  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: userApi.getProfile, enabled: !!user });
  const [dismissed, setDismissed] = useState(
    () => typeof window !== "undefined" && sessionStorage.getItem("onboarding_dismissed") === "true"
  );

  if (!user || dismissed || profile?.first_name) {
    return null;
  }

  const handleDismiss = () => {
    sessionStorage.setItem("onboarding_dismissed", "true");
    setDismissed(true);
  };

  return (
    <div className="mb-6 flex items-center justify-between rounded-lg border border-purple-500/30 bg-purple-500/10 px-4 py-3 text-sm">
      <span className="text-foreground/80">
        Welcome!{" "}
        <Link href="/profile" className="text-purple-400 hover:text-purple-300 underline underline-offset-2">
          Complete your profile
        </Link>{" "}
        to get personalised recommendations.
      </span>
      <button
        onClick={handleDismiss}
        aria-label="Dismiss"
        className="ml-4 text-muted-foreground hover:text-foreground transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
