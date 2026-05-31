import type { CategoryValue } from "../api/types";

type Props = {
  category?: CategoryValue;
  tagName?: string;
  className?: string;
  showLabel?: boolean;
};

type Variant = {
  label: string;
  icon: IconName;
  from: string;
  to: string;
};

type IconName = "heart" | "stethoscope" | "shield" | "calendar" | "hands" | "news";

const VARIANTS: Record<CategoryValue, Variant> = {
  story:     { label: "История",     icon: "heart",       from: "#ec4899", to: "#1f6fe5" },
  event:     { label: "Мероприятие", icon: "calendar",    from: "#22d3ee", to: "#1f6fe5" },
  help:      { label: "Помощь",      icon: "hands",       from: "#10b981", to: "#0f4faa" },
  volunteer: { label: "Волонтёрство", icon: "shield",     from: "#f59e0b", to: "#1f6fe5" },
  news:      { label: "Новости",     icon: "news",        from: "#6366f1", to: "#0f4faa" },
};

const TAG_OVERRIDES: Record<string, Partial<Variant> & { icon?: IconName }> = {
  волонтёрство: { icon: "hands",       from: "#10b981", to: "#0f4faa", label: "Волонтёрство" },
  волонтерство: { icon: "hands",       from: "#10b981", to: "#0f4faa", label: "Волонтёрство" },
  медицина:     { icon: "stethoscope", from: "#06b6d4", to: "#1f6fe5", label: "Медицина" },
  врачи:        { icon: "stethoscope", from: "#06b6d4", to: "#1f6fe5", label: "Медицина" },
  герои:        { icon: "shield",      from: "#f43f5e", to: "#0f4faa", label: "Герои" },
  подвиги:      { icon: "shield",      from: "#f43f5e", to: "#0f4faa", label: "Подвиги" },
  мероприятия:  { icon: "calendar",    from: "#22d3ee", to: "#1f6fe5", label: "Мероприятия" },
  помощь:       { icon: "hands",       from: "#10b981", to: "#0f4faa", label: "Помощь" },
  новости:      { icon: "news",        from: "#6366f1", to: "#0f4faa", label: "Новости" },
};

function pick(category?: CategoryValue, tagName?: string): Variant {
  const base = category ? VARIANTS[category] : VARIANTS.story;
  if (tagName) {
    const key = tagName.toLowerCase().trim();
    const o = TAG_OVERRIDES[key];
    if (o) return { ...base, ...o };
  }
  return base;
}

function Icon({ name, size = 64 }: { name: IconName; size?: number }) {
  const stroke = "rgba(255,255,255,0.95)";
  const sw = 1.6;
  const common = {
    fill: "none",
    stroke,
    strokeWidth: sw,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...common} aria-hidden="true">
      {name === "heart" && (
        <path d="M12 21s-7-4.5-9-9.5C1.5 8 4 5 7 5c2 0 3.5 1 5 3 1.5-2 3-3 5-3 3 0 5.5 3 4 6.5-2 5-9 9.5-9 9.5z" />
      )}
      {name === "stethoscope" && (
        <>
          <path d="M6 3v6a4 4 0 0 0 8 0V3" />
          <path d="M6 3H4M16 3h-2" />
          <path d="M10 13v2a5 5 0 0 0 10 0v-2" />
          <circle cx="20" cy="11" r="2" />
        </>
      )}
      {name === "shield" && (
        <path d="M12 3l8 3v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3z" />
      )}
      {name === "calendar" && (
        <>
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M3 10h18M8 3v4M16 3v4" />
          <path d="M8 14h2M14 14h2M8 18h2M14 18h2" />
        </>
      )}
      {name === "hands" && (
        <>
          <path d="M7 13V8a1.5 1.5 0 0 1 3 0v4" />
          <path d="M10 12V6a1.5 1.5 0 0 1 3 0v6" />
          <path d="M13 12V7a1.5 1.5 0 0 1 3 0v7a6 6 0 0 1-12 0v-1" />
          <path d="M16 12V8.5a1.5 1.5 0 0 1 3 0V14" />
        </>
      )}
      {name === "news" && (
        <>
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <path d="M7 9h10M7 13h10M7 17h6" />
        </>
      )}
    </svg>
  );
}

export function DefaultCover({ category, tagName, className = "", showLabel = true }: Props) {
  const v = pick(category, tagName);
  return (
    <div
      className={`relative w-full h-full overflow-hidden ${className}`}
      style={{ background: `linear-gradient(135deg, ${v.from} 0%, ${v.to} 100%)` }}
      role="img"
      aria-label={v.label}
    >
      <div
        className="absolute inset-0 opacity-[0.18] pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 20%, rgba(255,255,255,.9) 0, transparent 35%), radial-gradient(circle at 80% 80%, rgba(255,255,255,.6) 0, transparent 40%)",
        }}
      />
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-white">
        <Icon name={v.icon} size={72} />
        {showLabel && (
          <span className="text-[11px] uppercase tracking-[0.35em] font-medium opacity-90">
            {v.label}
          </span>
        )}
      </div>
    </div>
  );
}
