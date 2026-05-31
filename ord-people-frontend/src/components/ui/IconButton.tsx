import type { ButtonHTMLAttributes } from "react";

type Variant = "edit" | "delete" | "ghost";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  label: string;
  icon: "pencil" | "trash";
  size?: number;
};

const VARIANT_CLASSES: Record<Variant, string> = {
  edit:
    "text-[var(--color-brand-deep)] bg-[#eaf2ff] hover:bg-[#dde9ff] border-[#cfe0ff] hover:border-brand",
  delete:
    "text-[#b91c1c] bg-[#fef2f2] hover:bg-[#fee2e2] border-[#fecaca] hover:border-[#ef4444]",
  ghost:
    "text-[var(--color-muted)] bg-white hover:bg-[var(--color-surface)] border-[var(--color-border)]",
};

export function IconButton({
  variant = "ghost",
  label,
  icon,
  size = 18,
  className = "",
  ...rest
}: Props) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={`inline-flex items-center justify-center w-9 h-9 rounded-full border transition-all hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${className}`}
      {...rest}
    >
      <Icon name={icon} size={size} />
    </button>
  );
}

function Icon({ name, size }: { name: "pencil" | "trash"; size: number }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  if (name === "pencil") {
    return (
      <svg {...common}>
        <path d="M12 20h9" />
        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <path d="M3 6h18" />
      <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6M14 11v6" />
    </svg>
  );
}
