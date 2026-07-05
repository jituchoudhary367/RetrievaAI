"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setAuthToken } from "@/lib/auth/session";
import { Hexagon } from "lucide-react";

function OAuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  useEffect(() => {
    if (token) {
      setAuthToken(token);
      // Brief delay to ensure cookie/storage sets
      setTimeout(() => {
        router.push("/chat");
      }, 500);
    } else {
      router.push("/login?error=OAuthTokenMissing");
    }
  }, [token, router]);

  return (
    <div className="flex flex-col items-center justify-center space-y-6">
      <div className="flex items-center justify-center relative w-16 h-16 animate-pulse">
        <Hexagon className="w-16 h-16 text-primary absolute fill-primary/20" />
        <div className="w-4 h-4 bg-primary rounded-full relative z-10 shadow-[0_0_15px_rgba(16,185,129,0.5)]" />
      </div>
      <h2 className="text-xl font-bold text-white tracking-tight">
        Authenticating...
      </h2>
      <p className="text-sm text-muted-foreground font-medium">
        Please wait while we log you in securely.
      </p>
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center space-y-6">
        <h2 className="text-xl font-bold text-white">Loading...</h2>
      </div>
    }>
      <OAuthCallbackContent />
    </Suspense>
  );
}
