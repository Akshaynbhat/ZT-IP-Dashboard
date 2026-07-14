import { useEffect, useState, useRef, useCallback } from "react";

export function usePolling<T>(
  fetchFn: () => Promise<T>,
  intervalMs: number,
  deps: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Keep a reference to the fetch function to prevent dependency loops
  const fetchRef = useRef(fetchFn);

  useEffect(() => {
    fetchRef.current = fetchFn;
  }, [fetchFn]);

  const executeFetch = useCallback(async (isFirstLoad: boolean) => {
    if (isFirstLoad) {
      setLoading(true);
    }
    try {
      const result = await fetchRef.current();
      setData(result);
      setError(null);
    } catch (err: any) {
      console.error("Polling error caught:", err);
      setError(err?.message || "Failed to retrieve data from server");
    } finally {
      if (isFirstLoad) {
        setLoading(false);
      }
    }
  }, []);

  const refresh = useCallback(() => {
    executeFetch(true);
  }, [executeFetch]);

  useEffect(() => {
    // Initial immediate invocation
    executeFetch(true);

    // Setup periodic execution interval
    const timer = setInterval(() => {
      executeFetch(false);
    }, intervalMs);

    // Clean up interval subscription on component unmount
    return () => clearInterval(timer);
  }, [intervalMs, executeFetch, ...deps]);

  return { data, setData, loading, error, refresh };
}
