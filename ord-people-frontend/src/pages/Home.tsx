import { useState } from "react";
import { usePostsFeed, type PostFilters } from "../api/queries/posts";
import { PostFeed } from "../components/PostFeed";
import { Filters } from "../components/Filters";

export default function Home() {
  const [filters, setFilters] = useState<PostFilters>({});
  const feed = usePostsFeed(filters);

  return (
    <div>
      <section className="mb-8 md:mb-10">
        <h1 className="text-[28px] md:text-4xl font-bold text-[var(--color-ink)] leading-tight tracking-tight max-w-3xl">
          Истории, мероприятия и помощь простых людей
        </h1>
        <p className="mt-3 text-[var(--color-muted)] text-[15px] md:text-base max-w-2xl leading-relaxed">
          Новости сообщества: волонтёры, врачи и неравнодушные рассказывают о своих делах
          и приглашают присоединиться.
        </p>
      </section>

      <Filters value={filters} onChange={setFilters} />
      <PostFeed query={feed} emptyText="Пока нет проектов. Создайте первый!" />
    </div>
  );
}
