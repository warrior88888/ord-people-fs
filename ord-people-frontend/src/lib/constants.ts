export const PAGE_SIZE = 20;

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
