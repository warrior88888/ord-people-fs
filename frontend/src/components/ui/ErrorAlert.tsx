import { ApiError } from "../../api/client";

type Variant = "block" | "inline";

type Props = {
  error: unknown;
  title?: string;
  className?: string;
  variant?: Variant;
};

/**
 * Единая стилизованная плашка ошибки в брендовом стиле проекта.
 * Распознаёт ApiError и обычные Error, склеивает сообщения списком.
 */
export function ErrorAlert({ error, title, className = "", variant = "block" }: Props) {
  const messages = normalizeMessages(error);
  if (messages.length === 0) return null;

  const heading = title ?? defaultTitle(error);

  if (variant === "inline") {
    return (
      <p
        role="alert"
        className={`text-sm text-[#b91c1c] break-words ${className}`}
      >
        {messages.join(" ")}
      </p>
    );
  }

  return (
    <div
      role="alert"
      className={
        "rounded-xl border border-[#fecaca] bg-[#fef2f2] text-[#7f1d1d] " +
        "px-3 py-2.5 sm:px-4 sm:py-3 text-sm flex gap-3 items-start " +
        "shadow-[0_4px_14px_-10px_rgba(185,28,28,0.5)] " +
        className
      }
    >
      <span
        aria-hidden
        className="mt-[3px] inline-block w-2 h-2 rounded-full bg-[#dc2626] shrink-0"
      />
      <div className="min-w-0 flex-1">
        {heading && (
          <p className="font-semibold text-[#991b1b] leading-snug">{heading}</p>
        )}
        {messages.length === 1 ? (
          <p className="leading-snug break-words">{messages[0]}</p>
        ) : (
          <ul className="list-disc pl-5 leading-snug space-y-0.5">
            {messages.map((m, i) => (
              <li key={i} className="break-words">{m}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function defaultTitle(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 0) return "Нет соединения";
    if (error.status === 401) return "Нужна авторизация";
    if (error.status === 403) return "Доступ запрещён";
    if (error.status === 404) return "Не найдено";
    if (error.status === 409) return "Конфликт данных";
    if (error.status === 422) return "Проверьте поля формы";
    if (error.status === 429) return "Слишком часто";
    if (error.status >= 500) return "Ошибка сервера";
  }
  return "Что-то пошло не так";
}

function normalizeMessages(error: unknown): string[] {
  if (!error) return [];
  if (error instanceof ApiError) {
    return error.detail.split(/;\s+/).filter(Boolean);
  }
  if (error instanceof Error) return [error.message];
  if (typeof error === "string") return [error];
  return [];
}
