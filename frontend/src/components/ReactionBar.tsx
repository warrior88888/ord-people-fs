import { useNavigate, useLocation } from "react-router";
import type { Post } from "../api/types";
import { REACTIONS, type ReactionValue } from "../lib/constants";
import { useToggleReaction } from "../api/queries/posts";
import { useMe } from "../api/queries/auth";

export function ReactionBar({ post }: { post: Post }) {
  const me = useMe();
  const navigate = useNavigate();
  const location = useLocation();
  const toggle = useToggleReaction(post.pk);

  function handle(r: ReactionValue) {
    if (!me.data) {
      navigate(`/login?next=${encodeURIComponent(location.pathname)}`);
      return;
    }
    toggle.mutate(r);
  }

  return (
    <div className="flex flex-wrap gap-2">
      {REACTIONS.map((r) => {
        const active = post.my_reaction === r.value;
        const count = post.reactions[r.value as keyof typeof post.reactions];
        return (
          <button
            key={r.value}
            onClick={() => handle(r.value)}
            disabled={toggle.isPending}
            className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 transition-all ${
              active
                ? "bg-brand text-white border-brand shadow-[0_2px_10px_-3px_rgba(31,111,229,0.5)]"
                : "bg-white text-[var(--color-ink)] border-[var(--color-border)] hover:border-brand hover:-translate-y-px"
            }`}
            aria-pressed={active}
            aria-label={r.label}
            title={r.label}
          >
            <span className="text-xl leading-none">{r.emoji}</span>
            <span className="tabular-nums text-sm font-medium">{count}</span>
          </button>
        );
      })}
    </div>
  );
}
