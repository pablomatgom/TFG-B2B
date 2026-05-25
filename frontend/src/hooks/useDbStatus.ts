import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";

type DbStatus = "checking" | "connected" | "disconnected";

export function useDbStatus(): DbStatus {
  const [status, setStatus] = useState<DbStatus>("checking");

  useEffect(() => {
    const check = async () => {
      try {
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), 4000);
        const res = await fetch(`${API_BASE}/api/health`, { signal: ctrl.signal });
        clearTimeout(timer);
        setStatus(res.ok ? "connected" : "disconnected");
      } catch {
        setStatus("disconnected");
      }
    };

    check();
    const id = setInterval(check, 15000);
    return () => clearInterval(id);
  }, []);

  return status;
}