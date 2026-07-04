"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { postAcceptInvite } from "@/lib/api/auth";
import { setAuthToken } from "@/lib/auth/session";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function AcceptInvitePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      setError("Invalid or missing invitation token.");
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setIsLoading(true);
    setError("");

    try {
      const resp = await postAcceptInvite({ token, password });
      setAuthToken(resp.accessToken);
      // Wait a moment for token to be available
      setTimeout(() => {
        router.push("/");
      }, 50);
    } catch (err: any) {
      setError(err.message || "Failed to accept invite. It may be expired.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-950 p-4">
      <div className="w-full max-w-md space-y-8 rounded-xl bg-white dark:bg-zinc-900 p-8 shadow-sm border border-zinc-200 dark:border-zinc-800">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Join Team</h2>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            Create a password to accept your invitation
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/30">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Choose a password
              </label>
              <Input
                type="password"
                required
                minLength={8}
                className="mt-1"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={!token}
              />
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={isLoading || !token}>
            {isLoading ? "Joining..." : "Accept Invitation"}
          </Button>
        </form>
      </div>
    </div>
  );
}
