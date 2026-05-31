import { MEDIA_BASE_URL } from "../api/client";
import { hashString, initialsOf } from "../lib/format";

type Props = {
  url?: string | null;
  username: string;
  firstName?: string;
  lastName?: string;
  size?: number;
  className?: string;
};

const PALETTE = ["#1f6fe5", "#3aa6e0", "#0f4faa", "#4f86e8", "#2563eb", "#0ea5b7"];

function resolveUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  return `${MEDIA_BASE_URL}${url.startsWith("/") ? "" : "/"}${url}`;
}

export function Avatar({ url, username, firstName, lastName, size = 40, className = "" }: Props) {
  const resolved = resolveUrl(url);
  const initials = initialsOf(firstName, lastName, username);
  const color = PALETTE[hashString(username) % PALETTE.length];

  if (resolved) {
    return (
      <img
        src={resolved}
        alt={username}
        loading="lazy"
        width={size}
        height={size}
        className={`rounded-full object-cover border border-[var(--color-border)] ${className}`}
        style={{ width: size, height: size }}
      />
    );
  }

  const fontSize = Math.round(size * 0.42);
  return (
    <div
      className={`inline-flex items-center justify-center rounded-full text-white font-semibold select-none ${className}`}
      style={{ width: size, height: size, background: color, fontSize }}
      aria-label={username}
    >
      {initials}
    </div>
  );
}
