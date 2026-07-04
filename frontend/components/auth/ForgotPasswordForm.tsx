"use client";

import { useState } from "react";
import { postRequestPasswordReset } from "@/lib/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function ForgotPasswordForm() {
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
      // For enumeration resistance, backend might return success anyway.
      // But if there's a network error or rate limit, show it.
      setStatus("error");
      setMessage(err.message || "Something went wrong. Please try again later.");
    }
  };

  if (status === "success") {
    return (
      <div className="rounded-md bg-green-50 p-4 dark:bg-green-900/30">
        <h3 className="text-sm font-medium text-green-800 dark:text-green-200">Check your email</h3>
        <p className="mt-2 text-sm text-green-700 dark:text-green-300">
          {message}
        </p>
      </div>
    );
  }

  return (
    <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
      {status === "error" && (
        <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/30">
          <p className="text-sm text-red-800 dark:text-red-200">{message}</p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Email address
        </label>
        <Input
          type="email"
          required
          className="mt-1"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      <Button type="submit" className="w-full" disabled={status === "loading"}>
        {status === "loading" ? "Sending..." : "Reset password"}
      </Button>
    </form>
  );
}
