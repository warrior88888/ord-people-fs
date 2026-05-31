import type { UseInfiniteQueryResult } from "@tanstack/react-query";
import { useCallback } from "react";
import type { Paginated, PostLight } from "../api/types";
import { CenterSpinner, Spinner } from "./ui/Spinner";
import { PostCard } from "./PostCard";
import { useIntersection } from "../hooks/useIntersection";
import { ErrorAlert } from "./ui/ErrorAlert";

type Props = {
  query: UseInfiniteQueryResult<{ pages: Paginated<PostLight>[] }, Error>;
  emptyText?: string;
};

export function PostFeed({ query, emptyText = "Пока ничего нет" }: Props) {
  const { data, isLoading, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage } = query;

  const loadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) fetchNextPage();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const sentinelRef = useIntersection(loadMore, !!hasNextPage);

  if (isLoading) return <CenterSpinner />;
  if (isError) return <ErrorAlert className="my-4" error={error} title="Не удалось загрузить ленту" />;

  const items = data?.pages.flatMap((p) => p.items) ?? [];
  if (items.length === 0) return <p className="text-[var(--color-muted)] py-6">{emptyText}</p>;

  return (
    <div>
      <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 auto-rows-fr">
        {items.map((p) => (
          <PostCard key={p.pk} post={p} />
        ))}
      </div>
      <div ref={sentinelRef} className="h-12 flex items-center justify-center mt-4">
        {isFetchingNextPage && <Spinner />}
      </div>
    </div>
  );
}
