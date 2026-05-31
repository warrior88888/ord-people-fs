export const PAGE_SIZE = 20;

// Keep in sync with backend ALLOWED_IMAGE_CONTENT_TYPES and IMAGE_INPUT_MAX_SIZE.
// `image/*` already covers most mobile pickers, but iOS Safari and some Android
// browsers won't show files of a given type unless we name the extension or
// MIME explicitly. We list every realistic camera/share-sheet format here so
// HEIC, AVIF, etc. are always tappable.
export const IMAGE_MAX_BYTES = 12 * 1024 * 1024;
export const IMAGE_MAX_LABEL = "12 МБ";
export const IMAGE_ACCEPT = [
  "image/*",
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
  "image/heic",
  "image/heif",
  "image/avif",
  "image/bmp",
  "image/tiff",
  ".jpg",
  ".jpeg",
  ".png",
  ".webp",
  ".gif",
  ".heic",
  ".heif",
  ".avif",
  ".bmp",
  ".tif",
  ".tiff",
].join(",");

export const CATEGORIES = [
  { value: "story", label: "История" },
  { value: "event", label: "Мероприятие" },
  { value: "help", label: "Помощь" },
  { value: "volunteer", label: "Волонтёрство" },
  { value: "news", label: "Новости" },
] as const;

export type CategoryValue = (typeof CATEGORIES)[number]["value"];

export const REACTIONS = [
  { value: "like", label: "Нравится", emoji: "❤️" },
  { value: "support", label: "Поддерживаю", emoji: "🤝" },
  { value: "inspiring", label: "Вдохновляет", emoji: "🌟" },
] as const;

export type ReactionValue = (typeof REACTIONS)[number]["value"];

export function categoryLabel(value: string): string {
  return CATEGORIES.find((c) => c.value === value)?.label ?? value;
}
