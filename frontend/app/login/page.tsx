"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "@/lib/auth-context";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

const loginSchema = z.object({
  username: z.string().min(3),
  password: z.string().min(8),
});
type LoginData = z.infer<typeof loginSchema>;

const registerSchema = z.object({
  username: z.string().min(3, "Username must be at least 3 characters").max(64).regex(/^\w+$/, "Only letters, numbers, and underscores"),
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
type RegisterData = z.infer<typeof registerSchema>;

interface LinkPendingState {
  linkToken: string;
  email: string;
  googleName: string | null;
}

export default function LoginPage() {
  const { login, register, googleLogin, confirmGoogleLink } = useAuth();
  const router = useRouter();
  const [mode, setMode] = useState<"signin" | "register">("signin");
  const [error, setError] = useState<string | null>(null);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [linkPending, setLinkPending] = useState<LinkPendingState | null>(null);
  const [linkLoading, setLinkLoading] = useState(false);

  const loginForm = useForm<LoginData>({ resolver: zodResolver(loginSchema) });
  const registerForm = useForm<RegisterData>({ resolver: zodResolver(registerSchema) });

  const onSignIn = async (data: LoginData) => {
    setError(null);
    try {
      await login(data.username, data.password);
      router.push("/dashboard");
    } catch (e: unknown) {
      const err = e as { detail?: string };
      setError(err?.detail ?? "Login failed");
    }
  };

  const onRegister = async (data: RegisterData) => {
    setError(null);
    try {
      await register(data.username, data.email, data.password);
      router.push("/profile");
    } catch (e: unknown) {
      const err = e as { detail?: string };
      setError(err?.detail ?? "Registration failed");
    }
  };

  const handleGoogleSuccess = async (credentialResponse: { credential?: string }) => {
    if (!credentialResponse.credential) {
      setError("Google sign-in failed. Please try again.");
      return;
    }
    setGoogleLoading(true);
    setError(null);
    try {
      const result = await googleLogin(credentialResponse.credential);
      if (result.needsLink && result.linkToken) {
        setLinkPending({
          linkToken: result.linkToken,
          email: result.email ?? "",
          googleName: result.googleName ?? null,
        });
      } else {
        router.push("/dashboard");
      }
    } catch (e: unknown) {
      const err = e as { detail?: string };
      setError(err?.detail ?? "Google sign-in failed. Please try again.");
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleConfirmLink = async () => {
    if (!linkPending) return;
    setLinkLoading(true);
    setError(null);
    try {
      await confirmGoogleLink(linkPending.linkToken);
      router.push("/dashboard");
    } catch (e: unknown) {
      const err = e as { detail?: string };
      setError(err?.detail ?? "Account linking failed. Please try again.");
      setLinkPending(null);
    } finally {
      setLinkLoading(false);
    }
  };

  const switchMode = (next: "signin" | "register") => {
    setMode(next);
    setError(null);
    loginForm.reset();
    registerForm.reset();
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md glass-card p-8">
        {/* Logo / Title */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold gradient-text">InBody Analyzer</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {mode === "signin" ? "Sign in to your account" : "Create a new account"}
          </p>
        </div>

        {/* Account Linking Confirmation */}
        {linkPending && (
          <div className="mb-6 rounded-lg border border-purple-500/30 bg-purple-500/10 p-4 space-y-3">
            <p className="text-sm font-medium text-foreground">
              An account with <span className="text-purple-300">{linkPending.email}</span> already exists.
            </p>
            <p className="text-xs text-muted-foreground">
              {linkPending.googleName
                ? `Link your Google account (${linkPending.googleName}) to sign in faster in the future?`
                : "Link your Google account to sign in faster in the future?"}
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                className="btn-primary-glass flex-1"
                disabled={linkLoading}
                onClick={handleConfirmLink}
              >
                {linkLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Linking…
                  </span>
                ) : "Yes, link account"}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="flex-1 text-muted-foreground"
                disabled={linkLoading}
                onClick={() => setLinkPending(null)}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Sign In Form */}
        {mode === "signin" && (
          <form onSubmit={loginForm.handleSubmit(onSignIn)} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="username" className="text-foreground/80">Username</Label>
              <Input
                id="username"
                {...loginForm.register("username")}
                className="bg-white/5 border-white/10 focus:border-purple-500 text-foreground placeholder:text-muted-foreground"
                placeholder="your_username"
              />
              {loginForm.formState.errors.username && (
                <p className="text-xs text-destructive">{loginForm.formState.errors.username.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-foreground/80">Password</Label>
              <Input
                id="password"
                type="password"
                {...loginForm.register("password")}
                className="bg-white/5 border-white/10 focus:border-purple-500 text-foreground"
                placeholder="••••••••"
              />
              {loginForm.formState.errors.password && (
                <p className="text-xs text-destructive">{loginForm.formState.errors.password.message}</p>
              )}
            </div>

            {error && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <Button
              type="submit"
              disabled={loginForm.formState.isSubmitting}
              className="w-full btn-primary-glass glow-purple"
            >
              {loginForm.formState.isSubmitting ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Signing in…
                </span>
              ) : "Sign In"}
            </Button>

            <p className="text-center text-xs text-muted-foreground">
              Don&apos;t have an account?{" "}
              <button
                type="button"
                onClick={() => switchMode("register")}
                className="text-purple-400 hover:text-purple-300 underline underline-offset-2"
              >
                Create Account
              </button>
            </p>
          </form>
        )}

        {/* Register Form */}
        {mode === "register" && (
          <form onSubmit={registerForm.handleSubmit(onRegister)} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="reg-username" className="text-foreground/80">Username</Label>
              <Input
                id="reg-username"
                {...registerForm.register("username")}
                className="bg-white/5 border-white/10 focus:border-purple-500 text-foreground placeholder:text-muted-foreground"
                placeholder="your_username"
              />
              {registerForm.formState.errors.username && (
                <p className="text-xs text-destructive">{registerForm.formState.errors.username.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="reg-email" className="text-foreground/80">Email</Label>
              <Input
                id="reg-email"
                type="email"
                {...registerForm.register("email")}
                className="bg-white/5 border-white/10 focus:border-purple-500 text-foreground placeholder:text-muted-foreground"
                placeholder="you@example.com"
              />
              {registerForm.formState.errors.email && (
                <p className="text-xs text-destructive">{registerForm.formState.errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="reg-password" className="text-foreground/80">Password</Label>
              <Input
                id="reg-password"
                type="password"
                {...registerForm.register("password")}
                className="bg-white/5 border-white/10 focus:border-purple-500 text-foreground"
                placeholder="••••••••"
              />
              {registerForm.formState.errors.password && (
                <p className="text-xs text-destructive">{registerForm.formState.errors.password.message}</p>
              )}
            </div>

            {error && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <Button
              type="submit"
              disabled={registerForm.formState.isSubmitting}
              className="w-full btn-primary-glass glow-purple"
            >
              {registerForm.formState.isSubmitting ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Creating account…
                </span>
              ) : "Create Account"}
            </Button>

            <p className="text-center text-xs text-muted-foreground">
              Already have an account?{" "}
              <button
                type="button"
                onClick={() => switchMode("signin")}
                className="text-purple-400 hover:text-purple-300 underline underline-offset-2"
              >
                Sign In Instead
              </button>
            </p>
          </form>
        )}

        {/* Divider */}
        <div className="my-5 flex items-center gap-3">
          <div className="flex-1 h-px bg-white/10" />
          <span className="text-xs text-muted-foreground">or</span>
          <div className="flex-1 h-px bg-white/10" />
        </div>

        {/* Google Sign-In */}
        <div className={`flex justify-center ${googleLoading ? "opacity-50 pointer-events-none" : ""}`}>
          {googleLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
              Signing in with Google…
            </div>
          ) : (
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => setError("Google sign-in failed. Please try again.")}
              theme="filled_black"
              shape="rectangular"
              text="continue_with"
              width="100%"
            />
          )}
        </div>
      </div>
    </div>
  );
}
