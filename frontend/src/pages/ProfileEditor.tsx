import { useState } from "react";
import { useNavigate } from "react-router";
import type { User } from "../api/types";
import {
  useDeleteAvatar,
  useDeleteMe,
  useUpdateBio,
  useUpdateMe,
  useUploadAvatar,
} from "../api/queries/users";
import { ApiError } from "../api/client";
import { IMAGE_ACCEPT, IMAGE_MAX_BYTES, IMAGE_MAX_LABEL } from "../lib/constants";
import { Avatar } from "../components/Avatar";
import { ImagePreview } from "../components/ImagePreview";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { ErrorAlert } from "../components/ui/ErrorAlert";

const ACCENT_FROM = "#3aa6e0";
const ACCENT_TO = "#1f6fe5";
const GRADIENT = `linear-gradient(135deg, ${ACCENT_FROM} 0%, ${ACCENT_TO} 100%)`;

export function ProfileEditor({ user, onDone }: { user: User; onDone: () => void }) {
  const [firstName, setFirstName] = useState(user.first_name);
  const [lastName, setLastName] = useState(user.last_name);
  const [about, setAbout] = useState(user.bio?.about ?? "");
  const [phone, setPhone] = useState(user.bio?.phone_number ?? "");
  const [email, setEmail] = useState(user.bio?.email ?? "");
  const [vk, setVk] = useState(user.bio?.vk_link ?? "");
  const [max, setMax] = useState(user.bio?.max_link ?? "");

  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [error, setError] = useState<unknown>(null);

  const updMe = useUpdateMe();
  const updBio = useUpdateBio();
  const upAvatar = useUploadAvatar();
  const delAvatar = useDeleteAvatar();
  const delMe = useDeleteMe();
  const navigate = useNavigate();

  const [confirmAvatar, setConfirmAvatar] = useState(false);
  const [confirmDeleteMe, setConfirmDeleteMe] = useState(false);

  const busy =
    updMe.isPending || updBio.isPending || upAvatar.isPending || delAvatar.isPending;

  // The button is shown whenever the server says the user has an avatar OR the
  // user has picked a new file (so they can drop it before submitting). A failed
  // delete (e.g. 5xx) does NOT remove the button — it's a server issue, not a
  // confirmation that the avatar is gone.
  const hasServerAvatar = !!user.avatar_url;
  const canRemoveAvatar = hasServerAvatar || !!avatarFile;

  function removeAvatarConfirmed() {
    setConfirmAvatar(false);
    setError(null);
    setAvatarFile(null);
    if (!hasServerAvatar) return;
    delAvatar.mutate(undefined, {
      onError: (err) => {
        if (err instanceof ApiError && err.status === 404) return; // already gone
        setError(err);
      },
    });
  }

  function deleteMeConfirmed() {
    delMe.mutate(undefined, {
      onSuccess: () => {
        setConfirmDeleteMe(false);
        navigate("/");
      },
      onError: (err) => {
        setConfirmDeleteMe(false);
        setError(err);
      },
    });
  }

  function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    if (!file) {
      setAvatarFile(null);
      return;
    }
    if (file.size > IMAGE_MAX_BYTES) {
      setError(`Размер файла не должен превышать ${IMAGE_MAX_LABEL}.`);
      e.target.value = "";
      return;
    }
    setError(null);
    setAvatarFile(file);
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (firstName !== user.first_name || lastName !== user.last_name) {
        await updMe.mutateAsync({ first_name: firstName, last_name: lastName });
      }
      await updBio.mutateAsync({
        about: about || null,
        phone_number: phone || null,
        email: email || null,
        vk_link: vk || null,
        max_link: max || null,
      });
      if (avatarFile) {
        await upAvatar.mutateAsync(avatarFile);
      }
      onDone();
    } catch (err) {
      setError(err);
    }
  }

  return (
    <form onSubmit={save} className="max-w-3xl mx-auto">
      <div className="text-sm mb-4">
        <button
          type="button"
          onClick={onDone}
          className="link inline-flex items-center gap-1"
        >
          <span aria-hidden="true">←</span> К профилю
        </button>
      </div>

      <article className="relative rounded-2xl border border-[var(--color-border)] bg-white overflow-hidden shadow-[0_10px_40px_-20px_rgba(15,23,42,0.25)]">
        {/* accent stripe */}
        <div
          className="absolute left-0 top-0 bottom-0 w-1 z-10"
          style={{ background: GRADIENT }}
        />

        {/* HERO — pure gradient banner */}
        <div className="relative h-36 md:h-44" style={{ background: GRADIENT }}>
          <div
            className="absolute inset-0 opacity-25 pointer-events-none"
            style={{
              backgroundImage:
                "radial-gradient(circle at 15% 30%, rgba(255,255,255,.9) 0, transparent 40%), radial-gradient(circle at 80% 80%, rgba(255,255,255,.6) 0, transparent 45%)",
            }}
          />
        </div>

        {/* AVATAR — overlaps the seam */}
        <div className="px-4 sm:px-6 md:px-8 -mt-12 relative z-10 flex items-end gap-4">
          <div className="relative">
            {avatarFile ? (
              <ImagePreview
                file={avatarFile}
                className="w-24 h-24 md:w-28 md:h-28 rounded-full object-cover border-4 border-white shadow-md"
                alt="Аватар"
              />
            ) : (
              <div className="w-24 h-24 md:w-28 md:h-28 rounded-full border-4 border-white shadow-md overflow-hidden">
                <Avatar
                  url={user.avatar_url}
                  username={user.username}
                  firstName={user.first_name}
                  lastName={user.last_name}
                  size={112}
                  className="!w-full !h-full"
                />
              </div>
            )}
            <label
              className="absolute -bottom-1 -right-1 w-9 h-9 rounded-full bg-white border border-[var(--color-border)] shadow-sm cursor-pointer inline-flex items-center justify-center hover:border-brand hover:text-brand text-[var(--color-brand-deep)] transition-colors"
              title="Сменить аватар"
              aria-label="Сменить аватар"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z" />
              </svg>
              <input
                type="file"
                accept={IMAGE_ACCEPT}
                className="hidden"
                onChange={handleAvatarChange}
              />
            </label>
          </div>
          <div className="pb-1 min-w-0 flex-1">
            <p className="text-sm font-semibold text-[var(--color-ink)] truncate">
              {firstName} {lastName}
            </p>
            <p className="text-xs text-[var(--color-muted)] truncate">
              @{user.username}
            </p>
          </div>
        </div>

        {(avatarFile || canRemoveAvatar) && (
          <div className="px-4 sm:px-6 md:px-8 mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs">
            {avatarFile && (
              <button
                type="button"
                className="text-[var(--color-muted)] hover:text-brand transition-colors"
                onClick={() => setAvatarFile(null)}
              >
                Отменить выбор
              </button>
            )}
            {canRemoveAvatar && (
              <button
                type="button"
                className="text-[var(--color-muted)] hover:text-[#b91c1c] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={() => setConfirmAvatar(true)}
                disabled={delAvatar.isPending}
              >
                {delAvatar.isPending ? "Удаление…" : "Удалить аватар"}
              </button>
            )}
          </div>
        )}

        {/* BODY */}
        <div className="px-4 sm:px-6 md:px-8 pt-8 pb-8 flex flex-col gap-8">
          <section
            className="relative"
            style={{ borderLeft: `3px solid ${ACCENT_FROM}55`, paddingLeft: "1.25rem" }}
          >
            <SectionLabel>Личные данные</SectionLabel>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Имя" value={firstName} onChange={setFirstName} required min={2} max={32} />
              <Field label="Фамилия" value={lastName} onChange={setLastName} required min={2} max={32} />
            </div>
          </section>

          <section
            className="relative"
            style={{ borderLeft: `3px solid ${ACCENT_FROM}55`, paddingLeft: "1.25rem" }}
          >
            <SectionLabel>О себе</SectionLabel>
            <Field
              label="Несколько слов про вас и ваши добрые дела"
              value={about}
              onChange={setAbout}
              as="textarea"
              max={512}
            />
            <p className="mt-1 text-xs text-[var(--color-muted)] text-right">
              {about.length}/512
            </p>
          </section>

          <section
            className="relative"
            style={{ borderLeft: `3px solid ${ACCENT_FROM}55`, paddingLeft: "1.25rem" }}
          >
            <SectionLabel>Контакты</SectionLabel>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Телефон" value={phone} onChange={setPhone} placeholder="+79991234567" />
              <Field label="Email" value={email} onChange={setEmail} type="email" />
            </div>
          </section>

          <section
            className="relative"
            style={{ borderLeft: `3px solid ${ACCENT_FROM}55`, paddingLeft: "1.25rem" }}
          >
            <SectionLabel>Социальные сети</SectionLabel>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="VK" value={vk} onChange={setVk} placeholder="https://vk.com/username" />
              <Field label="Max" value={max} onChange={setMax} placeholder="https://max.ru/username" />
            </div>
          </section>

          {!!error && <ErrorAlert error={error} />}

          <section className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-2 pt-4 border-t border-[var(--color-border)]">
            <button type="submit" className="btn btn-primary w-full sm:w-auto" disabled={busy}>
              {busy ? "Сохранение…" : "Сохранить изменения"}
            </button>
            <button
              type="button"
              className="btn btn-outline w-full sm:w-auto"
              onClick={onDone}
              disabled={busy}
            >
              Отмена
            </button>
            <button
              type="button"
              className="btn btn-danger w-full sm:w-auto sm:ml-auto"
              onClick={() => setConfirmDeleteMe(true)}
              disabled={delMe.isPending}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h18" />
                <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
              </svg>
              Удалить профиль
            </button>
          </section>
        </div>
      </article>

      <ConfirmDialog
        open={confirmAvatar}
        title="Удалить аватар?"
        message="Вместо фотографии появится плашка с вашими инициалами на брендовом цвете. Новый аватар можно загрузить в любой момент."
        confirmLabel="Удалить аватар"
        destructive
        busy={delAvatar.isPending}
        onConfirm={removeAvatarConfirmed}
        onClose={() => setConfirmAvatar(false)}
      />

      <ConfirmDialog
        open={confirmDeleteMe}
        title="Удалить профиль?"
        message="Действие необратимо: имя пользователя и личные данные будут анонимизированы, аватар удалён, все сессии завершены. Ваши проекты и комментарии останутся, но без привязки к вам."
        confirmLabel="Удалить профиль"
        destructive
        busy={delMe.isPending}
        onConfirm={deleteMeConfirmed}
        onClose={() => setConfirmDeleteMe(false)}
      />
    </form>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="block w-5 h-[2px] rounded-full" style={{ background: ACCENT_FROM }} />
      <span className="text-[11px] font-semibold uppercase tracking-[0.3em] text-[var(--color-muted)]">
        {children}
      </span>
    </div>
  );
}

type FieldProps = {
  label: string;
  value: string;
  onChange: (v: string) => void;
  required?: boolean;
  type?: string;
  placeholder?: string;
  as?: "input" | "textarea";
  max?: number;
  min?: number;
};

function Field({
  label,
  value,
  onChange,
  required,
  type = "text",
  placeholder,
  as = "input",
  max,
  min,
}: FieldProps) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-[var(--color-muted)]">{label}</span>
      {as === "textarea" ? (
        <textarea
          className="textarea"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          maxLength={max}
          minLength={min}
          required={required}
          placeholder={placeholder}
        />
      ) : (
        <input
          className="input"
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={required}
          placeholder={placeholder}
          maxLength={max}
          minLength={min}
        />
      )}
    </label>
  );
}
