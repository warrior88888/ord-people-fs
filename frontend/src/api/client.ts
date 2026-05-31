const apiBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;
const mediaBaseUrl = import.meta.env.VITE_MEDIA_BASE_URL as string | undefined;

if (!apiBaseUrl) {
  throw new Error("VITE_API_BASE_URL is not configured");
}
if (!mediaBaseUrl) {
  throw new Error("VITE_MEDIA_BASE_URL is not configured");
}

export const API_BASE_URL = apiBaseUrl;
export const MEDIA_BASE_URL = mediaBaseUrl;

export class ApiError extends Error {
  status: number;
  detail: string;
  raw?: unknown;
  constructor(status: number, detail: string, raw?: unknown) {
    super(detail || `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
    this.raw = raw;
  }
}

function buildUrl(path: string, params?: Record<string, unknown>): string {
  const raw = path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
  const url = new URL(raw, typeof window !== "undefined" ? window.location.origin : "http://localhost");
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null || value === "") continue;
      if (Array.isArray(value)) {
        for (const v of value) url.searchParams.append(key, String(v));
      } else {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

type Options = {
  method?: string;
  body?: unknown;
  params?: Record<string, unknown>;
  formData?: FormData;
  signal?: AbortSignal;
};

async function doFetch<T>(path: string, opts: Options = {}, attempt = 0): Promise<T> {
  const { method = "GET", body, params, formData, signal } = opts;
  const headers: Record<string, string> = {};
  let bodyInit: BodyInit | undefined;
  if (formData) {
    bodyInit = formData;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    bodyInit = JSON.stringify(body);
  }

  let res: Response;
  try {
    res = await fetch(buildUrl(path, params), {
      method,
      headers,
      body: bodyInit,
      credentials: "include",
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(0, "Не удалось связаться с сервером. Проверьте подключение к интернету.", err);
  }

  if (res.status === 204) return undefined as T;

  if (res.status === 429 && attempt < 2) {
    const retryAfter = Number(res.headers.get("Retry-After") ?? "1");
    await new Promise((r) => setTimeout(r, Math.max(500, retryAfter * 1000)));
    return doFetch<T>(path, opts, attempt + 1);
  }

  let data: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const detail = extractDetail(data) ?? statusFallback(res.status);
    throw new ApiError(res.status, detail, data);
  }

  return data as T;
}

// Перевод имён полей из ответа FastAPI/pydantic в человекочитаемые названия.
const FIELD_LABELS: Record<string, string> = {
  username: "имя пользователя",
  password: "пароль",
  first_name: "имя",
  last_name: "фамилия",
  email: "email",
  phone_number: "телефон",
  vk_link: "ссылка ВКонтакте",
  max_link: "ссылка Max",
  about: "о себе",
  title: "название",
  text: "текст",
  description: "описание",
  category_id: "категория",
  tags: "теги",
  file: "файл",
};

// Перевод популярных pydantic-кодов в русские формулировки.
function translatePydanticMessage(type: string | undefined, msg: string): string {
  if (!type) return msg;
  if (type.startsWith("string_too_short")) return "значение слишком короткое";
  if (type.startsWith("string_too_long")) return "значение слишком длинное";
  if (type === "string_pattern_mismatch") return "значение не соответствует допустимому формату";
  if (type === "value_error" && /email/i.test(msg)) return "некорректный email";
  if (type === "missing") return "поле обязательно для заполнения";
  if (type === "url_parsing" || type === "url_scheme") return "некорректная ссылка";
  if (type.startsWith("int_") || type.startsWith("float_")) return "ожидается число";
  if (type === "value_error") return msg.replace(/^Value error,\s*/i, "");
  return msg;
}

function formatValidationItem(item: { loc?: unknown; msg?: string; type?: string }): string {
  const loc = Array.isArray(item.loc) ? item.loc : [];
  const fieldKey = loc.filter((p) => p !== "body" && p !== "query" && p !== "path").pop();
  const fieldLabel =
    typeof fieldKey === "string" ? FIELD_LABELS[fieldKey] ?? fieldKey : undefined;
  const message = translatePydanticMessage(item.type, item.msg ?? "ошибка валидации");
  return fieldLabel ? `Поле «${fieldLabel}»: ${message}` : message;
}

// Перевод популярных серверных строк (FastAPI / собственные ответы бэка).
const SERVER_PHRASES: Array<[RegExp, string]> = [
  [/^invalid credentials\.?$/i, "Неверное имя пользователя или пароль."],
  [/^not authenticated\.?$/i, "Требуется авторизация."],
  [/^could not validate credentials\.?$/i, "Не удалось подтвердить вход. Войдите снова."],
  [/^not found\.?$/i, "Запись не найдена."],
  [/^forbidden\.?$/i, "Действие запрещено."],
  [/already exists/i, "Запись с такими данными уже существует."],
  [/username .*taken|taken username/i, "Это имя пользователя уже занято."],
  [/email .*taken|taken email/i, "Этот email уже используется."],
  [/password .*(weak|short)/i, "Пароль слишком простой или короткий."],
  [/rate limit/i, "Слишком много запросов. Попробуйте позже."],
  [/file too large|too large/i, "Файл слишком большой."],
  [/unsupported (media|file)/i, "Неподдерживаемый тип файла."],
];

function translateServerPhrase(s: string): string {
  for (const [re, ru] of SERVER_PHRASES) if (re.test(s.trim())) return ru;
  return s;
}

function extractDetail(data: unknown): string | null {
  if (!data || typeof data !== "object") return null;
  const d = (data as { detail?: unknown }).detail;
  if (typeof d === "string") return translateServerPhrase(d);
  if (Array.isArray(d) && d.length > 0) {
    const items = d as Array<{ loc?: unknown; msg?: string; type?: string }>;
    const lines = items.map(formatValidationItem);
    const uniq = Array.from(new Set(lines));
    return uniq.slice(0, 3).join("; ");
  }
  return null;
}

function statusFallback(status: number): string {
  switch (status) {
    case 400:
      return "Некорректный запрос. Проверьте заполненные поля.";
    case 401:
      return "Требуется авторизация. Войдите в аккаунт и повторите.";
    case 403:
      return "Недостаточно прав для выполнения действия.";
    case 404:
      return "Запрашиваемый ресурс не найден.";
    case 409:
      return "Конфликт данных: похоже, такая запись уже существует.";
    case 413:
      return "Файл слишком большой.";
    case 415:
      return "Неподдерживаемый тип файла.";
    case 422:
      return "Не удалось обработать данные. Проверьте поля формы.";
    case 429:
      return "Слишком много запросов. Подождите немного и попробуйте снова.";
    case 500:
      return "Ошибка на сервере. Мы уже работаем над этим — попробуйте позже.";
    case 502:
    case 503:
    case 504:
      return "Сервис временно недоступен. Повторите попытку через минуту.";
    default:
      return status >= 500
        ? "Ошибка на сервере. Попробуйте позже."
        : `Не удалось выполнить запрос (код ${status}).`;
  }
}

export const api = {
  get: <T>(path: string, params?: Record<string, unknown>, signal?: AbortSignal) =>
    doFetch<T>(path, { params, signal }),
  post: <T>(path: string, body?: unknown, params?: Record<string, unknown>) =>
    doFetch<T>(path, { method: "POST", body, params }),
  patch: <T>(path: string, body?: unknown) => doFetch<T>(path, { method: "PATCH", body }),
  put: <T>(path: string, body?: unknown) => doFetch<T>(path, { method: "PUT", body }),
  del: <T>(path: string) => doFetch<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, file: File, method: "POST" | "PUT" = "PUT") => {
    const fd = new FormData();
    fd.append("file", file);
    return doFetch<T>(path, { method, formData: fd });
  },
};
