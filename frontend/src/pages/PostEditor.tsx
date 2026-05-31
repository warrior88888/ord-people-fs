import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router";
import {
  useCreatePost,
  useDeletePost,
  useDeletePostPhoto,
  usePost,
  useUpdatePost,
  useUploadPostPhoto,
} from "../api/queries/posts";
import { ApiError } from "../api/client";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { useTags } from "../api/queries/tags";
import { CATEGORIES, type CategoryValue } from "../lib/constants";
import { CenterSpinner } from "../components/ui/Spinner";
import { ImagePreview } from "../components/ImagePreview";
import { api, MEDIA_BASE_URL } from "../api/client";
import { DefaultCover } from "../components/DefaultCover";

function resolveMedia(url?: string | null): string | null {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  return `${MEDIA_BASE_URL}${url.startsWith("/") ? "" : "/"}${url}`;
}

export default function PostEditor() {
  const { id } = useParams();
  const postId = id ? Number(id) : null;
  const isEdit = postId != null;
  const existing = usePost(postId);
  const navigate = useNavigate();
  const tags = useTags();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<CategoryValue>("story");
  const [externalUrl, setExternalUrl] = useState("");
  const [tagIds, setTagIds] = useState<number[]>([]);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isEdit && existing.data) {
      const p = existing.data;
      setName(p.name);
      setDescription(p.description);
      setCategory(p.category);
      setExternalUrl(p.external_url ?? "");
      setTagIds(p.tags.map((t) => t.pk));
    }
  }, [isEdit, existing.data]);

  const create = useCreatePost();
  const update = useUpdatePost(postId ?? 0);
  const upload = useUploadPostPhoto(postId ?? 0);
  const delPhoto = useDeletePostPhoto(postId ?? 0);
  const delPost = useDeletePost();

  const [confirmPhoto, setConfirmPhoto] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const busy =
    create.isPending || update.isPending || upload.isPending || delPhoto.isPending;

  const hasServerPhoto = isEdit && !!existing.data?.photo_url;
  const canRemovePhoto = hasServerPhoto || !!photoFile;

  function removePhotoConfirmed() {
    setConfirmPhoto(false);
    setError(null);
    setPhotoFile(null);
    if (!hasServerPhoto || !postId) return;
    delPhoto.mutate(undefined, {
      onError: (err) => {
        if (err instanceof ApiError && err.status === 404) return;
        setError(err instanceof Error ? err.message : "Не удалось удалить фото");
      },
    });
  }

  function deletePostConfirmed() {
    if (!postId) return;
    delPost.mutate(postId, {
      onSuccess: () => {
        setConfirmDelete(false);
        navigate("/");
      },
      onError: (err) => {
        setConfirmDelete(false);
        setError(err instanceof Error ? err.message : "Не удалось удалить проект");
      },
    });
  }

  const existingPhoto = useMemo(
    () => resolveMedia(existing.data?.photo_url),
    [existing.data?.photo_url]
  );

  function toggleTag(pk: number) {
    setTagIds((cur) => (cur.includes(pk) ? cur.filter((x) => x !== pk) : [...cur, pk]));
  }

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    if (file && file.size > 10 * 1024 * 1024) {
      setError("Изображение не должно превышать 10 МБ.");
      e.target.value = "";
      return;
    }
    setError(null);
    setPhotoFile(file);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const payload = {
        name,
        description,
        category,
        external_url: externalUrl || null,
        tag_ids: tagIds,
      };

      if (isEdit && postId) {
        await update.mutateAsync(payload);
        if (photoFile) await upload.mutateAsync(photoFile);
        navigate(`/posts/${postId}`);
      } else {
        const created = await create.mutateAsync(payload);
        if (photoFile) {
          await api.upload<{ photo_url: string }>(`/posts/${created.pk}/photo`, photoFile, "POST");
        }
        navigate(`/posts/${created.pk}`);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }

  if (isEdit && existing.isLoading) return <CenterSpinner />;

  return (
    <form onSubmit={submit} className="max-w-2xl mx-auto">
      <div className="text-sm mb-6">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1 text-[var(--color-muted)] hover:text-[var(--color-ink)] transition-colors"
        >
          <span aria-hidden="true">←</span> Назад
        </button>
      </div>

      <h1 className="text-[28px] md:text-4xl font-bold tracking-tight text-[var(--color-ink)] mb-8">
        {isEdit ? "Редактирование проекта" : "Новый проект"}
      </h1>

      <div className="flex flex-col gap-7">
        <section>
          <p className="text-[11px] uppercase tracking-wider text-[var(--color-muted)] mb-2">
            Обложка
          </p>
          <div className="relative aspect-[16/9] rounded-lg overflow-hidden bg-[var(--color-surface)] border border-[var(--color-border)]">
            {photoFile ? (
              <ImagePreview
                file={photoFile}
                className="absolute inset-0 h-full w-full object-cover"
                alt="Превью"
              />
            ) : existingPhoto ? (
              <img src={existingPhoto} alt="" className="absolute inset-0 h-full w-full object-cover" />
            ) : (
              <DefaultCover category={category} className="absolute inset-0" showLabel={false} />
            )}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <label className="btn btn-outline cursor-pointer">
              {photoFile || existingPhoto ? "Заменить фото" : "Добавить фото"}
              <input type="file" accept="image/*" className="hidden" onChange={handleFile} />
            </label>
            {photoFile && (
              <button
                type="button"
                className="text-sm text-[var(--color-muted)] hover:text-[var(--color-ink)] transition-colors px-2 py-2"
                onClick={() => setPhotoFile(null)}
              >
                Отменить
              </button>
            )}
            {canRemovePhoto && (
              <button
                type="button"
                className="text-sm text-[var(--color-muted)] hover:text-red-600 transition-colors px-2 py-2 disabled:opacity-50"
                onClick={() => setConfirmPhoto(true)}
                disabled={delPhoto.isPending}
              >
                {delPhoto.isPending ? "Удаление…" : "Удалить фото"}
              </button>
            )}
          </div>
        </section>

        <section>
          <label className="block">
            <span className="text-[11px] uppercase tracking-wider text-[var(--color-muted)] mb-2 block">
              Название
            </span>
            <input
              className="input text-lg font-semibold"
              value={name}
              onChange={(e) => setName(e.target.value)}
              minLength={3}
              maxLength={50}
              required
              placeholder="Доброе дело, о котором стоит рассказать…"
            />
          </label>
          <p className="mt-1 text-xs text-[var(--color-muted)] text-right">{name.length}/50</p>
        </section>

        <section>
          <label className="block">
            <span className="text-[11px] uppercase tracking-wider text-[var(--color-muted)] mb-2 block">
              Описание
            </span>
            <textarea
              className="textarea !min-h-[180px] text-[15px] leading-[1.7]"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              minLength={10}
              maxLength={1000}
              required
              placeholder="Расскажите подробно, что произошло, кому помогли, как присоединиться…"
            />
          </label>
          <p className="mt-1 text-xs text-[var(--color-muted)] text-right">{description.length}/1000</p>
        </section>

        <section>
          <p
            className="text-[11px] uppercase tracking-wider text-[var(--color-muted)] mb-2"
            id="post-category-label"
          >
            Категория
          </p>
          <div
            role="radiogroup"
            aria-labelledby="post-category-label"
            className="flex flex-wrap gap-2"
          >
            {CATEGORIES.map((c) => {
              const on = category === c.value;
              return (
                <button
                  key={c.value}
                  type="button"
                  role="radio"
                  aria-checked={on}
                  onClick={() => setCategory(c.value as CategoryValue)}
                  className={`category-chip ${on ? "category-chip--on" : ""}`}
                >
                  {c.label}
                </button>
              );
            })}
          </div>
        </section>

        <section>
          <label className="block">
            <span className="text-[11px] uppercase tracking-wider text-[var(--color-muted)] mb-2 block">
              Внешняя ссылка
            </span>
            <input
              className="input"
              type="url"
              value={externalUrl}
              onChange={(e) => setExternalUrl(e.target.value)}
              placeholder="https://…"
            />
          </label>
        </section>

        <section>
          <p className="text-[11px] uppercase tracking-wider text-[var(--color-muted)] mb-2">Теги</p>
          <div className="flex flex-wrap gap-2">
            {tags.isLoading && (
              <span className="text-sm text-[var(--color-muted)]">Загрузка тегов…</span>
            )}
            {tags.data?.map((t) => {
              const on = tagIds.includes(t.pk);
              return (
                <button
                  key={t.pk}
                  type="button"
                  onClick={() => toggleTag(t.pk)}
                  className={`tag-pill ${on ? "!bg-[var(--color-ink)] !text-white !border-[var(--color-ink)]" : ""}`}
                >
                  {t.name}
                </button>
              );
            })}
            {tags.data?.length === 0 && (
              <span className="text-sm text-[var(--color-muted)]">Тегов пока нет</span>
            )}
          </div>
        </section>

        {error && <ErrorAlert error={error} />}

        <section className="flex flex-wrap items-center gap-2 pt-4 border-t border-[var(--color-border)]">
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "Сохранение…" : isEdit ? "Сохранить изменения" : "Опубликовать проект"}
          </button>
          <button type="button" className="btn btn-outline" onClick={() => navigate(-1)} disabled={busy}>
            Отмена
          </button>
          {isEdit && (
            <button
              type="button"
              className="btn btn-danger ml-auto"
              onClick={() => setConfirmDelete(true)}
              disabled={delPost.isPending}
            >
              Удалить проект
            </button>
          )}
        </section>
      </div>

      <ConfirmDialog
        open={confirmPhoto}
        title="Удалить фото проекта?"
        message="Вместо обложки появится категорийный заполнитель. Можно загрузить новое фото в любой момент."
        confirmLabel="Удалить фото"
        destructive
        busy={delPhoto.isPending}
        onConfirm={removePhotoConfirmed}
        onClose={() => setConfirmPhoto(false)}
      />

      <ConfirmDialog
        open={confirmDelete}
        title="Удалить проект?"
        message="Проект и его фото будут удалены безвозвратно вместе со всеми комментариями и реакциями."
        confirmLabel="Удалить проект"
        destructive
        busy={delPost.isPending}
        onConfirm={deletePostConfirmed}
        onClose={() => setConfirmDelete(false)}
      />
    </form>
  );
}
