import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "../client";
import type { Bio, BioUpdate, Paginated, User, UserLight, UserUpdate } from "../types";
import { PAGE_SIZE } from "../../lib/constants";
import { ME_KEY } from "./auth";

export function useUsersFeed() {
  return useInfiniteQuery({
    queryKey: ["users"] as const,
    initialPageParam: 0,
    queryFn: ({ pageParam, signal }) =>
      api.get<Paginated<UserLight>>(
        "/users",
        { limit: PAGE_SIZE, offset: pageParam },
        signal
      ),
    getNextPageParam: (last) => {
      const next = last.offset + last.limit;
      return next < last.total ? next : undefined;
    },
  });
}

export function useUser(username: string | undefined) {
  return useQuery({
    queryKey: ["user", username],
    enabled: !!username,
    queryFn: () => api.get<User>(`/users/${encodeURIComponent(username!)}`),
  });
}

export function useUpdateMe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: UserUpdate) => api.patch<User>("/users/me", p),
    onSuccess: (user) => {
      qc.setQueryData(ME_KEY, user);
      qc.invalidateQueries({ queryKey: ["user", user.username] });
      qc.invalidateQueries({ queryKey: ["users"] });
    },
  });
}

export function useUpdateBio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: BioUpdate) => api.put<Bio>("/users/me/bio", p),
    onSuccess: () => invalidateMyProfileEverywhere(qc),
  });
}

function invalidateMyProfileEverywhere(qc: ReturnType<typeof useQueryClient>) {
  const me = qc.getQueryData<User | null>(ME_KEY);
  qc.invalidateQueries({ queryKey: ME_KEY });
  qc.invalidateQueries({ queryKey: ["users"] });
  if (me?.username) {
    qc.invalidateQueries({ queryKey: ["user", me.username] });
  }
}

export function useUploadAvatar() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.upload<{ avatar_url: string }>("/users/me/avatar", file, "PUT"),
    onSuccess: () => invalidateMyProfileEverywhere(qc),
  });
}

export function useDeleteAvatar() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.del<void>("/users/me/avatar"),
    onSuccess: () => invalidateMyProfileEverywhere(qc),
  });
}

export function useDeleteMe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.del<void>("/users/me"),
    onSuccess: () => {
      qc.setQueryData(ME_KEY, null);
      qc.invalidateQueries();
    },
  });
}
