import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";

// This is a catch-all route that will match any URL that doesn't match other routes
export const Route = createFileRoute("/$")({
  component: CatchAllRoute,
});

function CatchAllRoute() {
  const navigate = useNavigate();

  useEffect(() => {
    navigate({ to: "/", replace: true });
  }, [navigate]);

  return (
    <div className="flex h-screen items-center justify-center bg-[#191a1a]">
      <div className="flex flex-col items-center gap-4">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
        <p className="text-sm text-slate-400">Redirecting...</p>
      </div>
    </div>
  );
}
