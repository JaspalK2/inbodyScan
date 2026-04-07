"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth-context";
import { user as userApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { LayoutDashboard, Upload, BarChart2, User, Lightbulb, ShieldCheck, LogOut } from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/scans", label: "Scans", icon: Upload },
  { href: "/analytics", label: "Analytics", icon: BarChart2 },
  { href: "/recommendations", label: "Plans", icon: Lightbulb },
];

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: userApi.getProfile, enabled: !!user });
  const displayName = profile?.first_name
    ? `${profile.first_name}${profile.last_name ? ` ${profile.last_name}` : ""}`
    : user?.username;

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <nav className="fixed left-0 top-0 h-full w-60 glass-card rounded-none border-r border-white/10 flex flex-col p-4">
      <div className="mb-8 px-2">
        <span className="text-xl font-bold gradient-text">InBody</span>
        <p className="text-xs text-muted-foreground mt-0.5">{displayName}</p>
      </div>

      <div className="flex-1 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link key={href} href={href}>
              <div className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all
                ${active
                  ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                  : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                }`}>
                <Icon className="h-4 w-4" />
                {label}
              </div>
            </Link>
          );
        })}

        {user?.is_admin && (
          <Link href="/admin">
            <div className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all
              ${pathname.startsWith("/admin")
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
              }`}>
              <ShieldCheck className="h-4 w-4" />
              Admin
            </div>
          </Link>
        )}
      </div>

      <Link href="/profile">
        <div className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all mb-1 ${
          pathname.startsWith("/profile")
            ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
            : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
        }`}>
          <User className="h-4 w-4" />
          Profile
        </div>
      </Link>
      <Button
        variant="ghost"
        onClick={handleLogout}
        className="w-full justify-start gap-3 text-muted-foreground hover:text-foreground hover:bg-white/5"
      >
        <LogOut className="h-4 w-4" />
        Sign Out
      </Button>
    </nav>
  );
}
