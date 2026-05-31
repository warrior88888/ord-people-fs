import { Link } from "react-router";
import type { UserLight } from "../api/types";
import { Avatar } from "./Avatar";

export function UserCard({ user }: { user: UserLight }) {
  return (
    <Link
      to={`/users/${user.username}`}
      className="group flex items-center gap-3 rounded-lg border border-[var(--color-border)] bg-white p-3.5 transition-colors hover:border-slate-300 hover:bg-[var(--color-surface)]"
    >
      <Avatar
        url={user.avatar_url}
        username={user.username}
        firstName={user.first_name}
        lastName={user.last_name}
        size={48}
      />
      <div className="min-w-0">
        <p className="font-semibold text-[var(--color-ink)] truncate group-hover:text-brand transition-colors">
          {user.first_name} {user.last_name}
        </p>
        <p className="text-[13px] text-[var(--color-muted)] truncate">@{user.username}</p>
      </div>
    </Link>
  );
}
