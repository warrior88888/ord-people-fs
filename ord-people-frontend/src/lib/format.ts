const MONTHS_RU = [
  "января", "февраля", "марта", "апреля", "мая", "июня",
  "июля", "августа", "сентября", "октября", "ноября", "декабря",
];

const MONTHS_RU_SHORT = [
  "янв", "фев", "мар", "апр", "май", "июн",
  "июл", "авг", "сен", "окт", "ноя", "дек",
];

const WEEKDAYS_RU_SHORT = [
  "вс", "пн", "вт", "ср", "чт", "пт", "сб",
];

export function formatWeekday(iso: string): string {
  return WEEKDAYS_RU_SHORT[new Date(iso).getDay()];
}

export function formatRelative(iso: string): string | null {
  const now = Date.now();
  const ts = new Date(iso).getTime();
  const diffMs = now - ts;
  const day = 24 * 60 * 60 * 1000;
  if (diffMs < 60_000) return "только что";
  if (diffMs < 60 * 60 * 1000) {
    const m = Math.floor(diffMs / 60_000);
    return `${m} мин назад`;
  }
  if (diffMs < day) {
    const h = Math.floor(diffMs / (60 * 60 * 1000));
    return `${h} ч назад`;
  }
  if (diffMs < 7 * day) {
    const d = Math.floor(diffMs / day);
    return `${d} дн назад`;
  }
  return null;
}

export function formatDateParts(iso: string): { day: string; month: string; year: string } {
  const d = new Date(iso);
  return {
    day: String(d.getDate()),
    month: MONTHS_RU_SHORT[d.getMonth()],
    year: String(d.getFullYear()),
  };
}

export function formatDateLong(iso: string): string {
  const d = new Date(iso);
  return `${d.getDate()} ${MONTHS_RU[d.getMonth()]} ${d.getFullYear()}`;
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${formatDateLong(iso)}, ${hh}:${mm}`;
}

export function hashString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

export function initialsOf(firstName?: string, lastName?: string, fallback?: string): string {
  const f = (firstName ?? "").trim();
  const l = (lastName ?? "").trim();
  if (f || l) return `${f.charAt(0)}${l.charAt(0)}`.toUpperCase() || "?";
  return (fallback ?? "?").charAt(0).toUpperCase();
}
