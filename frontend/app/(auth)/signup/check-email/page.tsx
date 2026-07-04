"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

export default function CheckEmailPage() {
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "your email address";

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-950 p-4">
      <div className="w-full max-w-md space-y-8 rounded-xl bg-white dark:bg-zinc-900 p-8 shadow-sm border border-zinc-200 dark:border-zinc-800 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
          <svg className="h-6 w-6 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
          </svg>
        </div>
        
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Check your email</h2>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            We've sent a verification link to <span className="font-semibold text-zinc-900 dark:text-zinc-100">{email}</span>. 
            Please click the link to verify your account and sign in.
          </p>
        </div>

        <div className="mt-6 text-sm text-zinc-600 dark:text-zinc-400">
          <p>Didn't receive the email?</p>
          <p className="mt-1">
            <Link href="/login" className="font-semibold text-blue-600 hover:text-blue-500 dark:text-blue-400">
              Return to login to resend
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
