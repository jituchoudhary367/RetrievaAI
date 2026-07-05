"use client";

import { Suspense } from "react";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm";

export const dynamic = "force-dynamic";

function ResetPasswordPageContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-950 p-4">
      <div className="w-full max-w-md space-y-8 rounded-xl bg-white dark:bg-zinc-900 p-8 shadow-sm border border-zinc-200 dark:border-zinc-800">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Set new password</h2>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            Please enter your new password below.
          </p>
        </div>

        {token ? (
          <ResetPasswordForm token={token} />
        ) : (
          <div className="mt-8 rounded-md bg-red-50 p-4 dark:bg-red-900/30">
            <p className="text-sm text-red-800 dark:text-red-200">Invalid or missing reset token.</p>
          </div>
        )}

        <p className="text-center text-sm text-zinc-600 dark:text-zinc-400 mt-6">
          <Link href="/login" className="font-semibold text-blue-600 hover:text-blue-500 dark:text-blue-400">
            Return to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <ResetPasswordPageContent />
    </Suspense>
  );
}
