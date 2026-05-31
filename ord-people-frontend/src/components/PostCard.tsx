import { Link } from "react-router";
import type { PostLight } from "../api/types";
import { categoryLabel } from "../lib/constants";
import { formatDateParts } from "../lib/format";
import { DefaultCover } from "./DefaultCover";
import { MEDIA_BASE_URL } from "../api/client";

function resolveMedia(url?: string | null): string | null {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  return `${MEDIA_BASE_URL}${url.startsWith("/") ? "" : "/"}${url}`;
}

type Props = { post: PostLight; wide?: boolean };

export function PostCard({ post }: Props) {
  const { day, month } = formatDateParts(post.created_at);
  const photo = resolveMedia(post.photo_url);

  return (
    <Link
      to={`/posts/${post.pk}`}
      className="group flex h-full flex-col overflow-hidden rounded-lg border border-[var(--color-border)] bg-white transition-shadow duration-150 hover:shadow-[0_6px_24px_-12px_rgba(15,23,42,0.18)]"
    >
      <div className="relative w-full overflow-hidden bg-[var(--color-surface)] aspect-[16/9]">
        {photo ? (
          <img
            src={photo}
            alt={post.name}
            loading="lazy"
            className="absolute inset-0 h-full w-full object-cover"
          />
        ) : (
          <DefaultCover category={post.category} className="absolute inset-0" />
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2.5 p-4 md:p-5">
        <div className="flex items-center gap-2 text-[12px] text-[var(--color-muted)]">
          <span className="font-medium text-[var(--color-ink)] tabular-nums">
            {day} {month}
          </span>
          <span aria-hidden="true" className="h-1 w-1 rounded-full bg-[var(--color-border)]" />
          <span className="uppercase tracking-wider text-[11px]">
            {categoryLabel(post.category)}
          </span>
        </div>

        <h3 className="font-semibold text-[var(--color-ink)] text-[17px] leading-snug clamp-2 group-hover:text-brand transition-colors">
          {post.name}
        </h3>
      </div>
    </Link>
  );
}
