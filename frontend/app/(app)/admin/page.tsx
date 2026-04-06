"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { admin } from "@/lib/api";
import { useAuth as useAuthCtx } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ShieldCheck, UserPlus } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const createUserSchema = z.object({
  username: z.string().min(3).regex(/^[a-zA-Z0-9_]+$/),
  email: z.string().email(),
  password: z.string().min(8),
  is_admin: z.boolean(),
}).transform(d => ({ ...d, is_admin: d.is_admin ?? false }));
type CreateUserForm = z.infer<typeof createUserSchema>;

export default function AdminPage() {
  const { user } = useAuthCtx();
  const router = useRouter();
  const qc = useQueryClient();
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    if (user && !user.is_admin) router.replace("/dashboard");
  }, [user, router]);

  const { data: users, isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: admin.listUsers,
    enabled: !!user?.is_admin,
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateUserForm) => admin.createUser(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin-users"] }); reset(); setCreateError(null); },
    onError: (e: unknown) => setCreateError((e as { detail?: string })?.detail ?? "Failed to create user"),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) => admin.toggleActive(id, is_active),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { register, handleSubmit, reset, formState: { isSubmitting, errors } } = useForm<any>({
    resolver: zodResolver(createUserSchema),
  });

  if (!user?.is_admin) return null;

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <ShieldCheck className="h-6 w-6 text-cyan-400" />
        <div>
          <h1 className="text-2xl font-bold gradient-text">Admin Portal</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Manage user accounts</p>
        </div>
      </div>

      {/* Create User Form */}
      <form onSubmit={handleSubmit(d => createMutation.mutate(d))} className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <UserPlus className="h-4 w-4 text-cyan-400" />
          Create New User
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label>Username</Label>
            <Input {...register("username")} className="bg-white/5 border-white/10 text-foreground" placeholder="username" />
            {errors.username && <p className="text-xs text-destructive">{String(errors.username.message)}</p>}
          </div>
          <div className="space-y-1.5">
            <Label>Email</Label>
            <Input {...register("email")} type="email" className="bg-white/5 border-white/10 text-foreground" placeholder="user@example.com" />
            {errors.email && <p className="text-xs text-destructive">{String(errors.email.message)}</p>}
          </div>
          <div className="space-y-1.5">
            <Label>Password</Label>
            <Input {...register("password")} type="password" className="bg-white/5 border-white/10 text-foreground" placeholder="min 8 characters" />
            {errors.password && <p className="text-xs text-destructive">{String(errors.password.message)}</p>}
          </div>
          <div className="flex items-end pb-0.5">
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input type="checkbox" {...register("is_admin")} className="rounded border-white/20" />
              Grant admin access
            </label>
          </div>
        </div>

        {createError && (
          <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-4 py-3 text-sm text-destructive">{createError}</div>
        )}

        <Button type="submit" disabled={isSubmitting} className="btn-primary-glass">
          {isSubmitting ? "Creating…" : "Create User"}
        </Button>
      </form>

      {/* Users Table */}
      <div className="glass-card overflow-hidden">
        <div className="p-4 border-b border-white/10">
          <h2 className="text-sm font-semibold text-foreground">All Users</h2>
        </div>
        {isLoading ? (
          <div className="flex h-32 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">Username</th>
                <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">Email</th>
                <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">Role</th>
                <th className="px-4 py-3 text-left text-xs text-muted-foreground font-medium">Status</th>
                <th className="px-4 py-3 text-right text-xs text-muted-foreground font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(users ?? []).map(u => (
                <tr key={u.id} className="border-b border-white/5 hover:bg-white/3 transition-colors">
                  <td className="px-4 py-3 font-medium text-foreground">{u.username}</td>
                  <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                  <td className="px-4 py-3">
                    {u.is_admin
                      ? <Badge className="bg-cyan-500/20 text-cyan-300 border-cyan-500/30">Admin</Badge>
                      : <Badge variant="outline" className="border-white/20 text-muted-foreground">User</Badge>
                    }
                  </td>
                  <td className="px-4 py-3">
                    {u.is_active
                      ? <Badge className="bg-green-500/20 text-green-300 border-green-500/30">Active</Badge>
                      : <Badge className="bg-red-500/20 text-red-300 border-red-500/30">Disabled</Badge>
                    }
                  </td>
                  <td className="px-4 py-3 text-right">
                    {u.username !== user.username && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => toggleMutation.mutate({ id: u.id, is_active: !u.is_active })}
                        className={u.is_active ? "text-red-400 hover:text-red-300 hover:bg-red-500/10" : "text-green-400 hover:text-green-300 hover:bg-green-500/10"}
                      >
                        {u.is_active ? "Disable" : "Enable"}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
