"use client";

import { useState } from "react";
import { postResendVerification } from "@/lib/api/auth";
import { Button } from "@/components/ui/button";

interface VerifyEmailNoticeProps {
  email: string;
}

export function VerifyEmailNotice({ email }: VerifyEmailNoticeProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleResend = async () => {
    setIsLoading(true);
    setMessage("");
    setError("");
    
    try {
      const resp = await postResendVerification({ email });
      setMessage(resp.message);
    } catch (err: any) {
      setError(err.message || "Failed to resend email.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="rounded-md bg-yellow-50 p-4 dark:bg-yellow-900/30">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Email Verification Required</h3>
          <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
            <p>
              Please check your email and verify your account before signing in.
            </p>
          </div>
          <div className="mt-4">
            <div className="-mx-2 -my-1.5 flex">
              <Button
                variant="outline"
                size="sm"
                onClick={handleResend}
                disabled={isLoading}
                className="bg-yellow-50 text-yellow-800 hover:bg-yellow-100 dark:bg-yellow-900/50 dark:text-yellow-200 dark:hover:bg-yellow-900"
              >
                {isLoading ? "Sending..." : "Resend verification email"}
              </Button>
            </div>
          </div>
          {message && (
            <p className="mt-2 text-sm text-green-700 dark:text-green-400">{message}</p>
          )}
          {error && (
            <p className="mt-2 text-sm text-red-700 dark:text-red-400">{error}</p>
          )}
        </div>
      </div>
    </div>
  );
}
