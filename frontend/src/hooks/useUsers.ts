import { useCallback } from "react";
import { usePolling } from "./usePolling";
import { getUsers } from "../api/client";
import { User } from "../types";

export function useUsers() {
  const fetchFn = useCallback(() => getUsers(), []);
  return usePolling<User[]>(fetchFn, 60000);
}
