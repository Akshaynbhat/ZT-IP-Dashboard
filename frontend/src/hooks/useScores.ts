import { useCallback } from "react";
import { usePolling } from "./usePolling";
import { getScores } from "../api/client";
import { TrustScore } from "../types";

export function useScores() {
  const fetchFn = useCallback(() => getScores(), []);
  return usePolling<TrustScore[]>(fetchFn, 30000);
}
