import { useUsersFeed } from "../api/queries/users";
import { UserFeed } from "../components/UserFeed";

export default function Users() {
  const q = useUsersFeed();
  return (
    <div>
      <h1 className="text-[28px] md:text-4xl font-bold tracking-tight text-[var(--color-ink)] mb-3">
        Пользователи
      </h1>
      <p className="text-[var(--color-muted)] mb-8 text-[15px] md:text-base">
        Те, кто делится добрыми делами на площадке.
      </p>
      <UserFeed query={q} />
    </div>
  );
}
