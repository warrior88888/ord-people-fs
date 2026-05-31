import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "../client";
import type {
  Paginated,
  Post,
  PostCreate,
  PostLight,
  PostUpdate,
  ReactionCounts,
  ReactionValue,
} from "../types";
import { PAGE_SIZE } from "../../lib/constants";

export type PostFilters = {
  category?: string;
  tag_ids?: number[];
  date_from?: string;
  date_to?: string;
};

export function usePostsFeed(filters: PostFilters = {}) {
  return useInfiniteQuery({
    queryKey: ["posts", filters] as const,
    initialPageParam: 0,
    queryFn: ({ pageParam, signal }) =>
      api.get<Paginated<PostLight>>(
        "/posts",
        { ...filters, limit: PAGE_SIZE, offset: pageParam },
        signal
      ),
    getNextPageParam: (last) => {
      const next = last.offset + last.limit;
      return next < last.total ? next : undefined;
    },
  });
}

export function useUserPosts(username: string, enabled: boolean) {
  return useInfiniteQuery({
    queryKey: ["user-posts", username] as const,
    enabled,
    initialPageParam: 0,
    queryFn: ({ pageParam, signal }) =>
      api.get<Paginated<PostLight>>(
        `/users/${encodeURIComponent(username)}/posts`,
        { limit: PAGE_SIZE, offset: pageParam },
        signal
      ),
    getNextPageParam: (last) => {
      const next = last.offset + last.limit;
      return next < last.total ? next : undefined;
    },
  });
}

export function usePost(postId: number | null) {
  return useQuery({
    queryKey: ["post", postId],
    enabled: postId != null,
    queryFn: () => api.get<Post>(`/posts/${postId}`),
  });
}

export function useCreatePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: PostCreate) => api.post<Post>("/posts", p),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["posts"] }),
  });
}

export function useUpdatePost(postId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: PostUpdate) => api.patch<Post>(`/posts/${postId}`, p),
    onSuccess: (data) => {
      qc.setQueryData(["post", postId], data);
      qc.invalidateQueries({ queryKey: ["posts"] });
    },
  });
}

export function useDeletePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (postId: number) => api.del<void>(`/posts/${postId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["posts"] }),
  });
}

export function useUploadPostPhoto(postId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.upload<{ photo_url: string }>(`/posts/${postId}/photo`, file, "POST"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["post", postId] });
      qc.invalidateQueries({ queryKey: ["posts"] });
    },
  });
}

export function useDeletePostPhoto(postId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.del<void>(`/posts/${postId}/photo`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["post", postId] });
      qc.invalidateQueries({ queryKey: ["posts"] });
    },
  });
}

export function useToggleReaction(postId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reaction: ReactionValue) =>
      api.post<{ counts: ReactionCounts; my_reaction: ReactionValue | null }>(
        `/posts/${postId}/reactions`,
        { reaction }
      ),
    onSuccess: (data) => {
      qc.setQueryData<Post | undefined>(["post", postId], (old) =>
        old ? { ...old, reactions: data.counts, my_reaction: data.my_reaction } : old
      );
    },
  });
}
