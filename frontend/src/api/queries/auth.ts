import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../client";
import type { LoginPayload, RegisterPayload, User } from "../types";

export const ME_KEY = ["me"] as const;

export function useMe() {
  return useQuery<User | null>({
    queryKey: ME_KEY,
    queryFn: async () => {
      try {
        return await api.get<User>("/users/me");
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) return null;
        throw err;
      }
    },
    staleTime: 60_000,
  });
}

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: LoginPayload) => api.post<Record<string, string>>("/auth/login", p),
    onSuccess: () => qc.invalidateQueries({ queryKey: ME_KEY }),
  });
}

export function useRegister() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: RegisterPayload) =>
      api.post<{ user_id: number; username: string }>("/auth/register", p),
    onSuccess: () => qc.invalidateQueries({ queryKey: ME_KEY }),
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<Record<string, string>>("/auth/logout"),
    onSuccess: () => {
      qc.setQueryData(ME_KEY, null);
      qc.invalidateQueries();
    },
  });
}
