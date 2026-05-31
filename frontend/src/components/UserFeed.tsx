import { useCallback } from "react";
import type { UseInfiniteQueryResult } from "@tanstack/react-query";
import type { Paginated, UserLight } from "../api/types";
import { CenterSpinner, Spinner } from "./ui/Spinner";
import { UserCard } from "./UserCard";
import { useIntersection } from "../hooks/useIntersection";
import { ErrorAlert } from "./ui/ErrorAlert";

type Props = { query: UseInfiniteQueryResult<{ pages: Paginated<UserLight>[] }, Error> };

export function UserFeed({ query }: Props) {
  const { data, isLoading, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage } = query;

  const loadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) fetchNextPage();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const sentinelRef = useIntersection(loadMore, !!hasNextPage);

  if (isLoading) return <CenterSpinner />;
  if (isError) return <ErrorAlert className="my-4" error={error} title="Не удалось загрузить список" />;

  const items = data?.pages.flatMap((p) => p.items) ?? [];
  if (items.length === 0) return <p className="text-[var(--color-muted)] py-6">Пока никого нет</p>;

  return (
    <div>
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((u) => <UserCard key={u.pk} user={u} />)}
      </div>
      <div ref={sentinelRef} className="h-12 flex items-center justify-center mt-4">
        {isFetchingNextPage && <Spinner />}
      </div>
    </div>
  );
}
