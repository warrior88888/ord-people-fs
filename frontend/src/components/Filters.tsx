import { useTags } from "../api/queries/tags";
import { CATEGORIES } from "../lib/constants";
import type { PostFilters } from "../api/queries/posts";

type Props = {
  value: PostFilters;
  onChange: (v: PostFilters) => void;
};

export function Filters({ value, onChange }: Props) {
  const tags = useTags();

  function toggleTag(id: number) {
    const set = new Set(value.tag_ids ?? []);
    if (set.has(id)) set.delete(id);
    else set.add(id);
    onChange({ ...value, tag_ids: set.size ? Array.from(set) : undefined });
  }

  function reset() {
    onChange({});
  }

  const active =
    !!value.category || !!value.tag_ids?.length || !!value.date_from || !!value.date_to;

  return (
    <div className="mb-8 border-b border-[var(--color-border)] pb-6">
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[180px]">
          <label className="block text-[11px] uppercase tracking-wider text-[var(--color-muted)] mb-1">
            Категория
          </label>
          <select
            className="select"
            value={value.category ?? ""}
            onChange={(e) => onChange({ ...value, category: e.target.value || undefined })}
          >
            <option value="">Любая</option>
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[11px] uppercase tracking-wider text-[var(--color-muted)] mb-1">
            Дата от
          </label>
          <input
            type="date"
            className="input"
            value={value.date_from?.slice(0, 10) ?? ""}
            onChange={(e) =>
              onChange({
                ...value,
                date_from: e.target.value ? `${e.target.value}T00:00:00` : undefined,
              })
            }
          />
        </div>

        <div>
          <label className="block text-[11px] uppercase tracking-wider text-[var(--color-muted)] mb-1">
            Дата до
          </label>
          <input
            type="date"
            className="input"
            value={value.date_to?.slice(0, 10) ?? ""}
            onChange={(e) =>
              onChange({
                ...value,
                date_to: e.target.value ? `${e.target.value}T23:59:59` : undefined,
              })
            }
          />
        </div>

        {active && (
          <button onClick={reset} className="text-sm text-[var(--color-muted)] hover:text-[var(--color-ink)] transition-colors py-2 px-2">
            Сбросить
          </button>
        )}
      </div>

      {!tags.isLoading && (tags.data?.length ?? 0) > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {(tags.data ?? []).map((t) => {
            const on = value.tag_ids?.includes(t.pk);
            return (
              <button
                key={t.pk}
                onClick={() => toggleTag(t.pk)}
                className={`tag-pill ${on ? "!bg-[var(--color-ink)] !text-white !border-[var(--color-ink)]" : ""}`}
                type="button"
              >
                {t.name}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
