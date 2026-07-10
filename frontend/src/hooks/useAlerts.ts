import { useCallback } from "react";
import { usePolling } from "./usePolling";
import { getAlerts } from "../api/client";
import { Alert } from "../types";

export function useAlerts(statusFilter?: string, severityFilter?: string) {
  const fetchFn = useCallback(
    () => getAlerts(statusFilter, severityFilter),
    [statusFilter, severityFilter]
  );
  return usePolling<Alert[]>(fetchFn, 15000, [statusFilter, severityFilter]);
}
