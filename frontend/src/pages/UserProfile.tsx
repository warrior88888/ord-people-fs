import { useState } from "react";
import { Link, useParams } from "react-router";
import { useUser } from "../api/queries/users";
import { useMe } from "../api/queries/auth";
import { useUserPosts } from "../api/queries/posts";
import { Avatar } from "../components/Avatar";
import { CenterSpinner } from "../components/ui/Spinner";
import { PostFeed } from "../components/PostFeed";
import { formatDateLong } from "../lib/format";
import { ProfileEditor } from "./ProfileEditor";
import { ErrorAlert } from "../components/ui/ErrorAlert";

export default function UserProfile() {
  const { username = "" } = useParams();
  const userQ = useUser(username);
  const me = useMe();

  const [showPosts, setShowPosts] = useState(false);
  const [editing, setEditing] = useState(false);
  const postsQ = useUserPosts(username, showPosts);

  if (userQ.isLoading) return <CenterSpinner />;
  if (userQ.isError || !userQ.data) {
    return (
      <div className="max-w-xl">
        <ErrorAlert
          error={userQ.error ?? "Пользователь не найден."}
          title="Пользователь не найден"
        />
      </div>
    );
  }

  const u = userQ.data;
  const isMe = me.data?.pk === u.pk;

  if (editing && isMe) {
    return <ProfileEditor user={u} onDone={() => setEditing(false)} />;
  }

  return (
    <div className="max-w-3xl">
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row items-start gap-4">
          <Avatar
            url={u.avatar_url}
            username={u.username}
            firstName={u.first_name}
            lastName={u.last_name}
            size={96}
          />
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold">
              {u.first_name} {u.last_name}
            </h1>
            <p className="text-[var(--color-muted)]">@{u.username}</p>
            <p className="text-xs text-[var(--color-muted)] mt-1">
              На площадке с {formatDateLong(u.created_at)}
            </p>
            {u.is_admin && (
              <span className="inline-block mt-2 tag-pill !text-brand !border-brand">
                Администратор
              </span>
            )}
            {u.bio?.about && (
              <p className="mt-3 whitespace-pre-wrap">{u.bio.about}</p>
            )}
          </div>
        </div>

        {u.bio && (u.bio.phone_number || u.bio.email || u.bio.vk_link || u.bio.max_link) && (
          <div className="mt-6 rounded-xl border border-[var(--color-brand)]/20 bg-gradient-to-br from-[var(--color-surface)] to-white p-4">
            <p className="text-[11px] uppercase tracking-wider font-semibold text-[var(--color-brand-deep)] mb-3">
              Контакты
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {u.bio.phone_number && (
                <ContactItem href={`tel:${u.bio.phone_number}`} label="Телефон" value={u.bio.phone_number} />
              )}
              {u.bio.email && (
                <ContactItem href={`mailto:${u.bio.email}`} label="Email" value={u.bio.email} />
              )}
              {u.bio.vk_link && (
                <ContactItem
                  href={u.bio.vk_link}
                  external
                  label="VK"
                  value={u.bio.vk_link.replace(/^https?:\/\/(www\.)?/, "")}
                />
              )}
              {u.bio.max_link && (
                <ContactItem
                  href={u.bio.max_link}
                  external
                  label="Max"
                  value={u.bio.max_link.replace(/^https?:\/\/(www\.)?/, "")}
                />
              )}
            </div>
          </div>
        )}

        <div className="mt-5 flex flex-wrap gap-2">
          <button onClick={() => setShowPosts((v) => !v)} className="btn btn-outline">
            {showPosts ? "Скрыть проекты" : "Проекты"}
          </button>
          {isMe && (
            <button onClick={() => setEditing(true)} className="btn btn-outline">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z" />
              </svg>
              Изменить профиль
            </button>
          )}
          {!isMe && (
            <Link to="/" className="btn btn-ghost">
              ← К ленте
            </Link>
          )}
        </div>
      </div>

      {showPosts && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-3">Проекты пользователя</h2>
          <PostFeed query={postsQ} emptyText="У пользователя пока нет проектов." />
        </div>
      )}
    </div>
  );
}

type ContactItemProps = {
  href: string;
  label: string;
  value: string;
  external?: boolean;
};

function ContactItem({ href, label, value, external }: ContactItemProps) {
  return (
    <a
      href={href}
      target={external ? "_blank" : undefined}
      rel={external ? "noreferrer" : undefined}
      className="group relative flex flex-col leading-tight rounded-lg bg-white border border-[var(--color-border)] pl-4 pr-3 py-2.5 hover:border-[var(--color-brand)] hover:shadow-sm transition-all min-w-0"
    >
      <span
        aria-hidden
        className="absolute left-0 top-2 bottom-2 w-[3px] rounded-full bg-[var(--color-brand)] opacity-60 group-hover:opacity-100 transition-opacity"
      />
      <span className="text-[10px] uppercase tracking-wider text-[var(--color-muted)]">
        {label}
      </span>
      <span className="text-sm font-medium text-[var(--color-ink)] truncate group-hover:text-[var(--color-brand-deep)] transition-colors">
        {value}
      </span>
    </a>
  );
}
