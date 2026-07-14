import { useCallback, useEffect } from "react";
import { usePolling } from "./usePolling";
import { getScores } from "../api/client";
import { TrustScore } from "../types";

export function useScores() {
  const fetchFn = useCallback(() => getScores(), []);
  const polling = usePolling<TrustScore[]>(fetchFn, 30000);

  useEffect(() => {
    const handleScoreUpdate = (event: Event) => {
      const newScore = (event as CustomEvent).detail;
      polling.setData((prev) => {
        if (!prev) return [newScore];
        const exists = prev.some((s) => s.user_id === newScore.user_id);
        let updatedList;
        if (exists) {
          updatedList = prev.map((s) => (s.user_id === newScore.user_id ? { ...s, ...newScore } : s));
        } else {
          updatedList = [...prev, newScore];
        }
        // Sort lowest trust score first
        return updatedList.sort((a, b) => a.trust_score - b.trust_score);
      });
    };

    window.addEventListener("zt-score-update", handleScoreUpdate);
    return () => window.removeEventListener("zt-score-update", handleScoreUpdate);
  }, [polling.setData]);

  return polling;
}

