import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../client";
import type { Comment, Paginated } from "../types";
import { PAGE_SIZE } from "../../lib/constants";

export function useComments(postId: number, enabled: boolean) {
  return useInfiniteQuery({
    queryKey: ["comments", postId] as const,
    enabled,
    initialPageParam: 0,
    queryFn: ({ pageParam, signal }) =>
      api.get<Paginated<Comment>>(
        `/posts/${postId}/comments`,
        { limit: PAGE_SIZE, offset: pageParam },
        signal
      ),
    getNextPageParam: (last) => {
      const next = last.offset + last.limit;
      return next < last.total ? next : undefined;
    },
  });
}

export function useCreateComment(postId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (text: string) => api.post<Comment>(`/posts/${postId}/comments`, { text }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["comments", postId] }),
  });
}

export function useUpdateComment(postId: number, commentId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (text: string) =>
      api.patch<Comment>(`/posts/${postId}/comments/${commentId}`, { text }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["comments", postId] }),
  });
}

export function useDeleteComment(postId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (commentId: number) =>
      api.del<void>(`/posts/${postId}/comments/${commentId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["comments", postId] }),
  });
}
