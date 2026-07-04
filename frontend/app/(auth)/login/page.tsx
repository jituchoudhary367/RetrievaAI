"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { postLogin } from "@/lib/api/auth";
import { apiBaseUrl } from "@/lib/api/client";
import { setAuthToken } from "@/lib/auth/session";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { VerifyEmailNotice } from "@/components/auth/VerifyEmailNotice";
import { Mail, Shield, Check, EyeOff, Eye, Lock, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectUrl = searchParams.get("redirect") || "/chat";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [needsVerification, setNeedsVerification] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const resp = await postLogin({ email, password });
      setAuthToken(resp.accessToken);
      setTimeout(() => {
        router.push(redirectUrl);
      }, 50);
    } catch (err: any) {
      if (err.errors?.[0]?.code === "EMAIL_NOT_VERIFIED" || err.message === "Email not verified") {
        setNeedsVerification(true);
      } else {
        setError(err.message || "Login failed. Please check your credentials.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuthLogin = (provider: string) => {
    window.location.href = `${apiBaseUrl}/api/oauth/${provider}/login`;
  };

  return (
    <div className="w-full relative z-10 dark">
      {/* Card Container */}
      <div className="bg-[#111827] border border-white/5 rounded-[24px] p-8 sm:p-10 shadow-2xl shadow-black/50">

        {/* Header */}
        <div className="flex flex-col space-y-2 text-center mb-8">
          <h1 className="text-[28px] font-bold tracking-tight text-white flex items-center justify-center gap-2">
            Welcome Back <span className="animate-wave origin-bottom-right"></span>
          </h1>
          <p className="text-sm text-zinc-400 font-medium">
            Sign in to continue to RetrievaAI
          </p>
        </div>

        {/* Form */}
        <form className="space-y-5" onSubmit={handleSubmit}>
          {needsVerification ? (
            <VerifyEmailNotice email={email} />
          ) : error ? (
            <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-500 flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
              {error}
            </div>
          ) : null}

          <div className="space-y-5">
            <div className="space-y-2">
              <label className="text-[13px] font-semibold text-white">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-zinc-500" />
                <Input
                  type="email"
                  required
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-[#0b0f19] border-white/10 pl-11 h-12 text-white placeholder:text-zinc-600 focus-visible:ring-[#10b981]/50 focus-visible:border-[#10b981]/50 rounded-xl transition-all"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-[13px] font-semibold text-white">
                  Password
                </label>
                <Link href="/forgot-password" className="text-[12px] font-semibold text-[#10b981] hover:text-[#10b981]/80 transition-colors">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3.5 h-4 w-4 text-zinc-500" />
                <Input
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-[#0b0f19] border-white/10 pl-11 pr-11 h-12 text-white placeholder:text-zinc-600 focus-visible:ring-[#10b981]/50 focus-visible:border-[#10b981]/50 rounded-xl transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3.5 text-zinc-500 hover:text-white transition-colors"
                >
                  {showPassword ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                </button>
              </div>
            </div>
          </div>

          {/* Sign In Button */}
          <div className="pt-2">
            <Button
              type="submit"
              className="w-full h-12 rounded-xl font-bold shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] transition-all text-white bg-gradient-to-r from-[#10b981] to-[#059669] hover:from-[#34d399] hover:to-[#10b981] border-none flex items-center justify-center gap-2"
              disabled={isLoading}
            >
              {isLoading ? "Signing in..." : "Sign In"}
              {!isLoading && <ArrowRight className="w-4 h-4" />}
            </Button>
          </div>

          {/* OR Divider */}
          <div className="relative py-2 flex items-center justify-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10"></div>
            </div>
            <div className="relative bg-[#111827] px-4 text-[11px] font-semibold text-zinc-500 uppercase tracking-widest">
              OR
            </div>
          </div>

          {/* Social Logins */}
          <div className="space-y-3">
            <Button
              type="button"
              variant="outline"
              className="w-full h-12 rounded-xl bg-[#0b0f19] border-white/5 hover:bg-[#1f2937] hover:border-white/10 hover:text-white transition-all font-semibold flex items-center justify-center gap-3 text-zinc-300"
              onClick={() => handleOAuthLogin('google')}
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
              </svg>
              Sign in with Google
            </Button>
          </div>
        </form>

        <div className="text-center text-sm mt-8">
          <span className="text-zinc-400 font-medium">Don't have an account? </span>
          <Link href="/signup" className="font-semibold text-[#10b981] hover:text-[#10b981]/80 transition-colors">
            Sign up
          </Link>
        </div>
      </div>

      {/* Bottom Security Badge */}
      <div className="absolute -bottom-16 left-0 w-full text-center flex items-center justify-center gap-2 text-xs text-zinc-400 font-medium">
        <Shield className="w-3.5 h-3.5 text-[#10b981]" />
        Your data is encrypted and secure
      </div>
    </div>
  );
}
