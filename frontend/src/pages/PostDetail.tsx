import { Link, useParams } from "react-router";
import { usePost } from "../api/queries/posts";
import { useMe } from "../api/queries/auth";
import { CenterSpinner } from "../components/ui/Spinner";
import { Avatar } from "../components/Avatar";
import { categoryLabel } from "../lib/constants";
import { formatDateLong } from "../lib/format";
import { MEDIA_BASE_URL } from "../api/client";
import { DefaultCover } from "../components/DefaultCover";
import { ReactionBar } from "../components/ReactionBar";
import { CommentList } from "../components/CommentList";
import { ErrorAlert } from "../components/ui/ErrorAlert";

function resolveMedia(url?: string | null) {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  return `${MEDIA_BASE_URL}${url.startsWith("/") ? "" : "/"}${url}`;
}

export default function PostDetail() {
  const { id } = useParams();
  const postId = id ? Number(id) : null;
  const q = usePost(postId);
  const me = useMe();

  if (q.isLoading) return <CenterSpinner />;
  if (q.isError || !q.data) {
    return (
      <div className="max-w-2xl mx-auto">
        <ErrorAlert error={q.error ?? "Проект не найден."} title="Проект не найден" />
      </div>
    );
  }

  const post = q.data;
  const photo = resolveMedia(post.photo_url);
  const isAuthor = me.data?.pk === post.author.pk;
  const isAdmin = !!me.data?.is_admin;
  const canOpenEditor = isAuthor || isAdmin;

  return (
    <article className="max-w-3xl mx-auto">
      <div className="text-sm mb-6">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-[var(--color-muted)] hover:text-[var(--color-ink)] transition-colors"
        >
          <span aria-hidden="true">←</span> Ко всем проектам
        </Link>
      </div>

      <header className="mb-6">
        <div className="flex items-center gap-3 text-[12px] text-[var(--color-muted)] mb-4">
          <span className="font-medium text-[var(--color-ink)]">
            {formatDateLong(post.created_at)}
          </span>
          <span aria-hidden="true" className="h-1 w-1 rounded-full bg-[var(--color-border)]" />
          <span className="uppercase tracking-wider">
            {categoryLabel(post.category)}
          </span>
        </div>

        <h1 className="text-[28px] md:text-[40px] font-bold text-[var(--color-ink)] leading-[1.15] tracking-tight break-words">
          {post.name}
        </h1>

        <Link
          to={`/users/${post.author.username}`}
          className="mt-5 inline-flex items-center gap-3 group"
        >
          <Avatar
            url={post.author.avatar_url}
            username={post.author.username}
            firstName={post.author.first_name}
            lastName={post.author.last_name}
            size={40}
          />
          <span>
            <span className="block text-sm font-semibold text-[var(--color-ink)] group-hover:text-brand leading-tight transition-colors">
              {post.author.first_name} {post.author.last_name}
            </span>
            <span className="block text-[12px] text-[var(--color-muted)] leading-tight">
              @{post.author.username}
            </span>
          </span>
        </Link>
      </header>

      <div className="relative w-full overflow-hidden rounded-lg bg-[var(--color-surface)] aspect-[16/9] mb-8">
        {photo ? (
          <img
            src={photo}
            alt={post.name}
            className="absolute inset-0 h-full w-full object-cover"
          />
        ) : (
          <DefaultCover
            category={post.category}
            tagName={post.tags[0]?.name}
            className="absolute inset-0"
            showLabel={false}
          />
        )}
      </div>

      <div className="text-[var(--color-ink)] text-[17px] md:text-[18px] leading-[1.75] whitespace-pre-wrap break-words">
        {post.description}
      </div>

      {post.external_url && (
        <a
          className="mt-5 inline-flex items-center gap-1.5 text-brand font-medium hover:underline"
          href={post.external_url}
          target="_blank"
          rel="noreferrer"
        >
          Перейти по ссылке
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M7 17L17 7" />
            <path d="M8 7h9v9" />
          </svg>
        </a>
      )}

      {post.tags.length > 0 && (
        <div className="mt-8 flex flex-wrap gap-2">
          {post.tags.map((t) => (
            <span key={t.pk} className="tag-pill">
              #{t.name}
            </span>
          ))}
        </div>
      )}

      <div className="mt-10 pt-6 border-t border-[var(--color-border)]">
        <p className="text-[11px] uppercase tracking-[0.2em] text-[var(--color-muted)] mb-3">
          Поддержите проект
        </p>
        <ReactionBar post={post} />
      </div>

      {canOpenEditor && (
        <div className="mt-8">
          <Link to={`/posts/${post.pk}/edit`} className="btn btn-outline">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z" />
            </svg>
            Редактировать
          </Link>
        </div>
      )}

      <section className="mt-12 pt-8 border-t border-[var(--color-border)]">
        <CommentList postId={post.pk} />
      </section>
    </article>
  );
}
