"use client";

import { Suspense } from "react";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { postVerifyEmail } from "@/lib/api/auth";

export const dynamic = "force-dynamic";

function VerifyEmailPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token provided.");
      return;
    }

    let isMounted = true;
    
    postVerifyEmail({ token })
      .then((resp) => {
        if (isMounted) {
          setStatus("success");
          setMessage(resp.message);
          setTimeout(() => {
            router.push("/login");
          }, 3000);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setStatus("error");
          setMessage(err.message || "Verification failed. The link might be invalid or expired.");
        }
      });

    return () => {
      isMounted = false;
    };
  }, [token, router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-950 p-4">
      <div className="w-full max-w-md space-y-8 rounded-xl bg-white dark:bg-zinc-900 p-8 shadow-sm border border-zinc-200 dark:border-zinc-800 text-center">
        {status === "loading" && (
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Verifying Email...</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Please wait while we verify your email address.
            </p>
          </div>
        )}
        
        {status === "success" && (
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-green-600 dark:text-green-400">Email Verified!</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              {message} Redirecting you to login...
            </p>
          </div>
        )}
        
        {status === "error" && (
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-red-600 dark:text-red-400">Verification Failed</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              {message}
            </p>
            <div className="mt-6">
              <Link href="/login" className="text-sm font-semibold text-blue-600 hover:text-blue-500 dark:text-blue-400">
                Return to login
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <VerifyEmailPageContent />
    </Suspense>
  );
}
