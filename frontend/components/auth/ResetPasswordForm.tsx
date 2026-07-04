"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { postResetPassword } from "@/lib/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function ResetPasswordForm({ token }: { token: string }) {
  const router = useRouter();
  const [newPassword, setNewPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      const resp = await postResetPassword({ token, newPassword });
      setStatus("success");
      setMessage(resp.message);
      
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message || "Failed to reset password. The link might be invalid or expired.");
    }
  };

  if (status === "success") {
    return (
      <div className="rounded-md bg-green-50 p-4 dark:bg-green-900/30">
        <h3 className="text-sm font-medium text-green-800 dark:text-green-200">Password reset successful</h3>
        <p className="mt-2 text-sm text-green-700 dark:text-green-300">
          {message} Redirecting to login...
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
          New Password
        </label>
        <Input
          type="password"
          required
          minLength={8}
          className="mt-1"
          placeholder="••••••••"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />
      </div>

      <Button type="submit" className="w-full" disabled={status === "loading"}>
        {status === "loading" ? "Resetting..." : "Reset password"}
      </Button>
    </form>
  );
}
