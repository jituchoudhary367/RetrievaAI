"use client";

import { useState } from "react";
import Link from "next/link";
import { postRequestPasswordReset } from "@/lib/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mail, Shield } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      const resp = await postRequestPasswordReset({ email });
      setStatus("success");
      setMessage(resp.message);
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message || "Something went wrong. Please try again later.");
    }
  };

  return (
    <div className="w-full relative z-10 dark">
      {/* Card Container */}
      <div className="bg-[#111827] border border-white/5 rounded-[24px] p-8 sm:p-10 shadow-2xl shadow-black/50">
        
        {/* Header */}
        <div className="flex flex-col space-y-2 text-center mb-8">
          <h1 className="text-[28px] font-bold tracking-tight text-white flex items-center justify-center gap-2">
            Reset your password
          </h1>
          <p className="text-sm text-zinc-400 font-medium max-w-sm mx-auto">
            Enter your email and we'll send you a link to reset your password.
          </p>
        </div>

        {/* Form */}
        {status === "success" ? (
          <div className="rounded-xl bg-green-500/10 border border-green-500/20 p-4 text-center">
            <h3 className="text-sm font-bold text-green-400 mb-1">Check your email</h3>
            <p className="text-sm text-green-500/80">
              {message}
            </p>
          </div>
        ) : (
          <form className="space-y-5" onSubmit={handleSubmit}>
            {status === "error" && (
              <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-500 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                {message}
              </div>
            )}

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

            <div className="pt-2">
              <Button 
                type="submit" 
                className="w-full h-12 rounded-xl font-bold shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] transition-all text-white bg-gradient-to-r from-[#10b981] to-[#059669] hover:from-[#34d399] hover:to-[#10b981] border-none" 
                disabled={status === "loading"}
              >
                {status === "loading" ? "Sending..." : "Reset password"}
              </Button>
            </div>
          </form>
        )}

        <div className="text-center text-sm mt-8">
          <span className="text-zinc-400 font-medium">Remember your password? </span>
          <Link href="/login" className="font-semibold text-[#10b981] hover:text-[#10b981]/80 transition-colors">
            Sign in
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
