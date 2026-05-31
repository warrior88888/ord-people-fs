export const PAGE_SIZE = 20;

// Keep in sync with backend ALLOWED_IMAGE_CONTENT_TYPES and IMAGE_INPUT_MAX_SIZE.
// HEIC/HEIF entries make iPhone photos selectable in pickers that don't expand
// `image/*` to Apple formats (some Android browsers, file dialogs in older OSes).
export const IMAGE_MAX_BYTES = 12 * 1024 * 1024;
export const IMAGE_MAX_LABEL = "12 МБ";
export const IMAGE_ACCEPT =
  "image/jpeg,image/png,image/webp,image/gif,image/heic,image/heif,.heic,.heif";

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
