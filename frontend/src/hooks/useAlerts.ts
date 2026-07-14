import { useCallback, useEffect } from "react";
import { usePolling } from "./usePolling";
import { getAlerts } from "../api/client";
import { Alert } from "../types";

export function useAlerts(statusFilter?: string, severityFilter?: string) {
  const fetchFn = useCallback(
    () => getAlerts(statusFilter, severityFilter),
    [statusFilter, severityFilter]
  );
  const polling = usePolling<Alert[]>(fetchFn, 15000, [statusFilter, severityFilter]);

  useEffect(() => {
    const handleAlertUpdate = (event: Event) => {
      const newAlert = (event as CustomEvent).detail as Alert;

      // Local filter verification matches status and severity parameters
      const matchesStatus = !statusFilter || newAlert.status.toLowerCase() === statusFilter.toLowerCase();
      const matchesSeverity = !severityFilter || newAlert.severity.toLowerCase() === severityFilter.toLowerCase();

      if (matchesStatus && matchesSeverity) {
        polling.setData((prev) => {
          if (!prev) return [newAlert];
          const exists = prev.some((a) => a.id === newAlert.id);
          if (exists) {
            return prev.map((a) => (a.id === newAlert.id ? { ...a, ...newAlert } : a));
          }
          return [newAlert, ...prev];
        });
      }
    };

    window.addEventListener("zt-alert-update", handleAlertUpdate);
    return () => window.removeEventListener("zt-alert-update", handleAlertUpdate);
  }, [polling.setData, statusFilter, severityFilter]);

  return polling;
}

